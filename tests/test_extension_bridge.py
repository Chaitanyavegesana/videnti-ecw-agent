"""
Tests: Chrome Extension WebSocket Bridge
Validates that the ecw-bridge server correctly handles messages from the
Chrome Extension WebSocket endpoint.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_server():
    """Import the server module and reset its state for test isolation."""
    import mcp_servers.ecw_bridge.server as srv
    while not srv._schedule_queue.empty():
        srv._schedule_queue.get_nowait()
    while not srv._chart_queue.empty():
        srv._chart_queue.get_nowait()
    srv._extension_connections.clear()
    return srv


class _AsyncIterWebSocket:
    """Fake WebSocket that yields a fixed list of text messages then stops."""

    def __init__(self, messages, *, send_raises=False):
        self._messages = list(messages)
        self._send_raises = send_raises
        self.sent = []

    def iter_text(self):
        return self._aiter()

    async def _aiter(self):
        for msg in self._messages:
            yield msg

    async def send_text(self, text):
        if self._send_raises:
            raise RuntimeError("connection closed")
        self.sent.append(text)


# ─── is_extension_connected ───────────────────────────────────────────────────

def test_is_extension_connected_false_when_no_connections():
    """is_extension_connected should return False when set is empty."""
    srv = _get_server()
    assert not srv.is_extension_connected()
    print("✓ is_extension_connected returns False with no connections")


def test_is_extension_connected_true_when_connection_present():
    """is_extension_connected should return True when a mock WS is in the set."""
    srv = _get_server()
    mock_ws = MagicMock()
    srv._extension_connections.add(mock_ws)
    assert srv.is_extension_connected()
    srv._extension_connections.discard(mock_ws)
    print("✓ is_extension_connected returns True with active connection")


# ─── _extension_ws_handler ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ws_handler_enqueues_schedule_data():
    """
    A 'schedule_data' message from the extension should be placed in
    _schedule_queue so that get_schedule() can consume it.
    """
    srv = _get_server()

    appointments = [
        {"mrn": "MRN-001", "time": "09:00"},
        {"mrn": "MRN-002", "time": "09:15"},
    ]
    ws = _AsyncIterWebSocket([
        json.dumps({"type": "schedule_data", "appointments": appointments}),
    ])

    await srv._extension_ws_handler(ws)

    assert not srv._schedule_queue.empty()
    queued = srv._schedule_queue.get_nowait()
    assert queued == appointments
    print("✓ ws_handler enqueued schedule_data correctly")


@pytest.mark.asyncio
async def test_ws_handler_enqueues_chart_data():
    """
    A 'chart_data' message from the extension should be placed in
    _chart_queue so that extract_chart_data() can consume it.
    """
    srv = _get_server()

    chart_payload = {
        "type": "chart_data",
        "mrn": "MRN-123",
        "snapshot": {
            "demographics": {"name": "Test Patient", "mrn": "MRN-123"},
            "vitals": {"bmi": 31.0},
        },
    }
    ws = _AsyncIterWebSocket([json.dumps(chart_payload)])

    await srv._extension_ws_handler(ws)

    assert not srv._chart_queue.empty()
    queued = srv._chart_queue.get_nowait()
    assert queued["mrn"] == "MRN-123"
    assert queued["snapshot"]["vitals"]["bmi"] == 31.0
    print("✓ ws_handler enqueued chart_data correctly")


@pytest.mark.asyncio
async def test_ws_handler_sends_ack_for_valid_message():
    """
    The handler should send a JSON ACK after processing each recognised message.
    """
    srv = _get_server()
    ws = _AsyncIterWebSocket([
        json.dumps({"type": "frame_ready", "frameType": "chart", "url": "https://example.com"}),
    ])

    await srv._extension_ws_handler(ws)

    assert len(ws.sent) == 1
    ack = json.loads(ws.sent[0])
    assert ack.get("type") == "ack"
    print("✓ ws_handler sent ACK for frame_ready message")


@pytest.mark.asyncio
async def test_ws_handler_removes_connection_on_close():
    """
    The WS connection should be removed from _extension_connections when the
    handler exits (simulating socket close).
    """
    srv = _get_server()
    ws = _AsyncIterWebSocket([])  # No messages — handler exits immediately

    await srv._extension_ws_handler(ws)

    assert ws not in srv._extension_connections
    print("✓ ws_handler removed connection from set on exit")


# ─── get_schedule with extension ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_schedule_uses_extension_data_when_connected():
    """
    get_schedule should return data from _schedule_queue when an extension
    is connected.  We mock _send_to_extension to also populate the queue,
    mimicking the real extension's response.
    """
    srv = _get_server()

    mock_ws = MagicMock()
    srv._extension_connections.add(mock_ws)

    test_appointments = [{"mrn": "EXT-001", "time": "08:00"}]

    async def _fake_send(payload):
        # Simulate the extension responding immediately
        await srv._schedule_queue.put(test_appointments)

    with patch.object(srv, "_send_to_extension", side_effect=_fake_send):
        result = await srv.get_schedule()

    assert result["status"] == "SUCCESS"
    assert result["source"] == "extension"
    assert result["appointments"] == test_appointments
    print("✓ get_schedule returned extension data when WS connected")


# ─── extract_chart_data with extension ───────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_chart_data_uses_extension_snapshot_when_connected():
    """
    extract_chart_data should use the DOM snapshot from the extension queue
    when an extension is connected.
    """
    srv = _get_server()

    mock_ws = MagicMock()
    srv._extension_connections.add(mock_ws)

    dom_snapshot = {
        "demographics": {"name": "Ext Patient", "mrn": "EXT-123"},
        "vitals": {"bmi": 29.5},
        "pmh": ["Hypertension"],
        "chief_complaint": "Snoring",
        "hpi": "Patient reports snoring and fatigue",
        "medications": [],
        "allergies": [],
        "assessment": "Possible sleep apnea",
        "recent_labs": [],
    }

    async def _fake_send(payload):
        await srv._chart_queue.put({"snapshot": dom_snapshot, "mrn": "EXT-123"})

    with patch.object(srv, "_send_to_extension", side_effect=_fake_send):
        result = await srv.extract_chart_data("EXT-123")

    assert result["status"] == "SUCCESS"
    assert result["source"] == "extension"
    assert result["raw_data"]["demographics"]["name"] == "Ext Patient"
    print("✓ extract_chart_data used extension DOM snapshot")
