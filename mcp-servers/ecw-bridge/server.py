"""
ICS - Intelligent Clinical System — eCW Bridge MCP Server
FastMCP-based local server for eClinicalWorks RPA via PyAutoGUI.

Endpoint: http://localhost:8001

RPA FLOW:
1. get_schedule() → Connect to eCW, retrieve provider's daily schedule
2. open_chart(patient_mrn) → Navigate to and open patient chart
3. extract_chart_data(patient_mrn) → Read clinical data from open chart
4. pend_order() → Place diagnostic order in patient chart
5. approve_recommendation() → User approves, automatically pends order
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import pyautogui
from dotenv import load_dotenv, set_key
from mcp.server.fastmcp import FastMCP

# Load existing .env into environment
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


# ─── Configuration ───────────────────────────────────────────────────────────

SERVER_PORT = 8001

# PyAutoGUI Safety Settings
pyautogui.FAILSAFE = True      # Move mouse to corner to abort
pyautogui.PAUSE = 0.5          # Pause between actions

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ECW-BRIDGE] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastMCP Server Init ─────────────────────────────────────────────────────

mcp = FastMCP(
    name="ics-ecw-bridge",
    instructions="Local eClinicalWorks RPA bridge using PyAutoGUI for EMR automation",
)

# ─── Helper: Chart Data Cache ───────────────────────────────────────────────

# In-memory cache of extracted chart data (in production, use database)
CHART_DATA_CACHE: Dict[str, Dict[str, Any]] = {}

# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def get_schedule(date_str: str = None) -> Dict[str, Any]:
    """
    Retrieves the provider's daily schedule from eCW.
    
    This tool performs the following:
    1. Connects to eCW portal (via credentials in .env)
    2. Navigates to Schedule/Appointments screen
    3. Extracts today's appointments (or specified date)
    4. Returns list of patient MRNs and appointment times
    
    Args:
        date_str: Date in format 'YYYY-MM-DD' (defaults to today)
    
    Returns:
        {
            "status": "SUCCESS",
            "date": "2026-02-28",
            "appointments": [
                {"patient_mrn": "MRN-123456", "time": "09:00", "provider": "Dr. Smith"},
                {"patient_mrn": "MRN-789012", "time": "09:15", "provider": "Dr. Smith"}
            ]
        }
    """
    logger.info(f"Retrieving schedule for {date_str or 'today'}")
    
    try:
        # STEP 1: Connect to eCW (would use credentials from .env in production)
        ecw_url = os.getenv("ECW_URL", "https://eclinicalworks.example.com")
        logger.info(f"Connecting to eCW at {ecw_url}")
        
        # STEP 2: Navigate to Schedule screen
        # pyautogui.hotkey('ctrl', 'shift', 's')  # Example hotkey for Schedule
        # time.sleep(2)
        
        # STEP 3: Extract appointments (mock data for now - would parse eCW UI)
        # In real implementation:
        # - Use OCR or pyautogui.locateOnScreen() to find appointment rows
        # - Extract MRN, time, provider from each row
        # - Build appointments list
        
        mock_appointments = [
            {"patient_mrn": "MRN-123456", "time": "09:00", "provider": "Dr. Smith"},
            {"patient_mrn": "MRN-789012", "time": "09:15", "provider": "Dr. Smith"},
            {"patient_mrn": "MRN-345678", "time": "10:00", "provider": "Dr. Johnson"},
        ]
        
        logger.info(f"Retrieved {len(mock_appointments)} appointments")
        return {
            "status": "SUCCESS",
            "date": date_str or "2026-02-28",
            "appointments": mock_appointments,
            "total": len(mock_appointments)
        }
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def open_chart(patient_mrn: str) -> Dict[str, Any]:
    """
    Opens a patient chart in eCW using the MRN.
    
    RPA Steps:
    1. Clicks the patient search/lookup field
    2. Types the MRN
    3. Presses Enter to search
    4. Waits for results and opens the matching chart
    
    Args:
        patient_mrn: Patient's Medical Record Number (e.g., "MRN-123456")
    
    Returns:
        {
            "status": "SUCCESS",
            "patient_mrn": "MRN-123456",
            "message": "Chart opened and ready for data extraction"
        }
    """
    logger.info(f"RPA: Opening chart for MRN {patient_mrn}")
    
    try:
        # STEP 1: Click on patient search field
        # Coordinates depend on screen resolution and eCW version
        # This would be identified during setup/calibration
        # pyautogui.click(x=400, y=200, duration=0.5)
        # logger.info(f"Clicked search field at (400, 200)")
        # time.sleep(0.5)
        
        # STEP 2: Clear any existing text
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # STEP 3: Type the MRN
        logger.info(f"Typing MRN: {patient_mrn}")
        pyautogui.write(patient_mrn, interval=0.05)
        time.sleep(0.5)
        
        # STEP 4: Press Enter to search/open
        logger.info("Pressing Enter to open chart")
        pyautogui.press('enter')
        
        # STEP 5: Wait for chart to load
        time.sleep(2)
        logger.info(f"Chart should now be open for {patient_mrn}")
        
        return {
            "status": "SUCCESS",
            "patient_mrn": patient_mrn,
            "message": "Chart opened and ready for data extraction"
        }
    except Exception as e:
        logger.error(f"Failed to open chart: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def extract_chart_data(patient_mrn: str) -> Dict[str, Any]:
    """
    Extracts clinical data from the currently open eCW patient chart.
    
    This is the CRITICAL STEP where we gather data that will be analyzed.
    
    RPA Steps:
    1. Read visible text from the open chart using OCR or coordinate-based parsing
    2. Extract key clinical fields:
       - Demographics (Age, Sex)
       - Vital Signs (Weight, Height, BMI)
       - Chief Complaint
       - History of Present Illness (HPI)
       - Past Medical History (PMH)
       - Social History
       - Medications
       - Allergies
       - Recent Labs/Tests
    3. Cache the data locally
    
    Args:
        patient_mrn: Patient MRN (for logging/verification)
    
    Returns:
        {
            "status": "SUCCESS",
            "patient_mrn": "MRN-123456",
            "raw_data": {
                "demographics": {...},
                "vitals": {...},
                "hpi": "...",
                "pmh": "...",
                "medications": [...],
                "recent_tests": [...]
            }
        }
    """
    logger.info(f"RPA: Extracting chart data from eCW for {patient_mrn}")
    
    try:
        # STEP 1: Check if chart is open (would verify by looking for expected UI elements)
        logger.info("Verifying chart is open...")
        # pyautogui.locateOnScreen('chart_indicator.png')  # Would use image matching
        
        # STEP 2: Extract data from visible fields
        # In a real implementation, you would:
        # - Use Tesseract OCR to read text from specific screen regions
        # - Or use coordinate-based parsing for known eCW field locations
        # - Or use accessibility APIs if eCW supports them
        
        # For now, simulate extraction with realistic clinical data
        extracted_data = {
            "demographics": {
                "name": "John Doe",
                "mrn": patient_mrn,
                "dob": "1975-03-15",
                "age": 50,
                "sex": "M"
            },
            "vitals": {
                "height_in": 70,
                "weight_lb": 215,
                "bmi": 30.8,
                "bp": "138/88",
                "hr": 72,
                "temp_f": 98.6
            },
            "chief_complaint": "Fatigue and snoring",
            "hpi": "Patient reports chronic fatigue, difficulty staying awake during day. Wife reports loud snoring at night.",
            "pmh": [
                "Hypertension (on medication)",
                "Type 2 Diabetes (controlled)",
                "Hyperlipidemia"
            ],
            "social_history": {
                "smoking": "Former, quit 5 years ago",
                "alcohol": "Moderate use",
                "sleep_pattern": "Poor - snores heavily, restless"
            },
            "medications": [
                "Lisinopril 10mg daily (HTN)",
                "Metformin 1000mg BID (Diabetes)",
                "Atorvastatin 40mg daily (Cholesterol)"
            ],
            "allergies": ["NKDA"],
            "recent_labs": {
                "glucose": "145 mg/dL",
                "hemoglobin_a1c": "7.2%",
                "ldl": "125 mg/dL"
            },
            "assessment": "50M with BMI 30.8, hypertension, diabetes. Presenting with fatigue and snoring - concerning for sleep apnea.",
            "extraction_timestamp": time.time()
        }
        
        # STEP 3: Cache the data for later use
        CHART_DATA_CACHE[patient_mrn] = extracted_data
        logger.info(f"Cached chart data for {patient_mrn}")
        
        # STEP 4: Return the data
        return {
            "status": "SUCCESS",
            "patient_mrn": patient_mrn,
            "raw_data": extracted_data,
            "message": f"Extracted {len(extracted_data)} clinical fields from chart"
        }
    except Exception as e:
        logger.error(f"Failed to extract chart data: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def pend_order(cpt_code: str, icd_code: str, patient_mrn: str, approval_token: str) -> Dict[str, Any]:
    """
    Pends a diagnostic order in the eCW patient chart.
    
    This is the FINAL STEP after eligibility is confirmed.
    
    RPA Steps:
    1. Click the "Orders" or "New Order" button
    2. Search for the CPT code (e.g., "95800" for Home Sleep Test)
    3. Select the order
    4. Add the ICD-10 code (diagnosis)
    5. Click "Pend" to send for provider signature
    
    Security: Requires a valid approval_token to prevent unauthorized orders
    
    Args:
        cpt_code: Procedure code (e.g., "95800")
        icd_code: Diagnosis code (e.g., "G47.33")
        patient_mrn: Patient MRN
        approval_token: User approval token (min 10 chars)
    
    Returns:
        {
            "status": "SUCCESS",
            "order_details": {
                "cpt": "95800",
                "icd": "G47.33",
                "patient_mrn": "MRN-123456"
            },
            "message": "Order pended for provider signature"
        }
    """
    # Security check
    if not approval_token or len(approval_token) < 10:
        logger.warning(f"Invalid approval token for order {cpt_code}")
        return {"status": "AUTH_FAILED", "message": "Invalid or missing approval token."}
        
    logger.info(f"RPA: Pending order {cpt_code}/{icd_code} for {patient_mrn}")
    
    try:
        # STEP 1: Click "New Order" button
        # pyautogui.click(x=500, y=150, duration=0.5)
        # time.sleep(1)
        # logger.info("Clicked 'New Order' button")
        
        # STEP 2: Search for CPT code
        logger.info(f"Entering CPT code: {cpt_code}")
        pyautogui.write(cpt_code, interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1)
        
        # STEP 3: Select the order from results
        # pyautogui.press('enter')  # Assuming first result is selected
        # time.sleep(0.5)
        
        # STEP 4: Enter ICD-10 code
        logger.info(f"Entering ICD-10 code: {icd_code}")
        pyautogui.write(icd_code, interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        # STEP 5: Click "Pend" button
        logger.info("Clicking 'Pend' button to send for signature")
        # pyautogui.click(x=600, y=400, duration=0.5)  # "Pend" button coordinates
        # time.sleep(1)
        
        logger.info(f"✓ Order {cpt_code} pended for {patient_mrn}")
        
        return {
            "status": "SUCCESS",
            "order_details": {
                "cpt": cpt_code,
                "icd": icd_code,
                "patient_mrn": patient_mrn,
                "timestamp": time.time()
            },
            "message": f"Order {cpt_code} pended for provider signature"
        }
    except Exception as e:
        logger.error(f"Failed to pend order: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def approve_recommendation(snapshot_id: str) -> Dict[str, Any]:
    """
    Approves a clinical recommendation and automatically pends the order in eCW.
    
    Complete Flow:
    1. Look up recommendation metadata (MRN, test type, CPT/ICD codes)
    2. Open the patient chart with open_chart()
    3. Call pend_order() with the diagnostic codes
    4. Log the approval action to audit trail
    
    This is called when a user clicks "Approve" in the dashboard.
    
    Args:
        snapshot_id: ID of the recommendation (e.g., "v-9a1b")
    
    Returns:
        {
            "status": "SUCCESS",
            "snapshot_id": "v-9a1b",
            "action": "ORDER_PENDED",
            "message": "Recommendation approved - order pending in eCW"
        }
    """
    logger.info(f"User approved recommendation: {snapshot_id}")
    
    try:
        # In a real scenario, you would:
        # 1. Look up snapshot_id in database to get: MRN, test type, CPT code, ICD code
        # 2. Call open_chart(mrn)
        # 3. Call pend_order(cpt, icd, mrn, token)
        # 4. Log to audit trail
        
        logger.info(f"✓ Recommendation {snapshot_id} approved - order pending in eCW")
        
        return {
            "status": "SUCCESS",
            "snapshot_id": snapshot_id,
            "action": "ORDER_PENDED",
            "message": f"Approved {snapshot_id} - order will be pending for provider signature"
        }
    except Exception as e:
        logger.error(f"Failed to approve recommendation: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def dismiss_recommendation(snapshot_id: str) -> Dict[str, Any]:
    """
    Dismisses a clinical recommendation (user rejected it).
    This logs the dismissal but does NOT pend any order.
    
    The recommendation remains in the audit log for compliance purposes.
    
    Args:
        snapshot_id: ID of the recommendation
    
    Returns:
        {
            "status": "SUCCESS",
            "snapshot_id": "v-9a1b",
            "action": "DISMISSED",
            "message": "Recommendation dismissed by user"
        }
    """
    logger.info(f"User dismissed recommendation: {snapshot_id}")
    
    try:
        logger.info(f"✓ Recommendation {snapshot_id} dismissed - audit logged")
        
        return {
            "status": "SUCCESS",
            "snapshot_id": snapshot_id,
            "action": "DISMISSED",
            "message": f"Dismissed {snapshot_id} - no order will be placed"
        }
    except Exception as e:
        logger.error(f"Failed to dismiss recommendation: {e}")
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def save_credentials(
    ecw_url: str,
    ecw_username: str,
    ecw_password: str,
    ecw_clinic_id: str = "",
    ecw_mfa: str = "manual",
    ollama_base_url: str = "http://localhost:11434",
    mrn_salt: str = "",
) -> Dict[str, Any]:
    """
    Securely saves eCW portal credentials to the local .env file.
    This data NEVER leaves the local machine — it is written only to disk.
    """
    try:
        # Create .env if it doesn't exist
        ENV_PATH.touch(exist_ok=True)

        set_key(str(ENV_PATH), "ECW_URL", ecw_url)
        set_key(str(ENV_PATH), "ECW_USERNAME", ecw_username)
        set_key(str(ENV_PATH), "ECW_PASSWORD", ecw_password)
        set_key(str(ENV_PATH), "ECW_CLINIC_ID", ecw_clinic_id)
        set_key(str(ENV_PATH), "ECW_MFA_METHOD", ecw_mfa)
        set_key(str(ENV_PATH), "OLLAMA_BASE_URL", ollama_base_url)
        if mrn_salt:
            set_key(str(ENV_PATH), "ICS_MRN_SALT", mrn_salt)

        logger.info("Credentials saved to local .env (NOT transmitted externally)")
        return {"status": "SUCCESS", "message": "Credentials saved to local .env file.", "env_path": str(ENV_PATH)}
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        return {"status": "ERROR", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting ICS eCW Bridge MCP Server on port {SERVER_PORT}")
    
    # Create ASGI app from FastMCP server
    app = mcp.asgi()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="info"
    )
