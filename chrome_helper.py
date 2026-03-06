#!/usr/bin/env python3
"""
Chrome Helper Module

Detects and manages Chrome browser state without programmatic launches.
Uses AppleScript on macOS to interact with running Chrome instance.
"""

import subprocess
import json
import re
from typing import Optional, Dict, List


def is_chrome_running() -> bool:
    """
    Check if Chrome process is currently running.
    
    Returns:
        bool: True if Chrome is running, False otherwise
    """
    try:
        result = subprocess.run(
            ["pgrep", "-x", "Google Chrome"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking Chrome process: {e}")
        return False


def find_ecw_tab() -> Optional[int]:
    """
    Find the tab ID running eCW application.
    
    Returns:
        Optional[int]: Tab ID if found, None otherwise
    """
    if not is_chrome_running():
        return None
    
    try:
        script = """
        tell application "Google Chrome"
            repeat with w in (windows)
                repeat with t in (tabs of w)
                    if (URL of t contains "eclinicalworks") or (URL of t contains "ecw") then
                        return id of t
                    end if
                end repeat
            end repeat
            return "none"
        end tell
        """
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        tab_id = result.stdout.strip()
        if tab_id and tab_id != "none":
            try:
                return int(tab_id)
            except ValueError:
                return None
        return None
    except Exception as e:
        print(f"Error finding eCW tab: {e}")
        return None


def activate_ecw_tab() -> bool:
    """
    Bring the eCW tab to foreground (non-blocking).
    
    Returns:
        bool: True if successful, False otherwise
    """
    tab_id = find_ecw_tab()
    if not tab_id:
        return False
    
    try:
        script = f"""
        tell application "Google Chrome"
            activate
            repeat with w in (windows)
                repeat with t in (tabs of w)
                    if id of t = {tab_id} then
                        set active tab index of w to (index of t)
                        return true
                    end if
                end repeat
            end repeat
            return false
        end tell
        """
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return "true" in result.stdout.lower()
    except Exception as e:
        print(f"Error activating eCW tab: {e}")
        return False


def get_active_tab_url() -> Optional[str]:
    """
    Get the URL of the currently active tab.
    
    Returns:
        Optional[str]: URL if available, None otherwise
    """
    if not is_chrome_running():
        return None
    
    try:
        script = """
        tell application "Google Chrome"
            return URL of active tab of front window
        end tell
        """
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        url = result.stdout.strip()
        return url if url else None
    except Exception as e:
        print(f"Error getting active tab URL: {e}")
        return None


def is_on_ecw_page() -> bool:
    """
    Check if currently on eCW page.
    
    Returns:
        bool: True if on eCW domain, False otherwise
    """
    url = get_active_tab_url()
    if not url:
        return False
    
    ecw_domains = [
        "eclinicalworks.com",
        "eclinicalworks",
        "ecw.",
        ".ecw"
    ]
    
    return any(domain in url.lower() for domain in ecw_domains)


def get_page_title() -> Optional[str]:
    """
    Get the title of the active page.
    
    Returns:
        Optional[str]: Page title if available, None otherwise
    """
    if not is_chrome_running():
        return None
    
    try:
        script = """
        tell application "Google Chrome"
            return title of active tab of front window
        end tell
        """
        
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        title = result.stdout.strip()
        return title if title else None
    except Exception as e:
        print(f"Error getting page title: {e}")
        return None


def is_on_login_page() -> bool:
    """
    Check if currently on login page (including Cloudflare CAPTCHA).
    
    Returns:
        bool: True if on login-related page, False otherwise
    """
    title = get_page_title()
    url = get_active_tab_url()
    
    if not title or not url:
        return False
    
    # Indicators of being on login page
    login_indicators = [
        "login" in title.lower(),
        "sign in" in title.lower(),
        "cloudflare" in title.lower(),
        "verify" in title.lower(),
        "/login" in url.lower(),
        "/auth" in url.lower(),
        "challenge" in title.lower(),
    ]
    
    return any(login_indicators)


def get_chrome_state() -> Dict:
    """
    Get comprehensive Chrome and eCW state.
    
    Returns:
        Dict: State information including:
            - chrome_running: bool
            - ecw_tab_found: bool
            - on_ecw_page: bool
            - on_login_page: bool
            - current_url: Optional[str]
            - page_title: Optional[str]
    """
    chrome_running = is_chrome_running()
    
    return {
        "chrome_running": chrome_running,
        "ecw_tab_found": bool(find_ecw_tab()) if chrome_running else False,
        "on_ecw_page": is_on_ecw_page() if chrome_running else False,
        "on_login_page": is_on_login_page() if chrome_running else False,
        "current_url": get_active_tab_url() if chrome_running else None,
        "page_title": get_page_title() if chrome_running else None,
    }


if __name__ == "__main__":
    # Test the Chrome helper
    state = get_chrome_state()
    print(json.dumps(state, indent=2))
