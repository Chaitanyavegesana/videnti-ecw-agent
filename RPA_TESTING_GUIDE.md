# RPA Testing Guide — eCW Bridge PyAutoGUI Automation

## Overview

The Videnti eCW Bridge uses **PyAutoGUI** to automate screen interactions with eClinicalWorks (RPA = Robotic Process Automation). This guide shows you how to test this functionality safely.

---

## ⚠️ Safety First — FAILSAFE Mode

PyAutoGUI has a built-in safety feature:
- **Move your mouse to the TOP-LEFT corner of your screen** to abort any RPA action
- This is critical during testing to prevent unwanted clicks/typing

```python
pyautogui.FAILSAFE = True  # Already enabled in our code
```

---

## Testing Approach: Three Levels

### Level 1: Unit Tests (No Real Screen Interaction)
✅ **Current:** Tests in `tests/test_ecw_bridge.py` use **mocking** to simulate PyAutoGUI without touching your screen.

```bash
# Run unit tests
pytest tests/test_ecw_bridge.py -v
```

**Result:** 
- ✓ `test_pend_order_rejects_invalid_token` — Validates auth
- ✓ `test_pend_order_accepts_valid_token` — Validates order flow
- ✓ `test_save_credentials_writes_env` — Validates credential storage

---

### Level 2: Integration Tests (Safe Screen Interaction)
⚠️ **Pre-requisite:** You must have eCW open and focused

**Setup:**
1. Open eClinicalWorks in a window
2. Navigate to the **Orders** screen or **Patient Lookup**
3. Run the test below

**Test: Simulate clicking a button**

```python
import pyautogui
import time

# Move mouse to known button location (adjust coordinates for your screen)
# Example: "Pend Order" button at (x=500, y=200)

pyautogui.moveTo(500, 200, duration=1)  # Slow movement so you can see it
time.sleep(1)

# If you want to abort, move mouse to TOP-LEFT corner NOW
pyautogui.click()  # Safe click
```

**Running a real integration test:**

```bash
# Start the eCW Bridge server first
python mcp_servers/ecw_bridge/server.py &

# Then test the open_chart tool
python -c "
import asyncio
from mcp_servers.ecw_bridge.server import open_chart

result = asyncio.run(open_chart('MRN-123456'))
print(result)
"
```

---

### Level 3: Full End-to-End Testing (Production Simulation)
🔴 **CAUTION:** Only do this in a test eCW instance or staging environment

**Steps:**

1. **Set up test patient in eCW**
   - MRN: `TEST-001`
   - Name: `Test Patient`
   - Chart: Open and ready

2. **Run the full pipeline**

```bash
# Terminal 1: Start all MCP servers
python mcp_servers/ecw_bridge/server.py &
python mcp_servers/ollama_server/server.py &
python mcp_servers/search_mcp/server.py &

# Terminal 2: Run the application test
python test_application.py

# Terminal 3: Start the dashboard
cd dashboard && npm run dev
```

3. **Monitor the logs**
   - Watch the terminal output for RPA actions
   - Each `pyautogui.write()` or `pyautogui.click()` is logged
   - If something goes wrong, move mouse to TOP-LEFT corner

---

## 🧪 Safe Testing Workflow

### Test Case: Approve a Recommendation (End-to-End)

**File:** `tests/test_rpa_approval_flow.py` (create this)

```python
import pytest
import asyncio
import time
import pyautogui
from mcp_servers.ecw_bridge.server import (
    open_chart, pend_order, approve_recommendation
)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_approve_recommendation_safe():
    """
    Safe end-to-end test of the approval flow.
    Only interacts with mock data until the actual RPA step.
    """
    # Step 1: Approve recommendation (no RPA yet, just logs)
    result = await approve_recommendation("v-9a1b")
    assert result["status"] == "SUCCESS"
    print(f"✓ Approval logged: {result['snapshot_id']}")
    
    # Step 2: When ready to test RPA, use this pattern:
    # result = await pend_order(
    #     cpt_code="95800",
    #     icd_code="G47.33",
    #     patient_mrn="TEST-001",
    #     approval_token="valid-token-12345"
    # )
    # assert result["status"] == "SUCCESS"

# Run with: pytest tests/test_rpa_approval_flow.py -v -m integration
```

---

## 🔍 Debugging PyAutoGUI Issues

### Problem: Clicks aren't working

**Solution:**
1. Get your screen size:
```python
import pyautogui
print(f"Screen size: {pyautogui.size()}")
```

2. Move mouse to known location:
```python
pyautogui.moveTo(100, 100, duration=2)  # Move to top-left with 2-sec animation
```

3. Take a screenshot:
```python
import pyautogui
screenshot = pyautogui.screenshot()
screenshot.save('debug_screenshot.png')
```

4. Check coordinates:
```python
# Get current mouse position
x, y = pyautogui.position()
print(f"Mouse at: {x}, {y}")
```

### Problem: Typing doesn't appear

**Cause:** eCW window isn't focused
**Solution:**
```python
import pyautogui
import time

# Click on the input field first
pyautogui.click(x=400, y=300)
time.sleep(0.5)

# Clear any existing text
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.2)

# Now type
pyautogui.write('MRN-123456', interval=0.1)
```

---

## 📊 Test Coverage Matrix

| Test Level | Tool | Scope | Risk | Requirement |
|-----------|------|-------|------|-------------|
| **Unit** | pytest + monkeypatch | Functions in isolation | ✅ None | Python env only |
| **Integration** | pytest + async | MCP server APIs | ⚠️ Screen focus | eCW window open |
| **E2E** | Manual + logs | Full pipeline | 🔴 Data write | Test instance |

---

## ✅ Checklist: Before Running RPA Tests

- [ ] eClinicalWorks is open and logged in
- [ ] You have a test patient chart ready (MRN: `TEST-001`)
- [ ] Your mouse is ready at TOP-LEFT corner (failsafe abort)
- [ ] All MCP servers are running (`ps aux | grep "mcp_servers"`)
- [ ] You've reviewed the coordinate positions for your screen resolution
- [ ] Logs are being tailed in another terminal (`tail -f logs/*.log`)
- [ ] You have a screenshot saved of the target eCW screen

---

## 🚀 Quick Start: Run All Tests

```bash
# 1. Unit tests (always safe)
pytest tests/ -v

# 2. Integration tests (requires eCW running)
pytest tests/ -v -m integration

# 3. Full application test
python test_application.py

# 4. Monitor logs in real-time
tail -f logs/*.log
```

---

## 📝 Logging RPA Actions

Every PyAutoGUI action is logged:

```python
logger.info(f"Clicking at coordinates: (500, 200)")
logger.info(f"Typing: {patient_mrn}")
logger.info(f"Pressing: enter")
```

Check `/Users/chaitanya/Desktop/videnti-ecw-agent/logs/` for detailed logs.

---

## 🔐 Security Notes

1. **Credentials are NEVER sent over the network**
   - Saved only to local `.env` file
   - Used only by local PyAutoGUI scripts

2. **RPA actions require approval tokens**
   - Token must be ≥10 characters
   - Prevents accidental order placement

3. **Audit trail logs all RPA actions**
   - Timestamp, action type, patient MRN
   - Stored locally in encrypted logs

---

## 💡 Pro Tips

1. **Use slow movements during development:**
   ```python
   pyautogui.moveTo(x, y, duration=2)  # 2-second move (slow for debugging)
   ```

2. **Add strategic pauses:**
   ```python
   time.sleep(1)  # Give eCW time to load data
   ```

3. **Log mouse position for future use:**
   ```python
   x, y = pyautogui.position()
   logger.info(f"Mouse at: {x}, {y}")  # Save this for button coordinates
   ```

4. **Test in headless mode** (no screen):
   ```python
   # Use mocking instead of real PyAutoGUI
   pytest tests/test_ecw_bridge.py -v  # Already does this!
   ```

---

## 🆘 Still Having Issues?

1. **Check if eCW window is focused:**
   ```bash
   # macOS: Check active window
   osascript -e 'tell app "System Events" to name of first application process whose frontmost is true'
   ```

2. **Verify coordinates:**
   - Open `logs/screenshots/` for captured screenshots
   - Use Python's `pyautogui.locateOnScreen()` for image-based clicking

3. **Review test logs:**
   ```bash
   grep "PYAUTOGUI\|ECW-BRIDGE" logs/*.log
   ```

---

**Happy RPA Testing! ��**
