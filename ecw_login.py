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
