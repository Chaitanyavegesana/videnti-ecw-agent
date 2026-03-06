"""
Visual Driver - RPA Automation with Calibrated Coordinates
Uses PyAutoGUI and anchor images to perform OS-level UI automation.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Tuple, Optional

import pyautogui as pag

from ecw_login import login_to_ecw, is_already_logged_in
from session_monitor import check_session_alive, get_session_debug_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VISUAL_DRIVER] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Anchor coordinates (relative to screen origin)
ANCHOR_MAP = {
    "hub_button": (800, 300),  # Approximate location of Hub button
    "schedule_button": (850, 350),  # Approximate location of Schedule button
    "patient_search": (900, 400),  # Approximate location of Patient Search
}

ANCHORS_DIR = Path(__file__).parent / "logs" / "anchors"


def load_anchor_map() -> Dict[str, Tuple[int, int]]:
    """Load calibrated coordinates from anchor map file."""
    try:
        map_file = ANCHORS_DIR / "anchor_map.json"
        if map_file.exists():
            with open(map_file, 'r') as f:
                coords = json.load(f)
            logger.info(f"✓ Loaded {len(coords)} anchors from map")
            return coords
        else:
            logger.warning("anchor_map.json not found, using defaults")
            return ANCHOR_MAP.copy()
    except Exception as e:
        logger.error(f"Error loading anchor map: {e}")
        return ANCHOR_MAP.copy()


def bring_to_front() -> bool:
    """Bring Chrome window to front using AppleScript."""
    try:
        import subprocess
        subprocess.run(
            ['osascript', '-e',
             'tell application "Google Chrome" to activate'],
            timeout=5, check=True,
        )
        time.sleep(0.5)
        logger.info("✓ Chrome brought to front")
        return True
    except Exception as e:
        logger.error(f"Failed to bring Chrome to front: {e}")
        return False


def ensure_logged_in() -> bool:
    """Ensure session is active; prompt for login if needed."""
    if check_session_alive():
        logger.info("✓ Session already active")
        return True

    logger.info("Session lost, initiating re-login...")
    result = login_to_ecw()

    if result["status"] == "SUCCESS":
        logger.info("✓ Re-login successful")
        return True
    else:
        logger.error(f"Re-login failed: {result['message']}")
        return False


def navigate_to_schedule(anchor_coords: Optional[Dict] = None) -> bool:
    """Navigate to Schedule view using visual coordinates."""
    if anchor_coords is None:
        anchor_coords = load_anchor_map()

    try:
        # Move mouse to Schedule button location
        schedule_x, schedule_y = anchor_coords.get("schedule_button", (850, 350))
        logger.info(f"Moving to schedule button: ({schedule_x}, {schedule_y})")

        pag.moveTo(schedule_x, schedule_y, duration=0.5)
        time.sleep(0.3)

        # Click
        pag.click()
        time.sleep(2)

        logger.info("✓ Navigated to Schedule")
        return True

    except Exception as e:
        logger.error(f"Navigation error: {e}")
        return False


def get_schedule_snapshot() -> Optional[str]:
    """Capture current schedule view and save screenshot."""
    try:
        timestamp = int(time.time())
        screenshot_path = Path(__file__).parent / "logs" / "screenshots" / f"schedule_{timestamp}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        screenshot = pag.screenshot()
        screenshot.save(str(screenshot_path))

        logger.info(f"✓ Screenshot saved to {screenshot_path}")
        return str(screenshot_path)

    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return None


def main():
    """Main RPA workflow."""
    logger.info("=" * 60)
    logger.info("STARTING VISUAL RPA DRIVER")
    logger.info("=" * 60)

    # Step 1: Ensure logged in
    if not ensure_logged_in():
        logger.error("❌ Login failed — cannot proceed")
        return False

    # Step 2: Bring Chrome to front
    if not bring_to_front():
        logger.warning("⚠ Could not bring Chrome to front")

    # Step 3: Navigate to schedule
    if not navigate_to_schedule():
        logger.error("❌ Navigation failed")
        return False

    # Step 4: Capture screenshot
    screenshot = get_schedule_snapshot()
    if not screenshot:
        logger.error("❌ Screenshot failed")
        return False

    # Step 5: Print session info
    logger.info("\nSession Debug Info:")
    logger.info(json.dumps(get_session_debug_info(), indent=2))

    logger.info("\n" + "=" * 60)
    logger.info("✓ VISUAL RPA DRIVER COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
