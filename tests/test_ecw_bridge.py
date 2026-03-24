"""
Module Tests: eCW Bridge MCP Server
Tests the complete RPA flow: schedule retrieval, chart opening, data extraction, and order placement.
"""

import pytest
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Unit Tests: Schedule Retrieval ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_schedule_returns_appointments(monkeypatch):
    """get_schedule should return a list of today's appointments with MRNs."""
    from mcp_servers.ecw_bridge.server import get_schedule

    result = await get_schedule()
    
    assert result.get("status") == "SUCCESS"
    assert "appointments" in result
    assert "date" in result
    assert len(result["appointments"]) > 0
    
    # Verify appointment structure
    for apt in result["appointments"]:
        assert "patient_mrn" in apt
        assert "time" in apt
        assert "provider" in apt
    
    print(f"✓ get_schedule returned {len(result['appointments'])} appointments")


@pytest.mark.asyncio
async def test_get_schedule_with_date(monkeypatch):
    """get_schedule should accept a specific date parameter."""
    from mcp_servers.ecw_bridge.server import get_schedule

    result = await get_schedule(date_str="2026-02-28")
    
    assert result.get("status") == "SUCCESS"
    assert result.get("date") == "2026-02-28"
    print(f"✓ get_schedule accepted date parameter")


# ── Unit Tests: Chart Opening ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_open_chart_with_valid_mrn(monkeypatch):
    """open_chart should successfully open a patient chart for a valid MRN."""
    from mcp_servers.ecw_bridge.server import open_chart
    from unittest.mock import MagicMock
    import sys

    # Mock pyautogui via sys.modules so the lazy import inside open_chart
    # gets the mock without needing a real display.
    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    result = await open_chart("MRN-123456")

    assert result.get("status") == "SUCCESS"
    assert result.get("patient_mrn") == "MRN-123456"
    assert "message" in result
    print(f"✓ open_chart successfully opened chart for MRN-123456")


@pytest.mark.asyncio
async def test_open_chart_handles_empty_mrn(monkeypatch):
    """open_chart should handle empty MRN gracefully."""
    from mcp_servers.ecw_bridge.server import open_chart
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    result = await open_chart("")

    # Should still succeed as open_chart doesn't validate - it just types what's given
    assert "status" in result
    print(f"✓ open_chart handled empty MRN")


# ── Unit Tests: Chart Data Extraction ────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_chart_data_returns_complete_data(monkeypatch):
    """extract_chart_data should return complete clinical information."""
    from mcp_servers.ecw_bridge.server import extract_chart_data

    result = await extract_chart_data("MRN-123456")
    
    assert result.get("status") == "SUCCESS"
    assert result.get("patient_mrn") == "MRN-123456"
    assert "raw_data" in result
    
    raw_data = result["raw_data"]
    
    # Verify all expected clinical fields are present
    assert "demographics" in raw_data
    assert "vitals" in raw_data
    assert "chief_complaint" in raw_data
    assert "hpi" in raw_data
    assert "pmh" in raw_data
    assert "social_history" in raw_data
    assert "medications" in raw_data
    assert "allergies" in raw_data
    assert "recent_labs" in raw_data
    assert "assessment" in raw_data
    
    print(f"✓ extract_chart_data returned complete clinical data")


@pytest.mark.asyncio
async def test_extract_chart_data_has_realistic_values(monkeypatch):
    """extract_chart_data should return clinically realistic data."""
    from mcp_servers.ecw_bridge.server import extract_chart_data

    result = await extract_chart_data("MRN-123456")
    raw_data = result["raw_data"]
    
    # Check demographics
    demo = raw_data["demographics"]
    assert demo["age"] > 0
    assert demo["sex"] in ["M", "F"]
    
    # Check vitals - realistic sleep apnea indicators
    vitals = raw_data["vitals"]
    assert vitals["bmi"] > 25  # Overweight
    assert vitals["height_in"] > 0
    assert vitals["weight_lb"] > 0
    
    # Check for sleep apnea indicators
    hpi = raw_data["hpi"]
    assert "snoring" in hpi.lower() or "fatigue" in hpi.lower()
    
    # Check PMH mentions hypertension (common with sleep apnea)
    pmh = raw_data["pmh"]
    assert any("hypertension" in item.lower() for item in pmh)
    
    print(f"✓ extract_chart_data returned clinically realistic data")


@pytest.mark.asyncio
async def test_extract_chart_data_caches_data(monkeypatch):
    """extract_chart_data should cache the encrypted snapshot for later use."""
    from mcp_servers.ecw_bridge.server import extract_chart_data, CHART_DATA_CACHE

    # Clear cache first
    CHART_DATA_CACHE.clear()

    result = await extract_chart_data("MRN-CACHE-TEST")

    # Verify an entry exists in the cache for this MRN
    assert "MRN-CACHE-TEST" in CHART_DATA_CACHE
    # Cache now stores (encrypted_token, timestamp) tuples
    cached_entry = CHART_DATA_CACHE["MRN-CACHE-TEST"]
    assert isinstance(cached_entry, tuple) and len(cached_entry) == 2
    cached_token, cached_ts = cached_entry
    assert isinstance(cached_token, str)
    assert len(cached_token) > 0

    # The raw_data returned in the response should still have demographics
    raw_data = result.get("raw_data", {})
    assert raw_data.get("demographics", {}).get("mrn") == "MRN-CACHE-TEST"

    print(f"✓ extract_chart_data cached encrypted snapshot for later use")


# ── Unit Tests: Order Placement ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pend_order_rejects_invalid_token(monkeypatch):
    """pend_order should return AUTH_FAILED for short/missing approval tokens."""
    from mcp_servers.ecw_bridge.server import pend_order

    result = await pend_order("95800", "G47.33", "MRN-123", "bad")
    assert result["status"] == "AUTH_FAILED", "Short token must be rejected"
    print("✓ pend_order correctly rejected invalid token")


@pytest.mark.asyncio
async def test_pend_order_accepts_valid_token(monkeypatch):
    """pend_order should place order with a valid approval token."""
    from mcp_servers.ecw_bridge.server import pend_order
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    result = await pend_order("95800", "G47.33", "MRN-123", "valid-token-12345")
    assert result["status"] == "SUCCESS", f"Expected SUCCESS, got: {result}"
    assert result["order_details"]["cpt"] == "95800"
    print(f"✓ pend_order succeeded with order details: {result['order_details']}")


@pytest.mark.asyncio
async def test_pend_order_with_home_sleep_test(monkeypatch):
    """pend_order should successfully place a Home Sleep Test order."""
    from mcp_servers.ecw_bridge.server import pend_order
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    # Home Sleep Test: CPT 95800, ICD-10 G47.33 (Sleep Apnea)
    result = await pend_order("95800", "G47.33", "MRN-123456", "approval-token-valid")

    assert result["status"] == "SUCCESS"
    assert result["order_details"]["cpt"] == "95800"
    assert result["order_details"]["icd"] == "G47.33"
    print(f"✓ Home Sleep Test order pended successfully")


@pytest.mark.asyncio
async def test_pend_order_with_eeg(monkeypatch):
    """pend_order should successfully place an EEG order."""
    from mcp_servers.ecw_bridge.server import pend_order
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    # EEG: CPT 95816, ICD-10 R56.9 (Seizure)
    result = await pend_order("95816", "R56.9", "MRN-789012", "approval-token-valid")
    
    assert result["status"] == "SUCCESS"
    assert result["order_details"]["cpt"] == "95816"
    print(f"✓ EEG order pended successfully")


# ── Unit Tests: Credentials ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_credentials_writes_env(tmp_path, monkeypatch):
    """save_credentials must write all keys to the .env file."""
    import mcp_servers.ecw_bridge.server as bridge_module

    # Override ENV_PATH to use a temp file
    test_env = tmp_path / ".env"
    monkeypatch.setattr(bridge_module, "ENV_PATH", test_env)

    result = await bridge_module.save_credentials(
        ecw_url="https://test.eclinicalworks.com",
        ecw_username="testuser",
        ecw_password="testpass",
        ecw_clinic_id="CL-001",
        mrn_salt="abc123xyz-very-secret-salt-here!!"
    )

    assert result["status"] == "SUCCESS"
    env_content = test_env.read_text()
    assert "ECW_URL" in env_content
    assert "ECW_USERNAME" in env_content
    assert "ICS_MRN_SALT" in env_content
    print("✓ save_credentials correctly wrote all keys to .env")


# ── Integration Tests: Complete RPA Flow ─────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_rpa_flow_get_schedule_to_extract_data(monkeypatch):
    """
    Test the complete RPA flow:
    1. Get schedule from eCW
    2. Open first patient chart
    3. Extract clinical data
    4. Verify data is ready for Ollama anonymization
    """
    from mcp_servers.ecw_bridge.server import (
        get_schedule, open_chart, extract_chart_data, CHART_DATA_CACHE
    )
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)

    CHART_DATA_CACHE.clear()

    # STEP 1: Get schedule
    schedule = await get_schedule()
    assert schedule["status"] == "SUCCESS"
    assert len(schedule["appointments"]) > 0
    print(f"✓ Step 1: Retrieved {len(schedule['appointments'])} appointments")

    # STEP 2: Open chart for first patient
    first_mrn = schedule["appointments"][0]["patient_mrn"]
    open_result = await open_chart(first_mrn)
    assert open_result["status"] == "SUCCESS"
    print(f"✓ Step 2: Opened chart for {first_mrn}")

    # STEP 3: Extract data from chart
    extract_result = await extract_chart_data(first_mrn)
    assert extract_result["status"] == "SUCCESS"
    raw_data = extract_result["raw_data"]
    print(f"✓ Step 3: Extracted {len(raw_data)} clinical fields")

    # STEP 4: Verify data is cached (as an encrypted token tuple) and raw_data is valid
    assert first_mrn in CHART_DATA_CACHE
    cached_entry = CHART_DATA_CACHE[first_mrn]
    assert isinstance(cached_entry, tuple) and len(cached_entry) == 2
    cached_token, _ = cached_entry
    assert isinstance(cached_token, str) and len(cached_token) > 0
    # Validate raw_data (returned in response) contains expected fields
    assert "demographics" in raw_data
    assert "vitals" in raw_data
    assert raw_data["vitals"]["bmi"] > 0
    print(f"✓ Step 4: Encrypted token cached; raw_data ready for Ollama anonymization")

    print(f"\n✓ Complete RPA flow succeeded: schedule → open_chart → extract_data → cache")


@pytest.mark.asyncio
async def test_rpa_flow_identifies_sleep_apnea_candidate(monkeypatch):
    """
    Test that extracted data shows clear indicators for sleep apnea testing.
    This simulates the data that will be sent to Ollama for eligibility checking.
    """
    from mcp_servers.ecw_bridge.server import extract_chart_data
    
    result = await extract_chart_data("MRN-SLEEP-TEST")
    raw_data = result["raw_data"]
    
    # Verify sleep apnea indicators are present
    sleep_apnea_indicators = []
    
    # Check 1: BMI > 30
    if raw_data["vitals"]["bmi"] > 30:
        sleep_apnea_indicators.append("BMI > 30")
    
    # Check 2: Snoring mentioned
    if "snoring" in raw_data["hpi"].lower():
        sleep_apnea_indicators.append("Snoring in HPI")
    
    # Check 3: Fatigue/daytime sleepiness
    if "fatigue" in raw_data["chief_complaint"].lower() or "fatigue" in raw_data["hpi"].lower():
        sleep_apnea_indicators.append("Fatigue/Daytime Sleepiness")
    
    # Check 4: Hypertension
    if any("hypertension" in str(item).lower() for item in raw_data["pmh"]):
        sleep_apnea_indicators.append("Hypertension (HTN)")
    
    assert len(sleep_apnea_indicators) >= 3, f"Expected 3+ sleep apnea indicators, got: {sleep_apnea_indicators}"
    print(f"✓ Patient has sleep apnea indicators: {sleep_apnea_indicators}")


@pytest.mark.asyncio
async def test_rpa_flow_complete_approval_workflow(monkeypatch):
    """
    Test the complete user approval workflow:
    1. Data extracted from eCW
    2. User approves recommendation in dashboard
    3. Order is automatically pended in eCW
    """
    from mcp_servers.ecw_bridge.server import (
        extract_chart_data, approve_recommendation, pend_order
    )
    from unittest.mock import MagicMock
    import sys

    mock_pag = MagicMock()
    monkeypatch.setitem(sys.modules, "pyautogui", mock_pag)

    import time
    monkeypatch.setattr(time, "sleep", lambda *a: None)
    
    # STEP 1: Extract data
    extract_result = await extract_chart_data("MRN-APPROVAL-TEST")
    assert extract_result["status"] == "SUCCESS"
    print(f"✓ Step 1: Data extracted")
    
    # STEP 2: User approves recommendation
    approve_result = await approve_recommendation("v-9a1b-approval-test")
    assert approve_result["status"] == "SUCCESS"
    assert approve_result["action"] == "ORDER_PENDED"
    print(f"✓ Step 2: User approved recommendation")
    
    # STEP 3: Order is pended
    order_result = await pend_order("95800", "G47.33", "MRN-APPROVAL-TEST", "approval-token-valid")
    assert order_result["status"] == "SUCCESS"
    assert order_result["order_details"]["cpt"] == "95800"
    print(f"✓ Step 3: Order pended in eCW")
    
    print(f"\n✓ Complete approval workflow succeeded")
