---
name: privacy-guard
description: >
  Bridge to local Ollama inference for PHI anonymization and eligibility validation.
  Ensures NO raw patient data leaves the local environment. Uses DeepSeek-R1 or
  MedGemma for clinical-grade local reasoning.
---

# Privacy Guard Skill — Local PHI Processing

## Purpose
This skill acts as the HIPAA compliance enforcement layer between raw eCW data and
the cloud planning agent. It runs exclusively on the local `ollama-server` MCP, using
medically fine-tuned language models to anonymize PHI and validate clinical eligibility —
all without internet connectivity.

## MCP Server Backend
- **Server**: `mcp-servers/ollama-server/server.py`
- **Endpoint**: `http://localhost:8000`
- **Ollama Base**: `http://localhost:11434`
- **Preferred Models**: `deepseek-r1:14b` | `medgemma:27b` | `llama3.3:70b-q4` | `qwen2.5:14b`

---

## TOOLS

### `summarize_phi(raw_snapshot: dict) -> dict`
**Description**: Strips all 18 HIPAA-defined identifiers from a raw patient snapshot
and returns an anonymized clinical summary. Assigns a `snapshot_id` for tracking.

**Parameters**:
- `raw_snapshot`: The raw dictionary returned by `rpa_driver.extract_snapshot()`.

**Returns**:
```json
{
  "snapshot_id": "a3f8b2c1-4d5e-6789-abcd-ef0123456789",
  "anonymized_summary": "Adult male patient, BMI 32.4, HTN, T2DM, reports snoring and daytime fatigue. No prior HST on record.",
  "risk_flags": ["BMI_over_30", "HYPERTENSION", "T2DM", "SNORING", "FATIGUE"],
  "last_orders_summary": "No sleep study in past 12 months",
  "phi_stripped": true,
  "model_used": "deepseek-r1:14b"
}
```

**Prompt Template** (sent to Ollama):
```
You are a clinical data anonymizer. Given the following patient snapshot, remove ALL
personally identifiable information (names, MRNs, DOBs, addresses, phone numbers,
insurance IDs) and return only a clinical summary suitable for diagnostic decision-making.
Extract and list any risk flags relevant to sleep apnea, seizure disorders, or allergic disease.

Patient Snapshot:
{raw_snapshot_json}

Return JSON with fields: anonymized_summary, risk_flags, last_orders_summary, phi_stripped.
```

---

### `validate_eligibility(summary: dict, rule_set: str) -> dict`
**Description**: Determines if the anonymized patient qualifies for specific diagnostic
tests based on the current clinical logic rules.

**Parameters**:
- `summary`: The anonymized summary dict from `summarize_phi()`.
- `rule_set`: Name of rule set to apply (e.g., `"speed_play"`, `"hst_only"`, `"eeg_only"`).

**Returns**:
```json
{
  "snapshot_id": "a3f8b2c1-...",
  "qualified_tests": [
    {
      "test": "HST",
      "cpt_code": "95800",
      "primary_icd": "G47.30",
      "qualifying_factors": ["BMI_over_30", "SNORING", "FATIGUE"],
      "suppressed": false,
      "suppression_reason": null,
      "confidence_score": 0.94,
      "recommendation": "RECOMMEND_ORDER"
    }
  ],
  "model_used": "deepseek-r1:14b",
  "rule_set_version": "2026-02-28"
}
```

**Confidence Thresholds**:
- `≥ 0.80` → `RECOMMEND_ORDER` (send to dashboard)
- `0.60–0.79` → `PHYSICIAN_REVIEW` (flag for manual check)
- `< 0.60` → `SUPPRESS` (do not recommend)

---

### `check_suppression(snapshot_id: str, test_type: str) -> dict`
**Description**: Applies the 12-month lookback suppression logic to determine if a
test should be blocked despite the patient otherwise qualifying.

**Parameters**:
- `snapshot_id`: The anonymized patient snapshot ID.
- `test_type`: One of `"HST"`, `"EEG"`, `"ALLERGY"`.

**Returns**:
```json
{
  "suppressed": true,
  "reason": "HST completed 2024-08-15 (within 12-month lookback window)",
  "suppression_expires": "2025-08-15",
  "days_remaining": 168
}
```

---

## MODEL SELECTION LOGIC

The skill selects the best available local model in this priority order:

```python
MODEL_PRIORITY = [
    "medgemma:27b",     # Best for clinical Q&A and HIPAA-sensitive reasoning
    "deepseek-r1:14b",  # Best for complex multi-step clinical logic
    "llama3.3:70b-q4",  # High-fidelity instruction following
    "qwen2.5:14b",      # Best for structured JSON output
    "deepseek-r1:7b",   # Fallback if GPU VRAM is limited
]
# Selected via: ollama list → pick best available from priority list
```
