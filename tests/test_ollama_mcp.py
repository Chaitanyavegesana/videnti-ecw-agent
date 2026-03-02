"""
Module Tests: Ollama MCP Server
Tests the summarize_phi and validate_eligibility tools in isolation.
"""

import asyncio
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Unit Tests (no server required) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_phi_assigns_snapshot_id_and_strips_phi(monkeypatch):
    """summarize_phi must return a snapshot_id and phi_stripped=True."""
    from mcp_servers.ollama_server.server import summarize_phi

    # Monkeypatch the Ollama HTTP call to avoid needing a live instance
    async def mock_generate(*args, **kwargs):
        return json.dumps({"clinical_notes": "BMI elevated, fatigue noted."})

    async def mock_get_model():
        return "test-model"

    monkeypatch.setattr("mcp_servers.ollama_server.server.ollama_generate", mock_generate)
    monkeypatch.setattr("mcp_servers.ollama_server.server.get_available_model", mock_get_model)

    result = await summarize_phi({"name": "John Doe", "mrn": "12345", "clinical_notes": "BMI elevated."})

    assert "snapshot_id" in result, "snapshot_id must be present"
    assert result["phi_stripped"] is True, "phi_stripped must be True"
    assert isinstance(result["snapshot_id"], str) and len(result["snapshot_id"]) == 36, "snapshot_id must be UUID"
    print(f"PASS: summarize_phi returned snapshot_id={result['snapshot_id']}")


@pytest.mark.asyncio
async def test_validate_eligibility_returns_structured_response(monkeypatch):
    """validate_eligibility must return a dict with eligibility_results."""
    from mcp_servers.ollama_server.server import validate_eligibility

    async def mock_generate(*args, **kwargs):
        return json.dumps([{"test": "HST", "confidence": 0.92}])

    async def mock_get_model():
        return "test-model"

    monkeypatch.setattr("mcp_servers.ollama_server.server.ollama_generate", mock_generate)
    monkeypatch.setattr("mcp_servers.ollama_server.server.get_available_model", mock_get_model)

    summary = {"snapshot_id": "abc-123", "clinical_notes": "BMI 32, fatigue."}
    result = await validate_eligibility(summary, rule_set="speed_play")

    assert "eligibility_results" in result, "eligibility_results must be present"
    assert result.get("snapshot_id") == "abc-123", "snapshot_id must pass through"
    print(f"PASS: validate_eligibility returned results for snapshot {result['snapshot_id']}")


# ── Integration-style Test (server must be running at :8000) ────────────────

@pytest.mark.asyncio
@pytest.mark.integration
async def test_live_summarize_phi_endpoint():
    """Integration test: sends a real request to the live ollama-server."""
    import httpx

    payload = {"raw_snapshot": {"name": "Test Patient", "mrn": "TEST-99", "notes": "Chronic snoring, BMI 33"}}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post("http://localhost:8000/tools/summarize_phi", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("phi_stripped") is True
            print(f"PASS (live): snapshot_id={data.get('snapshot_id')}")
    except httpx.ConnectError:
        pytest.skip("Ollama MCP server not running. Start it with: python3 mcp-servers/ollama-server/server.py")
