"""
REAL RPA DEMO: Create a Google Account with Dummy Values
=========================================================

This script shows you EXACTLY how RPA works by:
1. Opening Google account signup page
2. Identifying form fields on screen
3. Filling them with dummy data
4. Submitting the form

You'll SEE it happen in real-time on your screen!

IMPORTANT: This is educational. We'll fill the form but NOT submit,
so we don't actually create unwanted accounts.
"""

import pyautogui
import time
import webbrowser
import logging

# ─────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PyAutoGUI Safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# ─────────────────────────────────────────────────────────────────

def show_intro():
    """Show what we're about to do"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     REAL RPA DEMO: Create Google Account with Dummy Data       ║
    ║                                                                ║
    ║  What will happen:                                             ║
    ║  1. Browser opens Google account signup page                  ║
    ║  2. You identify form field locations                         ║
    ║  3. RPA fills all fields with dummy data AUTOMATICALLY        ║
    ║  4. You watch it happen in real-time                          ║
    ║  5. We DON'T submit (so no actual account created)            ║
    ║                                                                ║
    ║  Why this matters for eCW RPA:                                ║
    ║  • Same technique fills CPT codes in eCW                      ║
    ║  • Same technique fills ICD-10 codes                          ║
    ║  • Same technique clicks "Pend Order" button                  ║
    ║  • Same technique fills MRN search field                      ║
    ║                                                                ║
    ║  Safety Features:                                              ║
    ║  ⚠️  Move mouse to TOP-LEFT corner anytime to STOP            ║
    ║  ⚠️  We show you exactly what's happening                     ║
    ║  ⚠️  Complete logging of every action                         ║
    ║                                                                ║
    ║  Prerequisites:                                                ║
    ║  • Chrome or Firefox browser installed                        ║
    ║  • ~10 minutes of time                                        ║
    ║  • Keep mouse ready near top-left corner                      ║
    ║                                                                ║
    ║  Ready to see RPA in action? Press ENTER to continue...       ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    input()

def step_1_open_google_signup():
    """STEP 1: Open browser and navigate to Google signup"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 1: OPEN GOOGLE ACCOUNT SIGNUP PAGE                       ║
    ║                                                                ║
    ║  What we're doing:                                             ║
    ║  • Opening browser                                             ║
    ║  • Navigating to Google account creation                      ║
    ║  • Waiting for page to load                                   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Opening Google account signup page...")
    print("\n📱 Opening browser and navigating to Google signup...")
    print("   URL: https://accounts.google.com/signup")
    
    # Open browser
    url = "https://accounts.google.com/signup"
    webbrowser.open(url)
    
    print("\n⏳ Waiting for page to load (give it 10 seconds)...")
    time.sleep(10)
    
    print("\n✓ Page should now be loaded in your browser")
    print("\nYou should see a Google account signup form with fields:")
    print("  • First name")
    print("  • Last name")
    print("  • Username/Email")
    print("  • Password")
    print("  • Confirm password")
    
    print("\nPress ENTER when the form is fully visible...")
    input()
    
    logger.info("✓ Google signup page opened")

def step_2_identify_form_fields():
    """STEP 2: You identify where the form fields are"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 2: IDENTIFY FORM FIELD LOCATIONS                         ║
    ║                                                                ║
    ║  What we're doing:                                             ║
    ║  • You position mouse over each field                         ║
    ║  • Python captures the coordinates (x, y)                     ║
    ║  • We save these for automated filling                        ║
    ║                                                                ║
    ║  This is how RPA "learns" the website:                        ║
    ║  Instead of being programmed with fixed coordinates,          ║
    ║  You teach it where things are by pointing!                   ║
    ║                                                                ║
    ║  Think of it like:                                             ║
    ║  "Hey, see that text box? That's where we type the name"      ║
    ║  "And that blue button? That's what we click"                 ║
    ║                                                                ║
    ║  The same technique works for eCW:                            ║
    ║  You show RPA where the MRN field is                          ║
    ║  You show RPA where the CPT code field is                     ║
    ║  You show RPA where the "Pend Order" button is               ║
    ║  Then RPA does it automatically every time!                  ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    coords = {}
    fields = [
        ("First name", "first_name"),
        ("Last name", "last_name"),
        ("Username (email)", "email"),
        ("Password", "password"),
        ("Confirm password", "password_confirm"),
    ]
    
    print("\n🔍 FIELD IDENTIFICATION PHASE")
    print("=" * 70)
    
    for i, (display_name, field_key) in enumerate(fields, 1):
        print(f"\n{i}. {display_name} field")
        print("   ➜ Move your mouse to the input field")
        print("   ➜ Position cursor in the middle of the field")
        print("   ➜ Press ENTER when positioned")
        print(f"   (Currently identifying: {display_name})")
        
        input()
        
        x, y = pyautogui.position()
        coords[field_key] = (x, y)
        
        logger.info(f"Captured {field_key} at ({x}, {y})")
        print(f"   ✓ Field location saved: ({x}, {y})")
    
    print("\n" + "=" * 70)
    print("✅ ALL FIELD LOCATIONS IDENTIFIED")
    print("=" * 70)
    print(f"\nCoordinates map:")
    for key, (x, y) in coords.items():
        print(f"  {key:20} → ({x}, {y})")
    
    print("\nNow RPA 'knows' where everything is!")
    print("It can fill the form automatically.\n")
    
    return coords

def step_3_prepare_dummy_data():
    """STEP 3: Show what data we'll fill"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 3: PREPARE DUMMY DATA                                    ║
    ║                                                                ║
    ║  What we're doing:                                             ║
    ║  • Creating realistic dummy data                              ║
    ║  • This data will be automatically filled                     ║
    ║  • You'll watch it appear in the form in real-time            ║
    ║                                                                ║
    ║  For eCW, this would be:                                       ║
    ║  • CPT Code: 95800 (Home Sleep Test)                          ║
    ║  • ICD Code: G47.33 (Sleep Apnea)                             ║
    ║  • But here we're using account signup data                   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    dummy_data = {
        "first_name": "John",
        "last_name": "Demo",
        "email": "john.demo.rpa.test@gmail.com",
        "password": "TestRPA@2024!",
        "password_confirm": "TestRPA@2024!",
    }
    
    print("\n📋 DUMMY DATA TO BE FILLED:")
    print("=" * 70)
    print(f"  First Name:        {dummy_data['first_name']}")
    print(f"  Last Name:         {dummy_data['last_name']}")
    print(f"  Email:             {dummy_data['email']}")
    print(f"  Password:          {dummy_data['password']}")
    print(f"  Confirm Password:  {dummy_data['password_confirm']}")
    print("=" * 70)
    
    print("\nThis is realistic data like what eCW RPA would fill:")
    print("  • Field names: Readable and meaningful")
    print("  • Values: Appropriate for each field")
    print("  • Timing: Simulates human typing speed\n")
    
    return dummy_data

def step_4_automated_form_filling(coords, data):
    """STEP 4: RPA automatically fills the form"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 4: AUTOMATED FORM FILLING                                ║
    ║                                                                ║
    ║  What's about to happen:                                       ║
    ║  1. RPA clicks on each field (using saved coordinates)        ║
    ║  2. RPA types the data (simulating human typing)              ║
    ║  3. YOU WATCH IT HAPPEN IN REAL-TIME                          ║
    ║  4. All actions are logged                                    ║
    ║                                                                ║
    ║  SAFETY REMINDER:                                              ║
    ║  ⚠️  Move mouse to TOP-LEFT corner to STOP anytime            ║
    ║  ⚠️  This will trigger PyAutoGUI FAILSAFE                     ║
    ║                                                                ║
    ║  Ready? Press ENTER to start automated filling...             ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    input()
    
    print("\n" + "=" * 70)
    print("🤖 STARTING AUTOMATED FORM FILLING")
    print("=" * 70)
    
    field_order = [
        ("first_name", "First Name", data["first_name"]),
        ("last_name", "Last Name", data["last_name"]),
        ("email", "Email", data["email"]),
        ("password", "Password", data["password"]),
        ("password_confirm", "Confirm Password", data["password_confirm"]),
    ]
    
    for field_key, display_name, value in field_order:
        if field_key not in coords:
            print(f"⚠️  Field {field_key} not found in coordinates")
            continue
        
        x, y = coords[field_key]
        
        print(f"\n┌─ FILLING: {display_name}")
        print(f"│  Coordinates: ({x}, {y})")
        print(f"│  Value: {value}")
        print(f"└─ Starting in 2 seconds...")
        
        time.sleep(2)
        
        # Step 1: Click on the field
        logger.info(f"Clicking {field_key} at ({x}, {y})")
        print(f"   → Clicking field...")
        pyautogui.click(x, y)
        time.sleep(0.5)
        
        # Step 2: Clear any existing content
        logger.info(f"Clearing field {field_key}")
        pyautogui.hotkey('cmd' if sys.platform == 'darwin' else 'ctrl', 'a')
        time.sleep(0.2)
        
        # Step 3: Type the value slowly so you can see it
        logger.info(f"Typing into {field_key}: {value}")
        print(f"   → Typing: ", end="", flush=True)
        
        for char in value:
            pyautogui.write(char)
            print(char, end="", flush=True)
            time.sleep(0.05)  # Slow typing (50ms between chars)
        
        print()  # Newline
        print(f"   ✓ Field filled!")
        time.sleep(0.5)
        
        # Move to next field
        pyautogui.press('tab')
        time.sleep(0.3)

def step_5_verify_form():
    """STEP 5: Verify the form was filled"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 5: VERIFY FORM WAS FILLED                                ║
    ║                                                                ║
    ║  What we're doing:                                             ║
    ║  • Looking at the form in your browser                        ║
    ║  • Verifying all fields were filled correctly                 ║
    ║  • Checking for any errors                                    ║
    ║                                                                ║
    ║  In eCW, this would verify:                                    ║
    ║  ✓ CPT code field contains: 95800                             ║
    ║  ✓ ICD code field contains: G47.33                            ║
    ║  ✓ Patient MRN field contains: MRN-123456                     ║
    ║  ✓ Order is ready for submission                              ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n🔍 CHECKING YOUR BROWSER:")
    print("=" * 70)
    print("Look at the form in your browser.")
    print("\nYou should see:")
    print("  ✓ First name field filled with: John")
    print("  ✓ Last name field filled with: Demo")
    print("  ✓ Email field filled with: john.demo.rpa.test@gmail.com")
    print("  ✓ Password field filled with: TestRPA@2024!")
    print("  ✓ Confirm password field filled with: TestRPA@2024!")
    print("=" * 70)
    
    print("\n❓ Were all fields filled correctly?")
    print("   (Press 'y' for yes, 'n' for no)")
    
    response = input("   → ").strip().lower()
    
    if response == 'y':
        print("\n✅ VERIFICATION SUCCESSFUL!")
        print("   All fields were filled by RPA without any errors!")
        logger.info("Form verification successful")
        return True
    else:
        print("\n⚠️  Some fields may not have been filled correctly")
        print("   This could happen if:")
        print("   • Field coordinates were slightly off")
        print("   • Page took longer to load")
        print("   • Field IDs changed")
        print("\n   This is normal - we just calibrate and try again!")
        logger.warning("Form verification showed issues")
        return False

def step_6_do_not_submit():
    """STEP 6: Explain why we DON'T submit"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  STEP 6: WHY WE DON'T SUBMIT                                   ║
    ║                                                                ║
    ║  Important: We will NOT click the "Sign Up" button             ║
    ║  Why?                                                          ║
    ║  • This is a DEMO, not actually creating accounts             ║
    ║  • We don't want spam accounts created                        ║
    ║  • We've proven the RPA works (form is filled!)               ║
    ║  • Submitting would require phone verification                ║
    ║                                                                ║
    ║  But in PRODUCTION (eCW):                                      ║
    ║  ✓ We WOULD click the "Pend Order" button                     ║
    ║  ✓ The order would be submitted                               ║
    ║  ✓ Provider would see it in their queue                       ║
    ║                                                                ║
    ║  The technique is identical:                                   ║
    ║  1. Click button at coordinates                               ║
    ║  2. Wait for page to load                                     ║
    ║  3. Verify submission succeeded                               ║
    ║                                                                ║
    ║  We'll now close this browser tab...                           ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n📸 Screenshot the form if you want to keep proof of the demo!")
    print("\nPress ENTER to continue...")
    input()

def step_7_summary():
    """STEP 7: Summary of what we learned"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  ✅ RPA DEMO COMPLETE!                                         ║
    ║                                                                ║
    ║  What you just learned:                                        ║
    ╚════════════════════════════════════════════════════════════════╝
    
    HOW RPA LEARNS WEBSITES:
    ════════════════════════════════════════════════════════════════
    
    1️⃣  CALIBRATION (Manual, done once)
        ─────────────────────────────────
        You: "Move mouse to each field"
        Human: Positions mouse, presses ENTER
        RPA: Captures coordinates (x, y)
        
        Example:
        • First name field: (245, 150)
        • Last name field: (400, 150)
        • Submit button: (500, 300)
        
        ✓ RPA now "knows" the layout


    2️⃣  AUTOMATED INTERACTION (Automatic, done repeatedly)
        ─────────────────────────────────────────────────────
        For each action needed:
        
        pyautogui.click(245, 150)           # Click first name field
        pyautogui.write("John")             # Type first name
        
        pyautogui.click(400, 150)           # Click last name field
        pyautogui.write("Demo")             # Type last name
        
        pyautogui.click(500, 300)           # Click submit
        
        ✓ Same action every time, consistent and reliable


    HOW THIS APPLIES TO eCW:
    ════════════════════════════════════════════════════════════════
    
    CALIBRATION:
        • Find MRN search field coordinates: (x1, y1)
        • Find CPT code field coordinates: (x2, y2)
        • Find ICD code field coordinates: (x3, y3)
        • Find "Pend Order" button coordinates: (x4, y4)
    
    AUTOMATION:
        • Click MRN field → Type "MRN-123456"
        • Click CPT field → Type "95800"
        • Click ICD field → Type "G47.33"
        • Click "Pend Order" → Order placed!
    
    EVERY DAY AT 7:30 AM:
        • Process 50 patients automatically
        • Each takes ~20 seconds (vs 5 minutes manual)
        • All orders placed reliably
        • All actions logged for audit trail
    
    
    KEY INSIGHTS:
    ════════════════════════════════════════════════════════════════
    
    ❓ How does RPA "learn"?
    ✓ By recording coordinates of buttons and fields
    ✓ That's it! Simple but powerful
    
    ❓ Is it fragile?
    ✓ A little - if page layout changes, coordinates change
    ✓ Solution: Use image matching or accessibility APIs
    ✓ Videnti uses both approaches for reliability
    
    ❓ Why not just use APIs?
    ✓ eCW may not have APIs for order placement
    ✓ RPA works with any UI-based system
    ✓ RPA is "glue code" that bridges legacy systems
    
    ❓ Is RPA ethical?
    ✓ YES - when used correctly
    ✓ Saves time, reduces human error
    ✓ Must be transparent (users know it's automated)
    ✓ Must be auditable (all actions logged)
    ✓ Videnti does all of this ✓
    
    
    WHAT YOU'VE PROVEN:
    ════════════════════════════════════════════════════════════════
    
    ✅ RPA can identify website form fields
    ✅ RPA can automatically fill forms with data
    ✅ RPA can type at human-like speed
    ✅ RPA is reliable and repeatable
    ✅ RPA can be safely controlled (failsafe)
    ✅ RPA actions can be fully logged
    ✅ Same technique works for eCW, Google, any website
    
    
    NEXT STEPS:
    ════════════════════════════════════════════════════════════════
    
    Option 1: Test eCW coordinates
    ├─ Screenshot your eCW instance
    ├─ Identify button locations
    ├─ Test RPA with real eCW
    └─ Place real orders automatically
    
    Option 2: Run Videnti system
    ├─ Start all three MCP servers
    ├─ Open dashboard at http://localhost:5173
    ├─ Trigger orchestrator
    └─ Watch recommendations appear and approve orders
    
    Option 3: Understand the full pipeline
    ├─ Read PROJECT_CONTEXT.md
    ├─ Review RPA_DATA_FLOW.md
    ├─ Study the test suite
    └─ See how everything connects
    
    
    ═══════════════════════════════════════════════════════════════════
    
    You now understand how RPA works! 🎉
    
    It's not magic - just:
    1. Record coordinates (x, y)
    2. Click at those coordinates
    3. Type the data
    4. Repeat reliably, every time
    
    Simple but powerful! 💪
    
    ═══════════════════════════════════════════════════════════════════
    """)

def main():
    """Run the complete RPA demo"""
    import sys
    
    try:
        show_intro()
        step_1_open_google_signup()
        coords = step_2_identify_form_fields()
        data = step_3_prepare_dummy_data()
        step_4_automated_form_filling(coords, data)
        success = step_5_verify_form()
        step_6_do_not_submit()
        step_7_summary()
        
        print("\n" + "="*70)
        print("🎉 RPA DEMO COMPLETE!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        logger.warning("Demo interrupted by user")
    except pyautogui.FailSafeException:
        print("\n\n⚠️  FAILSAFE TRIGGERED!")
        print("   (You moved mouse to top-left corner)")
        print("   PyAutoGUI safely stopped all automation")
        logger.warning("FAILSAFE triggered")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    import sys
    main()
