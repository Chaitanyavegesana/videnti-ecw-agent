#!/usr/bin/env python3
"""
Session Monitor Module

Tracks eCW login session state using visual anchor detection.
Maintains global SESSION_STATE available to all modules.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import time

# Global session state - persistent across all modules
SESSION_STATE = {
    "is_active": False,
    "last_verified": None,
    "login_time": None,
    "needs_login": True,
    "consecutive_failures": 0,
    "last_error": None,
}


def check_session_alive() -> bool:
    """
    Verify if session is currently active through 6-step validation.
    
    Steps:
    1. Check if Chrome process running
    2. Check if eCW tab exists
    3. Check if not on login page
    4. Check if hub button visible (visual anchor)
    5. Check URL correctness
    6. Return overall result
    
    Returns:
        bool: True if session active, False otherwise
    """
    global SESSION_STATE
    
    # Import here to avoid circular imports
    from chrome_helper import (
        is_chrome_running,
        find_ecw_tab,
        is_on_login_page,
        is_on_ecw_page,
        get_active_tab_url,
    )
    
    try:
        # Step 1: Chrome running?
        if not is_chrome_running():
            SESSION_STATE["consecutive_failures"] += 1
            SESSION_STATE["last_error"] = "Chrome not running"
            return False
        
        # Step 2: eCW tab exists?
        if not find_ecw_tab():
            SESSION_STATE["consecutive_failures"] += 1
            SESSION_STATE["last_error"] = "eCW tab not found"
            return False
        
        # Step 3: Not on login page?
        if is_on_login_page():
            SESSION_STATE["consecutive_failures"] += 1
            SESSION_STATE["last_error"] = "Still on login page"
            return False
        
        # Step 4: On eCW page?
        if not is_on_ecw_page():
            SESSION_STATE["consecutive_failures"] += 1
            SESSION_STATE["last_error"] = "Not on eCW page"
            return False
        
        # Step 5: URL valid?
        url = get_active_tab_url()
        if not url or "eclinicalworks" not in url.lower():
            SESSION_STATE["consecutive_failures"] += 1
            SESSION_STATE["last_error"] = "Invalid URL"
            return False
        
        # Step 6: All checks passed!
        SESSION_STATE["is_active"] = True
        SESSION_STATE["last_verified"] = datetime.now()
        SESSION_STATE["needs_login"] = False
        SESSION_STATE["consecutive_failures"] = 0
        SESSION_STATE["last_error"] = None
        
        return True
        
    except Exception as e:
        SESSION_STATE["consecutive_failures"] += 1
        SESSION_STATE["last_error"] = str(e)
        return False


def get_session_status() -> Dict:
    """
    Return current session state including all metadata.
    
    Returns:
        Dict: Session state including:
            - is_active: bool
            - last_verified: Optional[str] (ISO format)
            - login_time: Optional[str] (ISO format)
            - needs_login: bool
            - consecutive_failures: int
            - last_error: Optional[str]
            - session_duration: Optional[str] (human readable)
    """
    global SESSION_STATE
    
    # Calculate session duration if logged in
    session_duration = None
    if SESSION_STATE["login_time"]:
        try:
            login_dt = datetime.fromisoformat(SESSION_STATE["login_time"])
            duration = datetime.now() - login_dt
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            session_duration = f"{int(hours)}h {int(minutes)}m"
        except:
            session_duration = None
    
    return {
        "is_active": SESSION_STATE["is_active"],
        "last_verified": SESSION_STATE["last_verified"].isoformat() if SESSION_STATE["last_verified"] else None,
        "login_time": SESSION_STATE["login_time"],
        "needs_login": SESSION_STATE["needs_login"],
        "consecutive_failures": SESSION_STATE["consecutive_failures"],
        "last_error": SESSION_STATE["last_error"],
        "session_duration": session_duration,
    }


def mark_login_complete():
    """
    Update session state after successful login.
    Called after user completes Cloudflare + credentials + MFA.
    """
    global SESSION_STATE
    
    SESSION_STATE["is_active"] = True
    SESSION_STATE["login_time"] = datetime.now().isoformat()
    SESSION_STATE["last_verified"] = datetime.now()
    SESSION_STATE["needs_login"] = False
    SESSION_STATE["consecutive_failures"] = 0
    SESSION_STATE["last_error"] = None


def reset_session():
    """
    Clear session state completely.
    Called when user logs out or session expires.
    """
    global SESSION_STATE
    
    SESSION_STATE["is_active"] = False
    SESSION_STATE["last_verified"] = None
    SESSION_STATE["login_time"] = None
    SESSION_STATE["needs_login"] = True
    SESSION_STATE["consecutive_failures"] = 0
    SESSION_STATE["last_error"] = None


def verify_session_timeout(inactivity_minutes: int = 120) -> bool:
    """
    Check if session has timed out due to inactivity.
    
    Args:
        inactivity_minutes: Minutes of inactivity before timeout (default: 120)
    
    Returns:
        bool: True if session still valid, False if timed out
    """
    global SESSION_STATE
    
    if not SESSION_STATE["last_verified"]:
        return False
    
    try:
        last_verified = datetime.fromisoformat(SESSION_STATE["last_verified"].isoformat() if isinstance(SESSION_STATE["last_verified"], datetime) else SESSION_STATE["last_verified"])
        elapsed = datetime.now() - last_verified
        
        if elapsed > timedelta(minutes=inactivity_minutes):
            reset_session()
            return False
        
        return True
    except Exception as e:
        print(f"Error checking session timeout: {e}")
        return False


def get_session_debug_info() -> Dict:
    """
    Get detailed debug information about session state.
    Useful for troubleshooting.
    
    Returns:
        Dict: Comprehensive session debug info
    """
    return {
        "session_state": SESSION_STATE.copy(),
        "status": get_session_status(),
        "timestamp": datetime.now().isoformat(),
    }


# Initialize session on module load
if __name__ == "__main__":
    import json
    print(json.dumps(get_session_status(), indent=2))
