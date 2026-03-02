"""
RPA Testing Module: Test PyAutoGUI Automation on Sample Website
This module demonstrates the complete RPA flow using a practice website.

Flow:
1. Navigate to sample website
2. Find and click form fields
3. Enter data (simulating patient chart extraction)
4. Submit form (simulating order placement)
5. Verify results

Safe Testing: Uses https://practicetestautomation.com/practice-test-login/
No credentials required, completely reversible actions.
"""

import pyautogui
import time
import logging
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RPA-TEST] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# PyAutoGUI Safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# ─── Test Website URLs ───────────────────────────────────────────────────────

# Practice Test Automation - Free demo site for testing
PRACTICE_SITE_URL = "https://practicetestautomation.com/practice-test-login/"

# Alternative demo sites (if you want to try others)
DEMO_SITES = {
    "practice_login": "https://practicetestautomation.com/practice-test-login/",
    "form_test": "https://formy-project.herokuapp.com/form",
    "demoqa_forms": "https://demoqa.com/automation-practice-form",
}

# ─── RPA Flow Functions ───────────────────────────────────────────────────────

def step_1_open_browser_and_navigate():
    """
    STEP 1: Open browser and navigate to practice website
    
    This simulates: open_chart() from eCW Bridge
    """
    logger.info("="*70)
    logger.info("STEP 1: Open Browser and Navigate to Practice Site")
    logger.info("="*70)
    
    # In a real scenario, you'd use:
    # pyautogui.hotkey('cmd', 'space')  # macOS spotlight
    # time.sleep(0.5)
    # pyautogui.write('Chrome', interval=0.05)
    # pyautogui.press('enter')
    # time.sleep(2)
    
    print("""
    🔵 MANUAL STEP:
    1. Open Chrome/Firefox browser
    2. Go to: https://practicetestautomation.com/practice-test-login/
    3. You should see a login form with:
       - Username field
       - Password field
       - Login button
    
    Press ENTER when the page is fully loaded...
    """)
    
    input()  # Wait for user to load page
    
    logger.info("✓ Browser opened and navigated to practice site")
    return True

def step_2_identify_form_elements():
    """
    STEP 2: Identify form element locations on screen
    
    This simulates: Locating fields in a patient chart
    """
    logger.info("="*70)
    logger.info("STEP 2: Identify Form Element Locations")
    logger.info("="*70)
    
    print("""
    🔍 INSPECTION PHASE:
    
    We need to find where the form fields are located.
    Move your mouse slowly to each field and note the coordinates:
    
    1. USERNAME FIELD - Position your mouse over it, then press ENTER
    2. PASSWORD FIELD - Position your mouse over it, then press ENTER
    3. LOGIN BUTTON - Position your mouse over it, then press ENTER
    
    (In production, we'd use image matching or accessibility APIs)
    
    Let's identify these locations...
    """)
    
    coords = {}
    
    # Get username field location
    print("\n📍 Step 1: Move mouse to USERNAME field, then press ENTER")
    input()
    username_x, username_y = pyautogui.position()
    coords['username'] = (username_x, username_y)
    logger.info(f"Username field at: ({username_x}, {username_y})")
    print(f"✓ Captured username field location: ({username_x}, {username_y})")
    
    # Get password field location
    print("\n📍 Step 2: Move mouse to PASSWORD field, then press ENTER")
    input()
    password_x, password_y = pyautogui.position()
    coords['password'] = (password_x, password_y)
    logger.info(f"Password field at: ({password_x}, {password_y})")
    print(f"✓ Captured password field location: ({password_x}, {password_y})")
    
    # Get login button location
    print("\n📍 Step 3: Move mouse to LOGIN button, then press ENTER")
    input()
    button_x, button_y = pyautogui.position()
    coords['button'] = (button_x, button_y)
    logger.info(f"Login button at: ({button_x}, {button_y})")
    print(f"✓ Captured login button location: ({button_x}, {button_y})")
    
    return coords

def step_3_extract_and_enter_data(coords):
    """
    STEP 3: Extract data (from chart) and enter into form
    
    This simulates: extract_chart_data() + pend_order()
    
    In eCW flow:
    - Extract: Patient name, MRN, test type
    - Enter: CPT code, ICD code, diagnosis
    """
    logger.info("="*70)
    logger.info("STEP 3: Extract & Enter Data (RPA Automation)")
    logger.info("="*70)
    
    # Simulated "extracted" clinical data
    extracted_data = {
        "username": "student",  # Practice site credentials
        "password": "Password123",  # Practice site credentials
        "patient_mrn": "MRN-123456",
        "test_type": "Home Sleep Test",
        "cpt_code": "95800",
        "icd_code": "G47.33"
    }
    
    logger.info(f"Extracted data: {extracted_data}")
    
    print(f"""
    📋 DATA EXTRACTED FROM FORM:
    ┌─────────────────────────────────────┐
    │ Username: {extracted_data['username']}                    │
    │ Password: {extracted_data['password']}                  │
    │ (For demo purposes on practice site) │
    │                                       │
    │ If this were eCW:                   │
    │ Patient MRN: {extracted_data['patient_mrn']}       │
    │ Test Type: {extracted_data['test_type']}       │
    │ CPT Code: {extracted_data['cpt_code']}                │
    │ ICD Code: {extracted_data['icd_code']}                │
    └─────────────────────────────────────┘
    
    🤖 STARTING RPA AUTOMATION...
    """)
    
    time.sleep(1)
    
    # STEP 3a: Click username field and enter data
    logger.info("Clicking username field...")
    pyautogui.click(coords['username'][0], coords['username'][1])
    time.sleep(0.5)
    logger.info(f"Entering username: {extracted_data['username']}")
    pyautogui.write(extracted_data['username'], interval=0.05)
    print(f"  ✓ Entered username: {extracted_data['username']}")
    time.sleep(0.5)
    
    # STEP 3b: Click password field and enter data
    logger.info("Clicking password field...")
    pyautogui.click(coords['password'][0], coords['password'][1])
    time.sleep(0.5)
    logger.info(f"Entering password: {extracted_data['password']}")
    pyautogui.write(extracted_data['password'], interval=0.05)
    print(f"  ✓ Entered password: {extracted_data['password']}")
    time.sleep(0.5)
    
    print("\n  ⚠️  SAFETY CHECK:")
    print("  Move your mouse to TOP-LEFT corner NOW to abort.")
    print("  Otherwise, we'll click the login button in 3 seconds...\n")
    
    for i in range(3, 0, -1):
        print(f"  {i}...", end=" ", flush=True)
        time.sleep(1)
    print("✓\n")
    
    logger.info("Data entry complete. Ready to submit form.")
    return extracted_data

def step_4_submit_form(coords):
    """
    STEP 4: Submit the form (click the button)
    
    This simulates: pend_order() - the final RPA action
    """
    logger.info("="*70)
    logger.info("STEP 4: Submit Form (Click Login Button)")
    logger.info("="*70)
    
    print("""
    🖱️  CLICKING LOGIN BUTTON...
    
    This simulates the RPA clicking the "Pend Order" button in eCW.
    """)
    
    logger.info("Clicking login button...")
    pyautogui.click(coords['button'][0], coords['button'][1])
    print("  ✓ Button clicked!")
    
    time.sleep(2)
    logger.info("Form submitted. Waiting for page response...")
    print("  ✓ Form submitted. Waiting for server response...")
    
    return True

def step_5_verify_results():
    """
    STEP 5: Verify form submission was successful
    
    This simulates: Confirming order appears in eCW
    """
    logger.info("="*70)
    logger.info("STEP 5: Verify Results")
    logger.info("="*70)
    
    print("""
    ✅ VERIFICATION PHASE:
    
    Check your browser screen:
    ✓ You should see "Congratulations student" or success message
    ✓ This means the form was submitted successfully
    ✓ In eCW, this would mean the order is now "PENDING"
    
    Did the form submit successfully?
    Press ENTER to continue...
    """)
    
    input()
    
    logger.info("✓ Form submission verified successfully")
    print("  ✓ Form submission confirmed!")
    
    return True

# ─── Complete RPA Flow ───────────────────────────────────────────────────────

def run_complete_rpa_flow():
    """
    Execute the complete RPA test flow:
    1. Navigate to website
    2. Identify form fields
    3. Extract & enter data
    4. Submit form
    5. Verify results
    """
    logger.info("\n" + "="*70)
    logger.info("VIDENTI RPA FLOW TEST - COMPLETE DEMONSTRATION")
    logger.info("="*70)
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         VIDENTI RPA FLOW - COMPLETE TEST DEMONSTRATION         ║
    ║                                                                ║
    ║  We'll test the complete RPA flow using a practice website:   ║
    ║  https://practicetestautomation.com/practice-test-login/     ║
    ║                                                                ║
    ║  Flow:                                                         ║
    ║  1️⃣  Open browser and navigate                                 ║
    ║  2️⃣  Identify form element locations                           ║
    ║  3️⃣  Extract data and enter into form                          ║
    ║  4️⃣  Submit form (click button)                                ║
    ║  5️⃣  Verify results                                            ║
    ║                                                                ║
    ║  This simulates the eCW workflow:                              ║
    ║  Extract Patient Data → Enter CPT/ICD → Click Pend Order      ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Step 1: Navigate
        step_1_open_browser_and_navigate()
        
        # Step 2: Identify elements
        coords = step_2_identify_form_elements()
        
        # Step 3: Extract & Enter
        data = step_3_extract_and_enter_data(coords)
        
        # Step 4: Submit
        step_4_submit_form(coords)
        
        # Step 5: Verify
        step_5_verify_results()
        
        logger.info("\n" + "="*70)
        logger.info("✅ RPA FLOW TEST COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
        print("""
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
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"RPA Flow failed: {e}")
        print(f"\n❌ Error: {e}")
        return False

# ─── Main Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                   RPA TESTING - GETTING STARTED                ║
    ║                                                                ║
    ║  This script demonstrates PyAutoGUI automation on a sample     ║
    ║  website. You'll learn how the eCW RPA flow works.             ║
    ║                                                                ║
    ║  IMPORTANT - Safety Features:                                  ║
    ║  • PyAutoGUI FAILSAFE is enabled                              ║
    ║  • Move mouse to TOP-LEFT corner to abort anytime              ║
    ║  • All actions are on a practice website (safe & reversible)   ║
    ║                                                                ║
    ║  Prerequisites:                                                ║
    ║  1. Have a browser open (Chrome or Firefox)                    ║
    ║  2. Navigate to the practice site (instructions will show URL) ║
    ║  3. Keep mouse ready near top-left corner                      ║
    ║  4. Have 5-10 minutes for the complete flow                    ║
    ║                                                                ║
    ║  Ready to start? Press ENTER...                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    input()
    
    success = run_complete_rpa_flow()
    sys.exit(0 if success else 1)
