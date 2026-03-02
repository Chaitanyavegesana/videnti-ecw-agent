"""
RPA DEMO: Visual Guide to PyAutoGUI Automation
===============================================

This demonstrates the complete RPA flow with visual examples.
Shows how the Videnti system automates eCW chart interactions.
"""

import pyautogui
import time

# ─────────────────────────────────────────────────────────────────

def demo_1_what_is_rpa():
    """Show what RPA is and why we use it"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                     DEMO 1: WHAT IS RPA?                       ║
    ╚════════════════════════════════════════════════════════════════╝
    
    RPA = Robotic Process Automation
    
    Instead of manually clicking and typing in eCW:
    ┌──────────────────────────────────────────────────────┐
    │ Manual (Slow, Error-prone):                          │
    │ 1. Doctor opens eCW manually                         │
    │ 2. Doctor searches for patient MRN                   │
    │ 3. Doctor clicks "Open Chart"                        │
    │ 4. Doctor reads patient data                         │
    │ 5. Doctor manually enters CPT code                   │
    │ 6. Doctor manually enters ICD code                   │
    │ 7. Doctor clicks "Pend Order"                        │
    │ ❌ Takes 5-10 minutes per patient                    │
    │ ❌ Repetitive and error-prone                        │
    └──────────────────────────────────────────────────────┘
    
    RPA does it automatically:
    ┌──────────────────────────────────────────────────────┐
    │ Automated (Fast, Reliable):                          │
    │ 1. Script opens eCW automatically                    │
    │ 2. Script searches for MRN automatically             │
    │ 3. Script clicks "Open Chart" automatically          │
    │ 4. Script extracts patient data automatically        │
    │ 5. Script enters CPT code automatically              │
    │ 6. Script enters ICD code automatically              │
    │ 7. Script clicks "Pend Order" automatically          │
    │ ✅ Takes ~20 seconds per patient                     │
    │ ✅ Consistent and reliable                           │
    └──────────────────────────────────────────────────────┘
    
    How does it work?
    ────────────────────────────────────────────────────────
    PyAutoGUI allows Python to control the mouse and keyboard:
    
    • pyautogui.click(x, y)        → Clicks at coordinates
    • pyautogui.write("text")       → Types text
    • pyautogui.press("enter")      → Presses keys
    • pyautogui.position()          → Gets current mouse position
    • pyautogui.locateOnScreen()    → Finds image on screen
    
    All actions logged and auditable for compliance ✓
    """)

# ─────────────────────────────────────────────────────────────────

def demo_2_how_it_works():
    """Show the step-by-step flow"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║            DEMO 2: HOW THE RPA FLOW WORKS                      ║
    ╚════════════════════════════════════════════════════════════════╝
    
    STEP-BY-STEP PROCESS:
    
    PHASE 1: IDENTIFY COORDINATES
    ════════════════════════════════════════════════════════════════
    
    Manual calibration (done once):
    
    Step 1a: You open eCW and take a screenshot
    Step 1b: You move mouse to the "MRN Search" field
    Step 1c: You note the coordinates: (x=245, y=150)
    
    Step 2a: You move mouse to the "Patient Name" field  
    Step 2b: You note the coordinates: (x=400, y=200)
    
    Step 3a: You move mouse to the "Open Chart" button
    Step 3b: You note the coordinates: (x=500, y=450)
    
    These coordinates are saved and reused.
    
    
    PHASE 2: AUTOMATED INTERACTIONS
    ════════════════════════════════════════════════════════════════
    
    When the script runs:
    
    📍 ACTION 1: CLICK MRN SEARCH FIELD
    ─────────────────────────────────────
    Code:
        pyautogui.click(245, 150)
    
    What happens on your screen:
        🖱️  Cursor moves to (245, 150)
        🖱️  Mouse clicks at that location
        ✓ MRN field is now focused (cursor is in the field)
    
    
    📍 ACTION 2: TYPE THE MRN
    ─────────────────────────────────────
    Code:
        pyautogui.write("MRN-123456", interval=0.05)
    
    What happens on your screen:
        ⌨️  "M" appears in the field
        ⌨️  "R" appears in the field
        ⌨️  "N" appears in the field
        ⌨️  "-" appears in the field
        ...
        ⌨️  Field now shows: "MRN-123456"
        ✓ You can see it being typed in real-time!
    
    
    📍 ACTION 3: PRESS ENTER
    ─────────────────────────────────────
    Code:
        pyautogui.press('enter')
    
    What happens on your screen:
        ⏎ Enter key is pressed
        📄 Page loads patient data
        ✓ Chart is now visible
    
    
    📍 ACTION 4: CLICK OPEN CHART BUTTON
    ─────────────────────────────────────
    Code:
        pyautogui.click(500, 450)
    
    What happens on your screen:
        🖱️  Cursor moves to (500, 450)
        🖱️  Button is clicked
        📄 Full patient chart opens
        ✓ You can see all patient data
    
    
    PHASE 3: EXTRACT DATA
    ════════════════════════════════════════════════════════════════
    
    Now with chart open, script reads what's on screen:
    
    Code:
        # In real scenario, would use OCR or coordinate-based parsing
        patient_data = {
            "age": 50,
            "bmi": 30.8,
            "vitals": {"bp": "138/88", "hr": 72},
            "symptoms": ["fatigue", "snoring"],
            "conditions": ["hypertension", "diabetes"]
        }
    
    What we extract:
        ✓ Demographics (Age, Sex, DOB)
        ✓ Vital Signs (Height, Weight, BMI, BP, HR)
        ✓ Chief Complaint
        ✓ History of Present Illness
        ✓ Past Medical History
        ✓ Current Medications
        ✓ Allergies
        ✓ Recent Labs
    
    
    PHASE 4: SEND TO AI FOR ANALYSIS
    ════════════════════════════════════════════════════════════════
    
    Extracted data goes to Ollama LLM (local, on-premise):
    
    Input:
        Raw patient data with sensitive info
        (Name, SSN, Address, etc.)
    
    Ollama processes:
        ✓ Strips PHI (names, addresses, IDs)
        ✓ Keeps clinical data
        ✓ Generates unique snapshot_id
    
    Output:
        De-identified data ready for analysis
        {
            "snapshot_id": "v-9a1b-2026-02-28",
            "age": 50,
            "bmi": 30.8,
            "symptoms": ["fatigue", "snoring"],
            "conditions": ["hypertension", "diabetes"],
            "recommendation": "Home Sleep Test (94% confidence)"
        }
    
    
    PHASE 5: DISPLAY IN DASHBOARD & WAIT FOR APPROVAL
    ════════════════════════════════════════════════════════════════
    
    Dashboard shows:
        ┌─────────────────────────────────────┐
        │ Patient MRN: MRN-123456             │
        │ Recommended Test: Home Sleep Test   │
        │ AI Confidence: 94%                  │
        │ Reason: BMI 30.8 + snoring + HTN   │
        │                                     │
        │ [APPROVE]  [DISMISS]               │
        └─────────────────────────────────────┘
    
    Doctor sees recommendation and clicks [APPROVE]
    
    
    PHASE 6: AUTOMATED ORDER PLACEMENT
    ════════════════════════════════════════════════════════════════
    
    Script re-opens chart and enters diagnostic codes:
    
    Step 1: Click "New Order" button
        pyautogui.click(300, 100)
        ✓ Order entry screen opens
    
    Step 2: Type CPT code
        pyautogui.write("95800", interval=0.05)
        ✓ CPT code appears in field (CPT 95800 = Home Sleep Test)
    
    Step 3: Type ICD-10 diagnosis code
        pyautogui.write("G47.33", interval=0.05)
        ✓ ICD code appears in field (G47.33 = Sleep Apnea)
    
    Step 4: Click "Pend Order" button
        pyautogui.click(400, 400)
        ✓ Order is pended
        ✓ Provider sees it for signature
    
    
    PHASE 7: VERIFICATION
    ════════════════════════════════════════════════════════════════
    
    System verifies order was placed:
    
    ✓ Check order appears in patient chart
    ✓ Log action to audit trail
    ✓ Send notification to provider
    ✓ Mark recommendation as "COMPLETED"
    
    Everything is logged and auditable!
    """)

# ─────────────────────────────────────────────────────────────────

def demo_3_real_code_examples():
    """Show actual PyAutoGUI code"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║        DEMO 3: REAL PYAUTOGUI CODE EXAMPLES                    ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Here are the actual Python commands used in Videnti:
    
    
    EXAMPLE 1: OPENING A PATIENT CHART
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    import time
    
    # Step 1: Click on the MRN search field (coordinates from calibration)
    pyautogui.click(245, 150)
    time.sleep(0.5)  # Wait for field to be ready
    
    # Step 2: Type the patient MRN
    patient_mrn = "MRN-123456"
    pyautogui.write(patient_mrn, interval=0.05)  # 0.05s between keystrokes
    
    # Step 3: Press Enter to search
    pyautogui.press('enter')
    time.sleep(2)  # Wait for results to load
    
    # Step 4: Click "Open Chart" button
    pyautogui.click(500, 450)
    time.sleep(2)  # Wait for chart to fully load
    
    # Result: Patient chart is now open on screen! ✓
    
    
    EXAMPLE 2: ENTERING DIAGNOSTIC CODES
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    import time
    
    # Step 1: Click "New Order" button
    pyautogui.click(300, 100)
    time.sleep(1)
    
    # Step 2: Click CPT code field and enter code
    pyautogui.click(400, 200)
    time.sleep(0.5)
    pyautogui.write("95800", interval=0.05)  # Home Sleep Test CPT
    time.sleep(0.5)
    pyautogui.press('tab')  # Move to next field
    
    # Step 3: Click ICD-10 field and enter code
    pyautogui.click(400, 250)
    time.sleep(0.5)
    pyautogui.write("G47.33", interval=0.05)  # Sleep Apnea ICD-10
    time.sleep(0.5)
    
    # Step 4: Click "Pend Order" button
    pyautogui.click(400, 400)
    time.sleep(2)  # Wait for order to be pended
    
    # Result: Order is now PENDING in eCW! ✓
    
    
    EXAMPLE 3: GETTING CURRENT MOUSE POSITION
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    
    # Get where your mouse currently is
    x, y = pyautogui.position()
    print(f"Mouse is at: ({x}, {y})")
    
    # Output might be:
    # Mouse is at: (1024, 768)
    
    # Use this to calibrate and find button coordinates!
    
    
    EXAMPLE 4: SAFETY FAILSAFE
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    
    # Enable failsafe - move mouse to corner to abort
    pyautogui.FAILSAFE = True
    
    # If you move mouse to TOP-LEFT corner (0, 0) during execution,
    # PyAutoGUI will immediately stop and raise an exception.
    # This prevents accidental clicks or typing!
    
    # Also add logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("About to click order button at (400, 400)")
    pyautogui.click(400, 400)
    logger.info("Order button clicked successfully")
    
    
    EXAMPLE 5: COMPLETE WORKFLOW
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    import time
    
    def automate_order_placement(patient_mrn, cpt_code, icd_code):
        '''Complete automation: Open chart → Extract → Enter codes → Pend order'''
        
        # STEP 1: Open chart
        pyautogui.click(245, 150)  # Click MRN field
        time.sleep(0.5)
        pyautogui.write(patient_mrn, interval=0.05)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.click(500, 450)  # Click "Open Chart"
        time.sleep(2)
        
        # STEP 2: Navigate to orders
        pyautogui.click(300, 100)  # Click "New Order"
        time.sleep(1)
        
        # STEP 3: Enter diagnostic codes
        pyautogui.click(400, 200)  # Click CPT field
        time.sleep(0.5)
        pyautogui.write(cpt_code, interval=0.05)
        pyautogui.press('tab')
        
        pyautogui.click(400, 250)  # Click ICD field
        time.sleep(0.5)
        pyautogui.write(icd_code, interval=0.05)
        
        # STEP 4: Pend order
        pyautogui.click(400, 400)  # Click "Pend Order"
        time.sleep(2)
        
        return True
    
    # Usage:
    success = automate_order_placement("MRN-123456", "95800", "G47.33")
    
    if success:
        print("✅ Order pended successfully!")
    
    """)

# ─────────────────────────────────────────────────────────────────

def demo_4_what_you_see():
    """Show what happens on screen"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║        DEMO 4: WHAT YOU SEE ON SCREEN (Real-Time)              ║
    ╚════════════════════════════════════════════════════════════════╝
    
    When RPA is running, here's what you observe:
    
    
    TIMELINE OF EVENTS:
    ════════════════════════════════════════════════════════════════
    
    T=0 seconds:  eCW window is open with login page visible
    
    T=1 second:   Mouse cursor moves to MRN search field
                  ─────────────────────────────────────
                  You see: cursor smoothly move to field location
    
    T=1.5 sec:    MRN search field is clicked (focused)
                  ─────────────────────────────────────
                  You see: field highlights, cursor blinking inside
    
    T=2 sec:      Script types "MRN-123456" character by character
                  ─────────────────────────────────────
                  You see:
                  M       (field shows: "M")
                  MR      (field shows: "MR")
                  MRN     (field shows: "MRN")
                  MRN-    (field shows: "MRN-")
                  MRN-1   (field shows: "MRN-1")
                  ...
                  MRN-123456 (field shows: "MRN-123456")
                  ✓ You can watch it being typed in real-time!
    
    T=3 sec:      Enter key is pressed
                  ─────────────────────────────────────
                  You see: Page starts loading (spinner appears)
    
    T=5 sec:      Patient data appears on screen
                  ─────────────────────────────────────
                  You see:
                  - Patient name
                  - Age, DOB
                  - Vital signs
                  - Recent labs
                  - Medical history
    
    T=5.5 sec:    "Open Chart" button is clicked
                  ─────────────────────────────────────
                  You see: Mouse moves to button and clicks
    
    T=7.5 sec:    Full patient chart is now visible
                  ─────────────────────────────────────
                  You see: Complete patient information displayed
    
    [If approving order:]
    
    T=8 sec:      Script clicks "New Order" button
                  ─────────────────────────────────────
                  You see: Order entry form opens
    
    T=9 sec:      Script types "95800" (CPT code)
                  ─────────────────────────────────────
                  You see: CPT field fills with "95800"
    
    T=9.5 sec:    Script types "G47.33" (ICD-10 code)
                  ─────────────────────────────────────
                  You see: ICD field fills with "G47.33"
    
    T=10 sec:     Script clicks "Pend Order" button
                  ─────────────────────────────────────
                  You see: Button highlights, order processes
    
    T=12 sec:     ✅ SUCCESS MESSAGE appears
                  ─────────────────────────────────────
                  You see: "Order Pended Successfully"
                  Order is now in provider's queue!
    
    
    VISUAL REPRESENTATION:
    ════════════════════════════════════════════════════════════════
    
    Your eCW screen during RPA automation:
    
    BEFORE:                          DURING:                 AFTER:
    ┌────────────────┐              ┌────────────────┐     ┌────────────────┐
    │ eCW Login      │              │ Patient Search │     │ Full Chart     │
    │                │    T=0-5s    │ MRN-123456     │     │ ─────────────  │
    │ [Login Form]   │   ─────────> │ [LOADING...]   │────>│ • Name: John   │
    │                │              │                │     │ • Age: 50      │
    └────────────────┘              └────────────────┘     │ • BMI: 30.8    │
                                                            │ • BP: 138/88   │
                                                            │                │
                                                            │ [New Order]    │
                                                            │ CPT: 95800     │
                                                            │ ICD: G47.33    │
                                                            │ [Pend Order]   │
                                                            └────────────────┘
    
    All done in ~12 seconds!
    Doctor would need 5-10 minutes to do manually.
    
    
    KEY OBSERVATIONS:
    ════════════════════════════════════════════════════════════════
    
    ✓ Typing is slow enough to see it happen
    ✓ Mouse movements are smooth and visible
    ✓ Page loads are respected (pauses between actions)
    ✓ Every action is logged to console/file
    ✓ If something goes wrong, you can abort with failsafe
    ✓ The whole process is deterministic and repeatable
    
    """)

# ─────────────────────────────────────────────────────────────────

def demo_5_coordin_calibration():
    """Show how to find coordinates"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         DEMO 5: COORDINATE CALIBRATION (Finding Buttons)       ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Before RPA can work, we need to find the coordinates (x, y)
    of every button and field we want to click.
    
    This is done ONE TIME during setup.
    
    
    METHOD 1: MANUAL POSITION TRACKING
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    
    # Move your mouse to a button slowly and carefully
    # As you move, Python tells you your coordinates in real-time:
    
    while True:
        x, y = pyautogui.position()
        print(f"Mouse position: ({x}, {y})", end='\\r')
    
    
    OUTPUT:
    Mouse position: (100, 50)
    Mouse position: (150, 100)
    Mouse position: (200, 150)
    Mouse position: (245, 150)  <-- This is the MRN field!
    Mouse position: (250, 150)
    Mouse position: (245, 150)  <-- Back to field
    
    Save: MRN_FIELD = (245, 150)
    
    
    METHOD 2: SCREENSHOT + ANALYSIS
    ════════════════════════════════════════════════════════════════
    
    import pyautogui
    
    # Take a screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save('ecw_screen.png')
    
    # Open 'ecw_screen.png' in image editor
    # Hover over button, note the coordinates from image editor
    # Those are your PyAutoGUI coordinates!
    
    
    METHOD 3: INTERACTIVE CALIBRATION
    ════════════════════════════════════════════════════════════════
    
    Step 1: Open eCW in your browser/app
    Step 2: Run this Python code:
    
        import pyautogui
        import time
        
        coords = {}
        
        print("Move mouse to MRN field and press ENTER")
        input()
        x, y = pyautogui.position()
        coords['mrn_field'] = (x, y)
        print(f"✓ Saved MRN field at ({x}, {y})")
        
        print("Move mouse to Open Chart button and press ENTER")
        input()
        x, y = pyautogui.position()
        coords['open_chart'] = (x, y)
        print(f"✓ Saved Open Chart button at ({x}, {y})")
        
        print("Move mouse to New Order button and press ENTER")
        input()
        x, y = pyautogui.position()
        coords['new_order'] = (x, y)
        print(f"✓ Saved New Order button at ({x}, {y})")
        
        # Save coordinates
        import json
        with open('coordinates.json', 'w') as f:
            json.dump(coords, f)
        
        print("✅ Coordinates saved to coordinates.json")
    
    Step 3: Coordinates are now saved and can be reused!
    
    
    EXAMPLE COORDINATE MAP:
    ════════════════════════════════════════════════════════════════
    
    For a standard eCW instance with 1920x1080 resolution:
    
    ELEMENT                    COORDINATES
    ─────────────────────────────────────────
    MRN Search Field           (245, 150)
    Search Button              (350, 150)
    Open Chart Button          (500, 450)
    New Order Button           (300, 100)
    CPT Code Field             (400, 200)
    ICD-10 Code Field          (400, 250)
    Pend Order Button          (400, 400)
    Save Order Button          (500, 400)
    Close Button               (600, 50)
    
    Each screen resolution needs its own coordinate map!
    
    
    IMPORTANT NOTES:
    ════════════════════════════════════════════════════════════════
    
    ⚠️  Coordinates are SCREEN-DEPENDENT
        - 1920x1080 screen: different coordinates than 1280x720
        - Different zoom levels: different coordinates
        - Different eCW versions: might have different layout
    
    ✓ Calibration is ONE-TIME
        - Once you find coordinates, they don't change
        - Unless eCW updates or you change screens
    
    ✓ Slight inaccuracy is okay
        - If you click (245, 150) but button is at (248, 152)
        - The click will still register
        - PyAutoGUI is forgiving with ~5-10px accuracy
    
    """)

# ─────────────────────────────────────────────────────────────────

def main():
    """Run all demos"""
    demos = [
        ("1. What is RPA?", demo_1_what_is_rpa),
        ("2. How does it work?", demo_2_how_it_works),
        ("3. Real code examples", demo_3_real_code_examples),
        ("4. What you see on screen", demo_4_what_you_see),
        ("5. Coordinate calibration", demo_5_coordin_calibration),
    ]
    
    while True:
        print("\n" + "="*70)
        print("RPA DEMO - Choose which demo to watch:")
        print("="*70)
        
        for i, (name, _) in enumerate(demos, 1):
            print(f"{i}. {name}")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "0":
            print("\n✅ Thanks for watching the RPA demo!")
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(demos):
                print("\n")
                demos[idx][1]()
                print("\n" + "-"*70)
                input("Press ENTER to continue...")
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
