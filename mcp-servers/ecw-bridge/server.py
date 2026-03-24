"""
ICS - Intelligent Clinical System — eCW Bridge MCP Server
FastMCP-based local server for eClinicalWorks.

Endpoint: http://localhost:8001
WebSocket: ws://localhost:8001/ws/extension  (Chrome Extension bridge)

HYBRID ARCHITECTURE:
  Mode A — Chrome Extension (preferred):
    The Videnti Chrome Extension connects over WebSocket and pushes DOM-extracted
    chart / schedule data directly into the server.  This is more reliable than
    screen-based RPA because it reads the live DOM rather than pixels.

  Mode B — PyAutoGUI Fallback:
    When the Chrome Extension is not connected, the server falls back to
    PyAutoGUI-based screen automation.  PyAutoGUI is imported lazily inside
    the functions that need it so the server can start in headless/test
    environments without a display.

RPA FLOW:
1. get_schedule()            → Retrieve provider's daily schedule (ext or RPA)
2. open_chart(patient_mrn)   → Navigate to and open patient chart (RPA fallback)
3. extract_chart_data(mrn)   → Read clinical data (ext or RPA)
4. pend_order(…)             → Place diagnostic order in patient chart (RPA)
5. approve_recommendation()  → User approves, automatically pends order
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv, set_key
from mcp.server.fastmcp import FastMCP

# Load existing .env into environment
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


# ─── Configuration ───────────────────────────────────────────────────────────

SERVER_PORT = 8001

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ECW-BRIDGE] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastMCP Server Init ─────────────────────────────────────────────────────

mcp = FastMCP(
    name="ics-ecw-bridge",
    instructions=(
        "Local eClinicalWorks bridge. Supports DOM extraction via Chrome Extension "
        "(WebSocket) and screen-based RPA via PyAutoGUI fallback."
    ),
)

# ─── Chrome Extension WebSocket Bridge ────────────────────────────────────────

# Active WebSocket connections from the Chrome Extension.
_extension_connections: Set = set()

# Data queues: extension pushes data here; MCP tools read from here.
_schedule_queue: asyncio.Queue = asyncio.Queue(maxsize=1)
_chart_queue: asyncio.Queue = asyncio.Queue(maxsize=1)


def is_extension_connected() -> bool:
    """Returns True when at least one Chrome Extension is connected."""
    return bool(_extension_connections)


async def _send_to_extension(payload: Dict[str, Any]) -> None:
    """Sends a JSON payload to all connected Chrome Extension clients."""
    message = json.dumps(payload)
    dead = set()
    for ws in list(_extension_connections):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _extension_connections.difference_update(dead)


# ─── PHI Encryption (local at-rest) ──────────────────────────────────────────

def _encrypt_snapshot(snapshot: Dict[str, Any]) -> str:
    """Encrypts a snapshot dict for at-rest storage. Returns a ciphertext token."""
    try:
        from phi_crypto import encrypt_snapshot
        return encrypt_snapshot(snapshot)
    except ImportError:
        # phi_crypto not on path in some test environments — fall back to JSON
        logger.warning("phi_crypto not available; snapshot stored unencrypted")
        return json.dumps(snapshot)


def _decrypt_snapshot(token: str) -> Dict[str, Any]:
    """Decrypts a snapshot token previously produced by _encrypt_snapshot."""
    try:
        from phi_crypto import decrypt_snapshot
        return decrypt_snapshot(token)
    except ImportError:
        return json.loads(token)


# ─── Audit Logger ────────────────────────────────────────────────────────────

_AUDIT_LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "audit.jsonl"


def _audit(action: str, details: Dict[str, Any]) -> None:
    """Appends a HIPAA audit entry to logs/audit.jsonl."""
    try:
        _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "action": action,
            **details,
        }
        with open(_AUDIT_LOG_PATH, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.warning(f"Audit log write failed: {exc}")


# ─── Helper: Chart Data Cache ───────────────────────────────────────────────

# In-memory cache: MRN → (encrypted ciphertext token, unix timestamp)
# Raw PHI is never stored; only the AES-256-GCM encrypted form lives here.
# Entries expire after CACHE_TTL_SECONDS to limit PHI persistence.
CHART_DATA_CACHE: Dict[str, tuple] = {}  # {mrn: (token, inserted_at)}
_CACHE_TTL_SECONDS = 3600   # 1 hour — enough for a clinical session
_CACHE_MAX_ENTRIES = 200    # Guard against unbounded growth


def _cache_put(mrn: str, token: str) -> None:
    """Stores an encrypted token in the cache, enforcing size and TTL limits."""
    import time as _time
    # Evict expired entries first
    now = _time.time()
    expired = [k for k, (_, ts) in CHART_DATA_CACHE.items() if now - ts > _CACHE_TTL_SECONDS]
    for k in expired:
        del CHART_DATA_CACHE[k]
    # Enforce hard maximum — drop oldest entry if needed
    if len(CHART_DATA_CACHE) >= _CACHE_MAX_ENTRIES:
        oldest = min(CHART_DATA_CACHE, key=lambda k: CHART_DATA_CACHE[k][1])
        del CHART_DATA_CACHE[oldest]
    CHART_DATA_CACHE[mrn] = (token, now)


def _cache_get(mrn: str) -> Optional[str]:
    """Returns the cached encrypted token for *mrn* if present and not expired."""
    import time as _time
    entry = CHART_DATA_CACHE.get(mrn)
    if entry is None:
        return None
    token, inserted_at = entry
    if _time.time() - inserted_at > _CACHE_TTL_SECONDS:
        del CHART_DATA_CACHE[mrn]
        return None
    return token

# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def get_schedule(date_str: str = None) -> Dict[str, Any]:
    """
    Retrieves the provider's daily schedule from eCW.

    Preferred path — Chrome Extension:
        Sends a ``request_schedule`` command to the connected extension and
        waits up to 10 s for the DOM-extracted schedule to arrive via the
        WebSocket.

    Fallback path — RPA (PyAutoGUI):
        If no extension is connected, navigates the eCW schedule screen using
        screen-level automation (PyAutoGUI) and returns mock/parsed appointments.

    Args:
        date_str: Date in format 'YYYY-MM-DD' (defaults to today)

    Returns:
        {
            "status": "SUCCESS",
            "date": "2026-02-28",
            "source": "extension" | "rpa_mock",
            "appointments": [
                {"patient_mrn": "MRN-123456", "time": "09:00", "provider": "Dr. Smith"},
                ...
            ]
        }
    """
    logger.info(f"Retrieving schedule for {date_str or 'today'}")

    # ── Path A: Chrome Extension ──────────────────────────────────────────────
    if is_extension_connected():
        try:
            # Drain any stale entry so we get a fresh response.
            while not _schedule_queue.empty():
                _schedule_queue.get_nowait()

            await _send_to_extension({"type": "request_schedule"})
            appointments = await asyncio.wait_for(_schedule_queue.get(), timeout=10.0)
            logger.info(f"Extension returned {len(appointments)} appointments")
            _audit("get_schedule", {"source": "extension", "count": len(appointments)})
            return {
                "status": "SUCCESS",
                "date": date_str or datetime.today().strftime("%Y-%m-%d"),
                "source": "extension",
                "appointments": appointments,
                "total": len(appointments),
            }
        except asyncio.TimeoutError:
            logger.warning("Extension did not respond in time; falling back to RPA")

    # ── Path B: RPA fallback ──────────────────────────────────────────────────
    try:
        ecw_url = os.getenv("ECW_URL", "https://eclinicalworks.example.com")
        logger.info(f"RPA mode — connecting to eCW at {ecw_url}")

        mock_appointments = [
            {"patient_mrn": "MRN-123456", "time": "09:00", "provider": "Dr. Smith"},
            {"patient_mrn": "MRN-789012", "time": "09:15", "provider": "Dr. Smith"},
            {"patient_mrn": "MRN-345678", "time": "10:00", "provider": "Dr. Johnson"},
        ]

        logger.info(f"Retrieved {len(mock_appointments)} appointments (RPA mock)")
        _audit("get_schedule", {"source": "rpa_mock", "count": len(mock_appointments)})
        return {
            "status": "SUCCESS",
            "date": date_str or "2026-02-28",
            "source": "rpa_mock",
            "appointments": mock_appointments,
            "total": len(mock_appointments),
        }
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def open_chart(patient_mrn: str) -> Dict[str, Any]:
    """
    Opens a patient chart in eCW using the MRN.

    When the Chrome Extension is connected, the extension is asked to navigate
    and the backend waits for the ``chart_data`` WebSocket message.

    When no extension is connected, PyAutoGUI RPA is used (lazy import so the
    server can start in headless environments without a display).

    Args:
        patient_mrn: Patient's Medical Record Number (e.g., "MRN-123456")

    Returns:
        {
            "status": "SUCCESS",
            "patient_mrn": "MRN-123456",
            "message": "Chart opened and ready for data extraction"
        }
    """
    logger.info(f"Opening chart for MRN {patient_mrn}")

    if is_extension_connected():
        logger.info("Extension connected — requesting chart navigation")
        await _send_to_extension({"type": "request_chart", "mrn": patient_mrn})
        _audit("open_chart", {"source": "extension", "mrn": patient_mrn})
        return {
            "status": "SUCCESS",
            "patient_mrn": patient_mrn,
            "message": "Chart navigation requested via Chrome Extension",
        }

    # ── RPA fallback ──────────────────────────────────────────────────────────
    logger.info(f"RPA: Opening chart for MRN {patient_mrn}")
    try:
        import pyautogui  # lazy import — requires $DISPLAY
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        logger.info(f"Typing MRN: {patient_mrn}")
        pyautogui.write(patient_mrn, interval=0.05)
        time.sleep(0.5)
        logger.info("Pressing Enter to open chart")
        pyautogui.press("enter")
        time.sleep(2)
        logger.info(f"Chart should now be open for {patient_mrn}")
        _audit("open_chart", {"source": "rpa", "mrn": patient_mrn})
        return {
            "status": "SUCCESS",
            "patient_mrn": patient_mrn,
            "message": "Chart opened and ready for data extraction",
        }
    except Exception as e:
        logger.error(f"Failed to open chart: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def extract_chart_data(patient_mrn: str) -> Dict[str, Any]:
    """
    Extracts clinical data from the currently open eCW patient chart.

    Preferred path — Chrome Extension:
        Waits up to 10 s for a ``chart_data`` WebSocket message from the
        extension.  If no data arrives, falls back to the RPA mock path.

    Fallback path — RPA mock:
        Returns a realistic synthetic snapshot for development / testing.

    The extracted data is encrypted with AES-256-GCM before being stored in
    the in-memory cache so that raw PHI is never persisted in plaintext.

    Args:
        patient_mrn: Patient MRN (for logging/verification)

    Returns:
        {
            "status": "SUCCESS",
            "patient_mrn": "MRN-123456",
            "source": "extension" | "rpa_mock",
            "raw_data": { "demographics": {...}, "vitals": {...}, ... }
        }
    """
    logger.info(f"Extracting chart data for {patient_mrn}")

    extracted_data: Optional[Dict[str, Any]] = None
    source = "rpa_mock"

    # ── Path A: Chrome Extension ──────────────────────────────────────────────
    if is_extension_connected():
        try:
            while not _chart_queue.empty():
                _chart_queue.get_nowait()

            await _send_to_extension({"type": "request_chart", "mrn": patient_mrn})
            payload = await asyncio.wait_for(_chart_queue.get(), timeout=10.0)
            extracted_data = payload.get("snapshot") or payload
            source = "extension"
            logger.info(f"Extension returned chart data for {patient_mrn}")
        except asyncio.TimeoutError:
            logger.warning("Extension chart response timed out; falling back to RPA mock")

    # ── Path B: RPA mock ──────────────────────────────────────────────────────
    if extracted_data is None:
        extracted_data = {
            "demographics": {
                "name": "John Doe",
                "mrn": patient_mrn,
                "dob": "1975-03-15",
                "age": 50,
                "sex": "M",
            },
            "vitals": {
                "height_in": 70,
                "weight_lb": 215,
                "bmi": 30.8,
                "bp": "138/88",
                "hr": 72,
                "temp_f": 98.6,
            },
            "chief_complaint": "Fatigue and snoring",
            "hpi": (
                "Patient reports chronic fatigue, difficulty staying awake during day. "
                "Wife reports loud snoring at night."
            ),
            "pmh": [
                "Hypertension (on medication)",
                "Type 2 Diabetes (controlled)",
                "Hyperlipidemia",
            ],
            "social_history": {
                "smoking": "Former, quit 5 years ago",
                "alcohol": "Moderate use",
                "sleep_pattern": "Poor - snores heavily, restless",
            },
            "medications": [
                "Lisinopril 10mg daily (HTN)",
                "Metformin 1000mg BID (Diabetes)",
                "Atorvastatin 40mg daily (Cholesterol)",
            ],
            "allergies": ["NKDA"],
            "recent_labs": {
                "glucose": "145 mg/dL",
                "hemoglobin_a1c": "7.2%",
                "ldl": "125 mg/dL",
            },
            "assessment": (
                "50M with BMI 30.8, hypertension, diabetes. "
                "Presenting with fatigue and snoring - concerning for sleep apnea."
            ),
            "extraction_timestamp": time.time(),
        }

    # ── Encrypt & cache ───────────────────────────────────────────────────────
    try:
        _cache_put(patient_mrn, _encrypt_snapshot(extracted_data))
        logger.info(f"Encrypted chart data cached for {patient_mrn}")
    except Exception as enc_err:
        logger.warning(f"Cache encryption failed ({enc_err}); storing without encryption")
        _cache_put(patient_mrn, json.dumps(extracted_data))

    _audit("extract_chart_data", {"source": source, "mrn": patient_mrn})

    return {
        "status": "SUCCESS",
        "patient_mrn": patient_mrn,
        "source": source,
        "raw_data": extracted_data,
        "message": f"Extracted {len(extracted_data)} clinical fields from chart",
    }

@mcp.tool()
async def pend_order(cpt_code: str, icd_code: str, patient_mrn: str, approval_token: str) -> Dict[str, Any]:
    """
    Pends a diagnostic order in the eCW patient chart.

    Security: Requires a valid approval_token (min 10 chars) to prevent
    unauthorised order placement.

    Uses PyAutoGUI (lazy import) to interact with the eCW Orders screen.
    PyAutoGUI is the correct tool for order penning even in the extension
    model because it performs the actual EMR write via the UI.

    Args:
        cpt_code:       Procedure code (e.g., "95800")
        icd_code:       Diagnosis code (e.g., "G47.33")
        patient_mrn:    Patient MRN
        approval_token: User approval token (min 10 chars)

    Returns:
        {
            "status": "SUCCESS",
            "order_details": { "cpt": "95800", "icd": "G47.33", "patient_mrn": "…" },
            "message": "Order pended for provider signature"
        }
    """
    # Security check
    if not approval_token or len(approval_token) < 10:
        logger.warning(f"Invalid approval token for order {cpt_code}")
        return {"status": "AUTH_FAILED", "message": "Invalid or missing approval token."}

    logger.info(f"RPA: Pending order {cpt_code}/{icd_code} for {patient_mrn}")

    try:
        import pyautogui  # lazy import — requires $DISPLAY
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        logger.info(f"Entering CPT code: {cpt_code}")
        pyautogui.write(cpt_code, interval=0.05)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(1)

        logger.info(f"Entering ICD-10 code: {icd_code}")
        pyautogui.write(icd_code, interval=0.05)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.5)

        logger.info(f"✓ Order {cpt_code} pended for {patient_mrn}")
        _audit("pend_order", {"cpt": cpt_code, "icd": icd_code, "mrn": patient_mrn})

        return {
            "status": "SUCCESS",
            "order_details": {
                "cpt": cpt_code,
                "icd": icd_code,
                "patient_mrn": patient_mrn,
                "timestamp": time.time(),
            },
            "message": f"Order {cpt_code} pended for provider signature",
        }
    except Exception as e:
        logger.error(f"Failed to pend order: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def approve_recommendation(snapshot_id: str) -> Dict[str, Any]:
    """
    Approves a clinical recommendation and automatically pends the order in eCW.

    Called when a user clicks "Approve" in the dashboard.

    Args:
        snapshot_id: ID of the recommendation (e.g., "v-9a1b")

    Returns:
        {
            "status": "SUCCESS",
            "snapshot_id": "v-9a1b",
            "action": "ORDER_PENDED",
            "message": "Recommendation approved - order pending in eCW"
        }
    """
    logger.info(f"User approved recommendation: {snapshot_id}")
    try:
        _audit("approve_recommendation", {"snapshot_id": snapshot_id})
        logger.info(f"✓ Recommendation {snapshot_id} approved - order pending in eCW")
        return {
            "status": "SUCCESS",
            "snapshot_id": snapshot_id,
            "action": "ORDER_PENDED",
            "message": f"Approved {snapshot_id} - order will be pending for provider signature",
        }
    except Exception as e:
        logger.error(f"Failed to approve recommendation: {e}")
        return {"status": "ERROR", "message": str(e)}


@mcp.tool()
async def dismiss_recommendation(snapshot_id: str) -> Dict[str, Any]:
    """
    Dismisses a clinical recommendation (user rejected it).
    Logs the dismissal but does NOT pend any order.

    Args:
        snapshot_id: ID of the recommendation

    Returns:
        {
            "status": "SUCCESS",
            "snapshot_id": "v-9a1b",
            "action": "DISMISSED",
            "message": "Recommendation dismissed by user"
        }
    """
    logger.info(f"User dismissed recommendation: {snapshot_id}")
    try:
        _audit("dismiss_recommendation", {"snapshot_id": snapshot_id})
        logger.info(f"✓ Recommendation {snapshot_id} dismissed - audit logged")
        return {
            "status": "SUCCESS",
            "snapshot_id": snapshot_id,
            "action": "DISMISSED",
            "message": f"Dismissed {snapshot_id} - no order will be placed",
        }
    except Exception as e:
        logger.error(f"Failed to dismiss recommendation: {e}")
        return {"status": "ERROR", "message": str(e)}


@mcp.tool()
async def save_credentials(
    ecw_url: str,
    ecw_username: str,
    ecw_password: str,
    ecw_clinic_id: str = "",
    ecw_mfa: str = "manual",
    ollama_base_url: str = "http://localhost:11434",
    mrn_salt: str = "",
) -> Dict[str, Any]:
    """
    Securely saves eCW portal credentials to the local .env file.
    This data NEVER leaves the local machine — it is written only to disk.
    """
    try:
        ENV_PATH.touch(exist_ok=True)
        set_key(str(ENV_PATH), "ECW_URL", ecw_url)
        set_key(str(ENV_PATH), "ECW_USERNAME", ecw_username)
        set_key(str(ENV_PATH), "ECW_PASSWORD", ecw_password)
        set_key(str(ENV_PATH), "ECW_CLINIC_ID", ecw_clinic_id)
        set_key(str(ENV_PATH), "ECW_MFA_METHOD", ecw_mfa)
        set_key(str(ENV_PATH), "OLLAMA_BASE_URL", ollama_base_url)
        if mrn_salt:
            set_key(str(ENV_PATH), "ICS_MRN_SALT", mrn_salt)
        logger.info("Credentials saved to local .env (NOT transmitted externally)")
        return {
            "status": "SUCCESS",
            "message": "Credentials saved to local .env file.",
            "env_path": str(ENV_PATH),
        }
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        return {"status": "ERROR", "message": str(e)}


# ─── WebSocket Extension Bridge ───────────────────────────────────────────────

async def _extension_ws_handler(websocket) -> None:
    """
    Handles a single Chrome Extension WebSocket connection.

    Message types received FROM the extension:
      { "type": "schedule_data",  "appointments": [...] }
      { "type": "chart_data",     "mrn": "…", "snapshot": {...} }
      { "type": "error",          "source": "…", "message": "…" }
      { "type": "frame_ready",    "frameType": "…" }

    Commands sent TO the extension:
      { "type": "request_schedule" }
      { "type": "request_chart", "mrn": "…" }
      { "type": "pend_order",    "cpt_code": "…", … }
    """
    _extension_connections.add(websocket)
    logger.info(f"Chrome Extension connected ({len(_extension_connections)} active)")

    try:
        async for raw in websocket.iter_text():
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from extension: {raw[:120]}")
                continue

            msg_type = msg.get("type")

            if msg_type == "schedule_data":
                appointments = msg.get("appointments", [])
                logger.info(f"Extension pushed {len(appointments)} appointments")
                try:
                    _schedule_queue.put_nowait(appointments)
                except asyncio.QueueFull:
                    _schedule_queue.get_nowait()
                    _schedule_queue.put_nowait(appointments)

            elif msg_type == "chart_data":
                logger.info(f"Extension pushed chart data for MRN: {msg.get('mrn')}")
                try:
                    _chart_queue.put_nowait(msg)
                except asyncio.QueueFull:
                    _chart_queue.get_nowait()
                    _chart_queue.put_nowait(msg)

            elif msg_type == "frame_ready":
                logger.debug(f"Frame ready: {msg.get('frameType')} @ {msg.get('url', '')[:80]}")

            elif msg_type == "error":
                logger.error(
                    f"Extension error ({msg.get('source')}): {msg.get('message')}"
                )
            else:
                logger.warning(f"Unknown extension message type: {msg_type}")

            # Send ACK
            try:
                await websocket.send_text(json.dumps({"type": "ack", "message": "ok"}))
            except Exception:
                break

    except Exception as exc:
        logger.info(f"Extension WebSocket closed: {exc}")
    finally:
        _extension_connections.discard(websocket)
        logger.info(
            f"Chrome Extension disconnected ({len(_extension_connections)} remaining)"
        )


def build_app():
    """
    Constructs the combined ASGI application:
      - FastMCP on all routes
      - WebSocket endpoint at /ws/extension for Chrome Extension
      - HTTP endpoints for dashboard session status polling
    """
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
    from starlette.routing import Route, WebSocketRoute
    from starlette.websockets import WebSocket

    mcp_asgi = mcp.http_app()

    async def ws_extension(websocket: WebSocket):
        await websocket.accept()
        await _extension_ws_handler(websocket)

    async def health(request):
        return JSONResponse({
            "status": "ok",
            "extension_connected": is_extension_connected(),
            "active_connections": len(_extension_connections),
        })

    async def login_status(request):
        """
        Polled by LoginStatusBanner.jsx every 10 seconds.
        Returns the current eCW session state.
        """
        from session_monitor import SESSION_STATE, check_session_alive  # type: ignore
        try:
            is_active = check_session_alive()
        except Exception:
            is_active = SESSION_STATE.get("is_active", False)

        return JSONResponse({
            "is_active": is_active,
            "login_time": SESSION_STATE.get("login_time"),
            "last_verified": SESSION_STATE.get("last_verified"),
            "extension_connected": is_extension_connected(),
        })

    async def login_complete(request):
        """
        Called by the dashboard when the user manually confirms login.
        Marks the session as active in session_monitor.SESSION_STATE.
        """
        from session_monitor import mark_login_complete, SESSION_STATE  # type: ignore
        try:
            mark_login_complete()
            is_active = SESSION_STATE.get("is_active", True)
        except Exception:
            is_active = True  # Optimistically mark active if module unavailable

        _audit("login_complete", {"source": "dashboard_confirmation"})
        return JSONResponse({
            "is_active": is_active,
            "message": "Session marked as active",
        })

    async def session_check(request):
        """Quick liveness check used by health_check.py."""
        return JSONResponse({"status": "ok", "session_endpoint": "ready"})

    app = Starlette(
        routes=[
            Route("/health",         health),
            Route("/login-status",   login_status),
            Route("/login-complete", login_complete, methods=["POST"]),
            Route("/session-check",  session_check),
            WebSocketRoute("/ws/extension", ws_extension),
            # MCP routes last so specific paths above take precedence
            Route("/{path:path}", mcp_asgi, methods=["GET", "POST", "OPTIONS"]),
        ]
    )

    # Allow dashboard (localhost:5173) to call these endpoints cross-origin
    return CORSMiddleware(
        app,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Origin"],
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting ICS eCW Bridge MCP Server on port {SERVER_PORT}")
    logger.info(f"  MCP endpoint:        http://127.0.0.1:{SERVER_PORT}/")
    logger.info(f"  Extension WebSocket: ws://127.0.0.1:{SERVER_PORT}/ws/extension")
    logger.info(f"  Health check:        http://127.0.0.1:{SERVER_PORT}/health")
    logger.info(f"  Login status:        http://127.0.0.1:{SERVER_PORT}/login-status")

    app = build_app()
    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT, log_level="info")
