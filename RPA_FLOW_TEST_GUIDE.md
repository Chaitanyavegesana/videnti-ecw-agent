# RPA Flow Test Guide: Complete Step-by-Step

**What You'll See:** A real demonstration of PyAutoGUI automation

---

## 🎯 Quick Start (5 minutes)

```bash
cd /Users/chaitanya/Desktop/videnti-ecw-agent
.venv/bin/python test_rpa_flow_demo.py
```

---

## 📊 The Complete RPA Flow (Visual)

```
┌─────────────────────────────────────────────────────────────────┐
│                     RPA FLOW - 5 PHASES                          │
└─────────────────────────────────────────────────────────────────┘

PHASE 1: NAVIGATE
═══════════════════════════════════════════════════════════════════
   You open a browser
   ↓
   Script guides you to: https://practicetestautomation.com/...
   ↓
   You see a login form with:
   ✓ Username field
   ✓ Password field
   ✓ Login button

PHASE 2: IDENTIFY ELEMENT LOCATIONS
═══════════════════════════════════════════════════════════════════
   Script: "Move your mouse to USERNAME field, then press ENTER"
   ↓
   You position mouse over username field
   ↓
   Press ENTER → Script captures: (x=245, y=312)
   ↓
   Repeat for password field → (x=245, y=401)
   ↓
   Repeat for login button → (x=300, y=450)

PHASE 3: EXTRACT & ENTER DATA (AUTOMATED)
═══════════════════════════════════════════════════════════════════
   Script extracts:
   ├─ username: "student"
   ├─ password: "Password123"
   └─ (In real eCW, would extract: CPT 95800, ICD G47.33)
   ↓
   Script AUTOMATICALLY:
   ├─ Click username field at (245, 312)
   ├─ Type: "student"
   ├─ Click password field at (245, 401)
   ├─ Type: "Password123"
   └─ Wait 3 seconds (FAILSAFE: move mouse to top-left to abort)

PHASE 4: SUBMIT FORM (AUTOMATED)
═══════════════════════════════════════════════════════════════════
   Script AUTOMATICALLY:
   ├─ Click login button at (300, 450)
   ├─ Wait 2 seconds for page to load
   └─ Log: "Form submitted"

PHASE 5: VERIFY RESULTS
═══════════════════════════════════════════════════════════════════
   You check the browser:
   ✓ See "Congratulations student" message
   ✓ Form was submitted successfully
   ✓ (In eCW: Order would now be "PENDING")
   ↓
   Press ENTER to confirm
   ↓
   ✅ TEST COMPLETE
```

---

## 🚀 How This Maps to eCW RPA Flow

```
PRACTICE SITE                    →    REAL eCW WORKFLOW
═══════════════════════════════════════════════════════════════════

Username field                   →    Patient MRN lookup
Password field                   →    (authentication)
Login button                     →    Open chart button

Extract: "student"               →    Extract: Patient name
Extract: "Password123"           →    Extract: Patient data
                                      (Age, BMI, Vitals, PMH)

Enter into form fields           →    Enter CPT code
Enter into form fields           →    Enter ICD-10 code

Click Login button               →    Click "Pend Order" button

See success message              →    See order marked "PENDING"
                                      in eCW dashboard
```

---

## 📝 What's Actually Happening

### **Before Test Runs:**
```
You have coordinates:
  ❌ Username field location: UNKNOWN
  ❌ Password field location: UNKNOWN
  ❌ Button location: UNKNOWN
```

### **During Phase 2 (Identification):**
```
You move mouse to each element:
  ✓ Username field: (245, 312) ← Script captures this
  ✓ Password field: (245, 401) ← Script captures this
  ✓ Button: (300, 450)          ← Script captures this
```

### **During Phase 3 (Data Entry):**
```
Script uses captured coordinates to automate:
  1. pyautogui.click(245, 312)        # Click username
  2. pyautogui.write("student")        # Type username
  3. pyautogui.click(245, 401)        # Click password
  4. pyautogui.write("Password123")    # Type password
  5. [SAFETY WAIT 3 SECONDS]
```

### **During Phase 4 (Submit):**
```
Script uses captured coordinates to automate:
  1. pyautogui.click(300, 450)        # Click login button
  2. Wait for server response
```

---

## 🔒 Safety Features You'll See

### **FAILSAFE (Top-Left Corner Abort)**
```
Before clicking the login button, you see:

  ⚠️  SAFETY CHECK:
  Move your mouse to TOP-LEFT corner NOW to abort.
  Otherwise, we'll click the login button in 3 seconds...
  
  3... 2... 1... ✓

If you move your mouse to top-left corner during countdown:
  ✅ PyAutoGUI detects this and STOPS immediately
  ✅ No further automation occurs
  ✅ You're always in control
```

### **Logging**
```
All actions logged:
  [RPA-TEST] INFO: Clicking username field...
  [RPA-TEST] INFO: Entering username: student
  [RPA-TEST] INFO: Clicking password field...
  [RPA-TEST] INFO: Entering password: Password123
  [RPA-TEST] INFO: Clicking login button...
  [RPA-TEST] INFO: Form submitted. Waiting for response...
```

---

## 🎮 Step-by-Step Walkthrough

### **Step 1: Start the Test**
```bash
.venv/bin/python test_rpa_flow_demo.py
```

You'll see:
```
╔════════════════════════════════════════════════════════════════╗
║                   RPA TESTING - GETTING STARTED                ║
║                                                                ║
║  Prerequisites:                                                ║
║  1. Have a browser open (Chrome or Firefox)                    ║
║  2. Navigate to the practice site (instructions will show URL) ║
║  3. Keep mouse ready near top-left corner                      ║
║  4. Have 5-10 minutes for the complete flow                    ║
║                                                                ║
║  Ready to start? Press ENTER...                                ║
╚════════════════════════════════════════════════════════════════╝
```

Press ENTER to continue.

---

### **Step 2: Open the Practice Website**
```
🔵 MANUAL STEP:
1. Open Chrome/Firefox browser
2. Go to: https://practicetestautomation.com/practice-test-login/
3. You should see a login form with:
   - Username field
   - Password field
   - Login button

Press ENTER when the page is fully loaded...
```

Do exactly this:
1. Open your browser
2. Copy-paste the URL into address bar
3. Wait for page to load
4. Press ENTER in terminal

---

### **Step 3: Identify Form Element Locations**
```
🔍 INSPECTION PHASE:

📍 Step 1: Move mouse to USERNAME field, then press ENTER
```

Do this:
1. Slowly move your mouse to the username input field
2. Position it in the middle of the field
3. Press ENTER in terminal
4. Script captures the coordinates

You'll see:
```
✓ Captured username field location: (245, 312)
```

Repeat for password field and button.

---

### **Step 4: Automated Data Entry**
```
📋 DATA EXTRACTED FROM FORM:
┌─────────────────────────────────────┐
│ Username: student                   │
│ Password: Password123               │
│                                      │
│ If this were eCW:                   │
│ Patient MRN: MRN-123456             │
│ Test Type: Home Sleep Test          │
│ CPT Code: 95800                     │
│ ICD Code: G47.33                    │
└─────────────────────────────────────┘

🤖 STARTING RPA AUTOMATION...
  ✓ Entered username: student
  ✓ Entered password: Password123

  ⚠️  SAFETY CHECK:
  Move your mouse to TOP-LEFT corner NOW to abort.
  Otherwise, we'll click the login button in 3 seconds...
  
  3... 2... 1... ✓
```

Watch your browser - you'll see the username and password being typed automatically!

---

### **Step 5: Form Submission**
```
🖱️  CLICKING LOGIN BUTTON...

This simulates the RPA clicking the "Pend Order" button in eCW.
  ✓ Button clicked!
  ✓ Form submitted. Waiting for server response...
```

Watch your browser - you'll see the login button being clicked automatically!

---

### **Step 6: Verify Results**
```
✅ VERIFICATION PHASE:

Check your browser screen:
✓ You should see "Congratulations student" or success message
✓ This means the form was submitted successfully
✓ In eCW, this would mean the order is now "PENDING"

Did the form submit successfully?
Press ENTER to continue...
```

Check your browser. You should see the login page change to a success page.

Press ENTER to complete the test.

---

### **Step 7: Test Complete**
```
╔════════════════════════════════════════════════════════════════╗
║                    ✅ TEST COMPLETED SUCCESSFULLY              ║
║                                                                ║
║  You've successfully demonstrated:                             ║
║  ✓ Navigating to a website                                    ║
║  ✓ Identifying form element locations                         ║
║  ✓ Extracting and entering data via RPA                       ║
║  ✓ Clicking buttons and submitting forms                      ║
║  ✓ Verifying results on the page                              ║
║                                                                ║
║  In the eCW workflow, this same flow would:                   ║
║  1. Connect to eCW and get patient schedule                   ║
║  2. Identify the chart fields locations                       ║
║  3. Extract patient data from the chart                       ║
║  4. Enter diagnostic codes (CPT/ICD)                          ║
║  5. Click "Pend Order" button                                 ║
║  6. Verify order appears as PENDING                           ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🎓 What You've Learned

By running this test, you've seen:

1. **Element Location** 
   - How to identify coordinates of buttons/fields
   - How `pyautogui.position()` captures location

2. **Data Extraction**
   - How clinical data would be extracted from eCW
   - How it would be organized for entry

3. **Automated Data Entry**
   - How `pyautogui.click()` moves to coordinates
   - How `pyautogui.write()` types data
   - How timing is controlled with `time.sleep()`

4. **Form Submission**
   - How buttons are clicked automatically
   - How to wait for responses

5. **Safety & Control**
   - How FAILSAFE prevents unintended actions
   - How to abort at any time (top-left corner)
   - How logging tracks all actions

---

## 🔗 Real eCW Workflow (What's Different)

In the actual eCW implementation:

```
PRACTICE TEST                          REAL eCW
═══════════════════════════════════════════════════════════════════
1. Navigate to public website          1. Connect to eCW via credentials
                                          (from .env file)

2. Identify form field locations       2. Identify chart field locations
   (username, password)                   (vitals panel, PMH section, etc.)

3. Extract data from script            3. Extract data from patient chart
   (hard-coded for demo)                  (via chart access)

4. Type extracted data                 4. Type diagnostic codes
   into form                              into order entry form

5. Click login button                  5. Click "Pend Order" button

6. Verify login success                6. Verify order marked "PENDING"

7. Done!                               7. Provider signs off → Complete
```

---

## 📚 Files Reference

| File | What It Does |
|------|--------------|
| `test_rpa_flow_demo.py` | Complete RPA demo with 5 phases |
| `mcp_servers/ecw_bridge/server.py` | Real eCW implementation using same techniques |
| `tests/test_ecw_bridge.py` | 15 unit tests for RPA functions |

---

## 🚀 What's Next After This Test?

### **Option 1: Test Real eCW** 
Apply same technique to actual eCW instance:
1. Screenshot your eCW login page
2. Identify field locations on YOUR screen
3. Test with real eCW credentials

### **Option 2: Test Full Pipeline**
Run the complete Videnti system:
```bash
# Start all servers
.venv/bin/python mcp_servers/ecw_bridge/server.py &
.venv/bin/python mcp_servers/ollama_server/server.py &
.venv/bin/python mcp_servers/search_mcp/server.py &

# Run orchestrator
VIDENTI_TEST_RUN=1 .venv/bin/python main.py
```

### **Option 3: Advanced RPA**
Use image recognition instead of coordinates:
```python
# Instead of hardcoded (245, 312):
location = pyautogui.locateOnScreen('username_field.png')
if location:
    pyautogui.click(location)
```

---

## ✅ Success Criteria

You'll know the test worked if:

- ✓ Username gets typed into field automatically
- ✓ Password gets typed into field automatically
- ✓ Login button gets clicked automatically
- ✓ Browser shows success page
- ✓ You see log messages for each action

---

**Ready to see PyAutoGUI in action? Run it now:**

```bash
.venv/bin/python test_rpa_flow_demo.py
```

