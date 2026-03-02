---
name: rpa-driver
description: >
  Controls the eClinicalWorks (eCW) EMR system via the local ecw-bridge MCP server.
  Uses PyAutoGUI-backed tools to navigate the EMR UI, extract patient data, and
  pend diagnostic orders — all without exposing PHI to cloud APIs.
---

# RPA Driver Skill — eCW Automator

## Purpose
This skill is the primary interface between the Videnti Clinical AI agent and the
eClinicalWorks EMR. It communicates exclusively with the `ecw-bridge` MCP server
running locally at `http://localhost:8001`. All actions are performed via screen
actuation using PyAutoGUI on the clinic workstation.

## MCP Server Backend
- **Server**: `mcp-servers/ecw-bridge/server.py`
- **Endpoint**: `http://localhost:8001`
- **Protocol**: MCP over HTTP (FastMCP)
- **Security**: Local-only, no internet exposure

---

## TOOLS

### `get_daily_appointments(date: str = "today") -> list[dict]`
**Description**: Retrieves the full provider schedule from the eCW appointment screen.

**Parameters**:
- `date`: ISO date string (YYYY-MM-DD). Defaults to today. Accepts "today" or "tomorrow".

**Returns**: A list of appointment objects:
```json
[
  {
    "appointment_id": "APT-20260228-001",
    "time_slot": "09:00",
    "patient_mrn": "MRN-XXXXX",
    "provider_npi": "1234567890",
    "visit_type": "Established Patient Office Visit",
    "duration_minutes": 15
  }
]
```

**Execution Steps** (internal to ecw-bridge):
1. Navigate to eCW Provider Schedule view.
2. Locate the date column matching `date` parameter.
3. Scrape all appointment rows using PyAutoGUI + OCR (pytesseract).
4. Return structured JSON.

**HIPAA Note**: `patient_mrn` is included here but will be mapped to `snapshot_id`
before leaving the local environment.

---

### `open_chart(patient_mrn: str) -> bool`
**Description**: Opens the patient's chart in eCW by navigating to the chart via MRN.

**Parameters**:
- `patient_mrn`: The medical record number of the patient.

**Returns**: `true` if chart opened successfully, `false` otherwise.

**Execution Steps**:
1. Click the eCW "Patient Lookup" field.
2. Type the MRN using `pyautogui.typewrite()`.
3. Press Enter and wait for chart to load (confirmed by UI element detection).
4. Return success status.

**Error Handling**: If chart not found after 3 retries, invoke `Self-Healing` protocol —
capture screenshot and use template matching to re-locate the search field.

---

### `extract_snapshot(patient_mrn: str) -> dict`
**Description**: Extracts a structured clinical snapshot from an open patient chart.
Captures: Vitals, Past Medical History (PMH), Active Medications, Recent Notes,
and Problem List.

**Parameters**:
- `patient_mrn`: MRN of the currently open chart.

**Returns**: Raw structured snapshot (pre-anonymization):
```json
{
  "snapshot_id": null,
  "vitals": { "bmi": 32.4, "bp": "140/90", "weight_lbs": 210 },
  "pmh": ["Hypertension", "Type 2 Diabetes", "Snoring"],
  "medications": ["Metformin 500mg", "Lisinopril 10mg"],
  "notes_summary": "Patient complains of daytime fatigue and snoring...",
  "problem_list": ["E11.9", "I10", "G47.31"],
  "last_orders": [
    { "cpt": "95800", "date": "2024-08-15", "status": "Completed" }
  ]
}
```

**Post-Extraction**: Immediately pass this output to `Local_Privacy_Guard.summarize_phi()`
before storing or transmitting anywhere.

---

### `pend_order(cpt_code: str, icd_code: str, patient_mrn: str, approval_token: str) -> dict`
**Description**: Executes the diagnostic order pend workflow in eCW. Requires a valid
human approval token from the Videnti Dashboard.

**Parameters**:
- `cpt_code`: The CPT procedure code (e.g., "95800").
- `icd_code`: The ICD-10 diagnosis code (e.g., "G47.30").
- `patient_mrn`: Patient's MRN.
- `approval_token`: UUID token issued by the Videnti Dashboard after physician approval.

**Returns**:
```json
{
  "status": "PENNED" | "FAILED" | "PENDING_APPROVAL",
  "order_id": "ORD-XXXXX",
  "timestamp": "2026-02-28T09:15:00-05:00",
  "cpt_code": "95800",
  "icd_code": "G47.30"
}
```

**Execution Steps**:
1. Validate `approval_token` against local token store.
2. Open patient chart via `open_chart()`.
3. Navigate to "Orders" tab in eCW.
4. Click "New Order", enter CPT code.
5. Attach diagnosis code, confirm provider NPI auto-populated.
6. Click "Pend Order" (NOT "Sign" — physician must sign).
7. Capture confirmation dialog and extract order ID.
8. Log action to `./logs/audit.jsonl`.

**HIPAA Critical**: If `approval_token` is invalid or missing, return `PENDING_APPROVAL`
and DO NOT execute any UI actions.

---

### `capture_screenshot(label: str) -> str`
**Description**: Captures a screenshot for self-healing or audit purposes.

**Parameters**:
- `label`: A descriptive label (e.g., "button_not_found", "mfa_prompt").

**Returns**: Relative file path to saved screenshot (e.g., `./logs/screenshots/2026-02-28_button_not_found.png`).

---

## USAGE EXAMPLE

```python
# Typical workflow for a single patient
appointments = await rpa_driver.get_daily_appointments(date="today")

for apt in appointments:
    await rpa_driver.open_chart(apt["patient_mrn"])
    raw_snapshot = await rpa_driver.extract_snapshot(apt["patient_mrn"])

    # Hand off to Local_Privacy_Guard before any further processing
    anonymized = await privacy_guard.summarize_phi(raw_snapshot)

    # Then send anonymized data to clinical logic validator
    result = await privacy_guard.validate_eligibility(anonymized, rule_set="speed_play")
```

## SELF-HEALING PROTOCOL
If a UI element is not found:
1. Call `capture_screenshot("element_not_found")`.
2. Use PyAutoGUI's `locateOnScreen()` with alternative template images.
3. Retry up to 3 times with exponential backoff (1s, 2s, 4s).
4. If all retries fail: log `ELEMENT_NOT_FOUND` error and notify agent to skip this patient.
