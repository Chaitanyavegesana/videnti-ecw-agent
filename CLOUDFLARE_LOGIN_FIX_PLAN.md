# Cloudflare-Resilient eCW Login — Implementation Plan

**Document Status:** Implementation guide with current codebase state  
**Date:** March 6, 2026  
**Scope:** Fix corrupted files, complete remaining integration, achieve working login flow

---

## Current Codebase State (as of March 6, 2026)

### Files — Working

| File | Lines | Status | Description |
|------|-------|--------|-------------|
| `chrome_helper.py` | 256 | ✅ Clean | AppleScript Chrome tab management (8 functions) |
| `session_monitor.py` | 213 | ✅ Clean | Session health tracking (6 functions + SESSION_STATE) |
| `mcp_servers/ecw_bridge/server.py` | 497 | ✅ Clean | FastMCP-based MCP server (7 tools) |
| `dashboard/src/App.jsx` | ~350 | ✅ Clean | React dashboard with queue, stats, settings |

### Files — Corrupted (MUST FIX)

| File | Lines | Issue |
|------|-------|-------|
| `ecw_login.py` | 76 | ~60% garbled text — `verify_login_success()` and `login_to_ecw()` are unreadable |
| `dashboard/src/LoginStatusBanner.jsx` | 104 | ~40% garbled — polling logic and CSS broken |
| `health_check.py` | 74 | ~50% garbled — endpoint checking loop and results display broken |

### Files — Missing (MUST CREATE)

| File | Was | Notes |
|------|-----|-------|
| `visual_driver.py` | Deleted | Was 80 lines. Coordinate-based navigation using `logs/visual_coordinate_map.json` |
| `.env` | Never created | Needs `ECW_URL`, `ECW_USERNAME`, `ECW_PASSWORD`, `ECW_MFA_METHOD` |

### Files — NOT YET INTEGRATED

| File | Issue |
|------|-------|
| `mcp_servers/ecw_bridge/server.py` | Missing `/login-status`, `/login-complete`, `/session-check` endpoints |
| `mcp_servers/ecw_bridge/server.py` | No CORS middleware (dashboard on :5173 can't call :8001) |
| `dashboard/src/App.jsx` | Does NOT import or render `LoginStatusBanner` |

### Visual Anchors Available
- `logs/anchors/hub_button.png` — eCW dashboard hub button
- `logs/anchors/schedule_button.png` — Schedule view button
- `logs/anchors/patient_search.png` — Patient search field

### Dual Server Architecture (Important)
Two server directories exist:
- `mcp_servers/` (underscore) — Uses `FastMCP` (from `mcp.server.fastmcp`) → **This is the active one**
- `mcp-servers/` (hyphen) — Also uses `FastMCP` → **Legacy copy, do not modify**

Only modify files in `mcp_servers/` (underscore version).

---

## Problem Statement

The eCW login page has **Cloudflare Turnstile** ("Verify you are human"). When Chrome is navigated programmatically (AppleScript `open location` or keyboard automation), Cloudflare detects the programmatic origin and blocks login.

**Key facts:**
- Manual login in user-opened Chrome always works
- Programmatic launch triggers Cloudflare even with OS-level PyAutoGUI events
- No eCW API access — UI automation is the only option
- Sessions stay active once logged in manually

**Solution:** Never automate the login itself. Treat it as a human step. Focus on:
1. Detecting if already logged in (session persistence)
2. Prompting the user when login is needed
3. Verifying login success after user completes it
4. Keeping sessions alive

---

## Implementation Steps (Exact Order)

### Step 1: Fix `ecw_login.py` (CORRUPTED — REWRITE)

The current file has garbled text starting around line 35. Replace the **entire file** with:

```python
"""
eCW Login Module - Session-First Login Flow
Handles authentication with Cloudflare-protected eClinicalWorks portal.
Treats login as a human step — never automates Cloudflare or credential entry.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

from chrome_helper import is_chrome_running, find_ecw_tab, activate_ecw_tab
from session_monitor import check_session_alive, mark_login_complete, SESSION_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ECW_LOGIN] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

ECW_URL = "https://txlaacapp.ecwcloud.com/mobiledoc/jsp/webemr/login/newLogin.jsp"


def is_already_logged_in() -> bool:
    """Fast check using session monitor."""
    return check_session_alive()


def activate_browser() -> bool:
    """Activate already-running Chrome. Never launches Chrome."""
    if not is_chrome_running():
        logger.warning("Chrome is not running — user must open it manually")
        return False
    try:
        subprocess.run(
            ['osascript', '-e', 'tell application "Google Chrome" to activate'],
            timeout=5, check=True,
        )
        time.sleep(1)
        logger.info("✓ Chrome activated")
        return True
    except Exception as e:
        logger.error(f"Failed to activate Chrome: {e}")
        return False


def verify_login_success(max_retries: int = 3) -> bool:
    """Verify login by checking session state multiple times."""
    for attempt in range(max_retries):
        if check_session_alive():
            mark_login_complete()
            logger.info("✓ Login verified successfully")
            return True
        logger.info(f"Verification attempt {attempt + 1}/{max_retries} — waiting 2s...")
        time.sleep(2)
    logger.warning("Login verification failed after all retries")
    return False


def login_to_ecw() -> Dict[str, Any]:
    """
    Session-first login flow.

    Path 1: Session active → return SUCCESS immediately
    Path 2: Chrome not running → return NEEDS_HUMAN
    Path 3: Session inactive → prompt user for manual login → verify
    """
    logger.info("=" * 60)
    logger.info("CHECKING eCW SESSION")
    logger.info("=" * 60)

    try:
        # Path 1: Already logged in
        if is_already_logged_in():
            logger.info("✓ Active session detected")
            return {
                "status": "SUCCESS",
                "message": "Session already active",
                "requires_prompt": False,
            }

        # Path 2: Chrome not running
        if not is_chrome_running():
            return {
                "status": "NEEDS_HUMAN",
                "message": "Please open Google Chrome and navigate to eCW",
                "requires_prompt": True,
            }

        # Path 3: Find or create eCW tab, then prompt user
        tab = find_ecw_tab()
        if not tab:
            logger.info("No eCW tab found — opening one")
            subprocess.run(
                ['osascript', '-e',
                 f'tell application "Google Chrome" to open location "{ECW_URL}"'],
                timeout=5, check=True,
            )
            time.sleep(5)
        else:
            activate_ecw_tab()
            time.sleep(1)

        # Prompt user for manual login
        logger.info("\n" + "=" * 60)
        logger.info("  LOGIN REQUIRED")
        logger.info("=" * 60)
        logger.info("  Cloudflare verification requires a human.")
        logger.info("  Please complete these steps in Chrome:")
        logger.info("    1. Click 'Verify you are human'")
        logger.info("    2. Enter your username and password")
        logger.info("    3. Complete MFA if prompted")
        logger.info("    4. Wait until you see the eCW dashboard")
        logger.info("  Then press ENTER here to continue...")
        logger.info("=" * 60 + "\n")

        SESSION_STATE["needs_login"] = True

        try:
            input()
        except EOFError:
            return {
                "status": "CANCELLED",
                "message": "No terminal input available",
                "requires_prompt": True,
            }

        # Verify login success
        time.sleep(2)
        if verify_login_success():
            return {
                "status": "SUCCESS",
                "message": "Login verified successfully",
                "requires_prompt": True,
                "timestamp": time.time(),
            }
        else:
            return {
                "status": "WARNING",
                "message": "Login prompt shown but could not verify session",
                "requires_prompt": True,
            }

    except Exception as e:
        logger.error(f"Login error: {e}")
        return {
            "status": "ERROR",
            "message": str(e),
            "requires_prompt": True,
        }


if __name__ == "__main__":
    result = login_to_ecw()
    print(f"\nLogin Result: {result}\n")
```

**Verification:**
```bash
.venv/bin/python -c "from ecw_login import is_already_logged_in; print(is_already_logged_in())"
```

---

### Step 2: Fix `dashboard/src/LoginStatusBanner.jsx` (CORRUPTED — REWRITE)

Replace the entire file with:

```jsx
/**
 * LoginStatusBanner Component
 * Polls /login-status every 10 seconds, shows session state.
 */
import React, { useState, useEffect } from 'react';

const LoginStatusBanner = () => {
  const [status, setStatus] = useState(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('http://localhost:8001/login-status');
        if (res.ok) setStatus(await res.json());
      } catch { /* server not running */ }
    };
    poll();
    const id = setInterval(poll, 10000);
    return () => clearInterval(id);
  }, []);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      const res = await fetch('http://localhost:8001/login-complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(prev => ({ ...prev, is_active: data.session_active, needs_login: !data.session_active }));
      }
    } catch { /* ignore */ }
    setConfirming(false);
  };

  if (!status) return null;

  const active = status.is_active;

  return (
    <div style={{
      padding: '12px 20px',
      marginBottom: '16px',
      borderRadius: '8px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontSize: '14px',
      fontWeight: 500,
      background: active ? '#d4edda' : '#fff3cd',
      border: active ? '1px solid #c3e6cb' : '1px solid #ffeeba',
      color: active ? '#155724' : '#856404',
    }}>
      <span>
        {active
          ? '● eCW Session Active'
          : '○ Login Required — Please log in to eCW in Chrome'}
        {status.session_duration && active && (
          <span style={{ marginLeft: 8, opacity: 0.7 }}>({status.session_duration})</span>
        )}
      </span>
      {!active && (
        <button
          onClick={handleConfirm}
          disabled={confirming}
          style={{
            padding: '6px 16px',
            background: '#1976d2',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: confirming ? 'not-allowed' : 'pointer',
            fontSize: '13px',
          }}
        >
          {confirming ? 'Checking...' : "I've Logged In"}
        </button>
      )}
    </div>
  );
};

export default LoginStatusBanner;
```

---

### Step 3: Add LoginStatusBanner to `dashboard/src/App.jsx`

The `LoginStatusBanner` component exists but is NOT imported or rendered in `App.jsx`.

**Add this import** at line 1 of `App.jsx`:
```jsx
import LoginStatusBanner from './LoginStatusBanner';
```

**Add this JSX** as the first child inside the main content area (after the header, before the stats grid):
```jsx
<LoginStatusBanner />
```

---

### Step 4: Add Login Endpoints to `mcp_servers/ecw_bridge/server.py`

The server currently uses **FastMCP** (not FastAPI). It has 7 `@mcp.tool()` functions but **no** `/login-status`, `/login-complete`, or `/session-check` endpoints, and **no CORS**.

Since the server uses `mcp.asgi()` to create a Starlette-compatible ASGI app, add the REST endpoints by creating a combined ASGI app.

**Replace the `if __name__ == "__main__"` block** at the bottom of the file with:

```python
if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import sys
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    logger.info(f"Starting ICS eCW Bridge MCP Server on port {SERVER_PORT}")

    # --- REST endpoints for Dashboard integration ---
    
    async def login_status(request):
        """GET /login-status — returns session state for dashboard polling."""
        try:
            from session_monitor import get_session_status
            return JSONResponse(get_session_status())
        except Exception as e:
            return JSONResponse({"is_active": False, "needs_login": True, "error": str(e)})

    async def login_complete(request):
        """POST /login-complete — user confirms manual login."""
        try:
            from session_monitor import mark_login_complete, check_session_alive
            mark_login_complete()
            alive = check_session_alive()
            return JSONResponse({
                "status": "SUCCESS" if alive else "UNVERIFIED",
                "session_active": alive,
                "message": "Login marked complete" if alive else "Could not verify session",
            })
        except Exception as e:
            return JSONResponse({"status": "ERROR", "message": str(e)})

    async def session_check(request):
        """GET /session-check — actively verifies session (triggers visual check)."""
        try:
            from session_monitor import check_session_alive, get_session_status
            check_session_alive()
            return JSONResponse(get_session_status())
        except Exception as e:
            return JSONResponse({"is_active": False, "error": str(e)})

    async def health(request):
        """GET /health — server health check."""
        return JSONResponse({"status": "healthy", "service": "eCW Bridge", "port": SERVER_PORT})

    # Build combined app: REST routes + MCP ASGI
    rest_routes = [
        Route("/health", health, methods=["GET"]),
        Route("/login-status", login_status, methods=["GET"]),
        Route("/login-complete", login_complete, methods=["POST"]),
        Route("/session-check", session_check, methods=["GET"]),
    ]

    rest_app = Starlette(routes=rest_routes)
    mcp_app = mcp.asgi()

    # Combine: try REST first, fall through to MCP
    from starlette.routing import Router

    async def combined_app(scope, receive, send):
        """Route /health, /login-*, /session-* to REST; everything else to MCP."""
        path = scope.get("path", "")
        if path in ("/health", "/login-status", "/login-complete", "/session-check"):
            await rest_app(scope, receive, send)
        else:
            await mcp_app(scope, receive, send)

    # Wrap with CORS
    from starlette.middleware.cors import CORSMiddleware as CORSMw

    final_app = CORSMw(
        combined_app,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(
        final_app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="info",
    )
```

**Verification:**
```bash
# Start server
.venv/bin/python mcp_servers/ecw_bridge/server.py &

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8001/login-status
curl -X POST http://localhost:8001/login-complete
curl http://localhost:8001/session-check
```

---

### Step 5: Fix `health_check.py` (CORRUPTED — REWRITE)

Replace the entire file with:

```python
"""
Health Check — Service Connectivity Verification
Tests all service endpoints to verify system is operational.
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [HEALTH-CHECK] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SERVICES = {
    "eCW Bridge": {"url": "http://localhost:8001", "endpoints": ["/health", "/login-status", "/session-check"]},
    "Dashboard": {"url": "http://localhost:5173", "endpoints": ["/"]},
    "Ollama": {"url": "http://localhost:8000", "endpoints": ["/health"]},
    "Search": {"url": "http://localhost:8002", "endpoints": ["/health"]},
}


async def check_service(name: str, base_url: str, endpoints: list) -> dict:
    """Check if a service and its endpoints are responding."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint in endpoints:
            try:
                resp = await client.get(f"{base_url}{endpoint}")
                results[endpoint] = {"status": resp.status_code, "ok": resp.status_code < 400}
            except Exception as e:
                results[endpoint] = {"status": "ERROR", "ok": False, "error": str(e)}
    return results


async def main():
    """Run all health checks."""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60 + "\n")

    all_ok = True
    for name, config in SERVICES.items():
        results = await check_service(name, config["url"], config["endpoints"])
        service_ok = all(r["ok"] for r in results.values())
        icon = "✅" if service_ok else "❌"
        print(f"{icon} {name} ({config['url']})")
        for ep, r in results.items():
            ep_icon = "  ✓" if r["ok"] else "  ✗"
            print(f"   {ep_icon} {ep} → {r['status']}")
        if not service_ok:
            all_ok = False

    print("\n" + "=" * 60)
    print("✅ All systems operational" if all_ok else "❌ Some services offline")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Step 6: Recreate `visual_driver.py` (MISSING — CREATE)

```python
"""
Visual Driver — Coordinate-based RPA navigation for eCW.
Uses calibrated screen coordinates from logs/visual_coordinate_map.json.
"""

import json
import time
import logging
from pathlib import Path
from ecw_login import login_to_ecw

logging.basicConfig(level=logging.INFO, format="%(asctime)s [VISUAL_DRIVER] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MAP_PATH = Path("logs/visual_coordinate_map.json")


def load_map():
    """Load calibrated coordinate map."""
    if not MAP_PATH.exists():
        raise FileNotFoundError(f"Coordinate map not found at {MAP_PATH}. Run: python rpa_calibrator.py")
    with open(MAP_PATH, "r") as f:
        return json.load(f)


def bring_to_front():
    """Bring Chrome to front on macOS."""
    import os
    os.system('osascript -e "tell application \\"Google Chrome\\" to activate"')
    time.sleep(1)


def ensure_logged_in():
    """Ensure user is logged into eCW before proceeding."""
    from session_monitor import check_session_alive

    if check_session_alive():
        logger.info("✓ Session verified via monitor")
        return True

    logger.info("Session not active — initiating login flow")
    result = login_to_ecw()
    if result.get("status") not in ("SUCCESS", "WARNING"):
        raise Exception(f"Failed to login: {result.get('message')}")
    logger.info("✓ Logged in or already authenticated")
    return True


def navigate_to_schedule():
    """Navigate to schedule using calibrated coordinates."""
    import pyautogui
    coord_map = load_map()
    elements = coord_map.get("elements", {})

    if "schedule_button" not in elements:
        raise ValueError("Schedule button coordinates missing from map.")

    target = elements["schedule_button"]
    logger.info(f"Moving to schedule button at ({target['x']}, {target['y']})")

    pyautogui.moveTo(target["x"], target["y"], duration=0.8)
    pyautogui.click()
    logger.info("✓ Clicked Schedule button.")
    time.sleep(2)


def get_schedule_snapshot():
    """Take screenshot of the schedule area."""
    import pyautogui
    bring_to_front()
    ensure_logged_in()
    navigate_to_schedule()
    time.sleep(3)

    screenshot_path = Path("logs/screenshots/latest_schedule.png")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    pyautogui.screenshot(str(screenshot_path))
    logger.info(f"✓ Screenshot saved to {screenshot_path}")
    return screenshot_path


if __name__ == "__main__":
    try:
        bring_to_front()
        ensure_logged_in()
        navigate_to_schedule()
        logger.info("✓ Visual RPA automation completed")
    except Exception as e:
        logger.error(f"Visual RPA failed: {e}")
        raise
```

---

### Step 7: Create `.env` file

```env
ECW_URL=https://txlaacapp.ecwcloud.com/mobiledoc/jsp/webemr/login/newLogin.jsp
ECW_USERNAME=
ECW_PASSWORD=
ECW_MFA_METHOD=manual
OLLAMA_BASE_URL=http://localhost:11434
```

User must fill in `ECW_USERNAME` and `ECW_PASSWORD` before first run.

---

## Verification Checklist

After implementing all steps, verify:

- [ ] `python -c "from chrome_helper import get_chrome_state; print(get_chrome_state())"` → returns valid dict
- [ ] `python -c "from session_monitor import check_session_alive; print(check_session_alive())"` → returns bool
- [ ] `python -c "from ecw_login import login_to_ecw; print(login_to_ecw())"` → returns status dict (no garbled text)
- [ ] `python mcp_servers/ecw_bridge/server.py &` → starts on port 8001
- [ ] `curl http://localhost:8001/health` → `{"status":"healthy",...}`
- [ ] `curl http://localhost:8001/login-status` → `{"is_active":...,"needs_login":...}`
- [ ] `curl -X POST http://localhost:8001/login-complete` → `{"status":"SUCCESS",...}`
- [ ] `cd dashboard && npm run dev` → starts on port 5173
- [ ] Dashboard shows login status banner (green or yellow)
- [ ] `python health_check.py` → shows all services status
- [ ] `python visual_driver.py` → runs (requires calibration + login)

---

## User Workflow (After Implementation)

```
1. User opens Chrome manually
2. User starts system: python mcp_servers/ecw_bridge/server.py
3. Dashboard shows "Login Required" (yellow banner)
4. User navigates to eCW in Chrome
5. User clicks Cloudflare "Verify you are human"
6. User enters credentials + MFA
7. User clicks "I've Logged In" in dashboard
8. Dashboard turns green "Session Active"
9. RPA automation proceeds (schedule capture, chart extraction, etc.)
10. Session stays alive — no re-login needed for hours
```

---

## Critical Rules

1. **NEVER launch Chrome programmatically** — only interact with user-opened Chrome
2. **NEVER type credentials automatically** — user enters them manually
3. **NEVER bypass Cloudflare** — treat it as a human step (like MFA)
4. **Session persistence is the primary strategy** — minimize login frequency
5. **Only modify `mcp_servers/`** (underscore) — not `mcp-servers/` (hyphen)
6. **macOS only** — AppleScript is macOS-specific
7. **HIPAA compliance** — never log credentials or send PHI externally

