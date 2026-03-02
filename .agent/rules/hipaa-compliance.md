# HIPAA Compliance Guardrails — Videnti Clinical AI
# Version: 1.0.0 | Effective: 2026-02-28

## RULE 1: PHI MUST NEVER LEAVE THE LOCAL ENVIRONMENT
Raw Protected Health Information (PHI) must NEVER be transmitted to any cloud-based API.

## RULE 2: LOCAL-ONLY PROCESSING PIPELINE
All PHI must be anonymized by the `ollama-server` before leaving the local machine.

## RULE 3: DATA RESIDENCY
Patient data resides only on the clinic's local machine or approved on-premise server.

## RULE 4: MINIMUM NECESSARY
Access only the clinical data needed for the diagnostic scan (Vitals, PMH, Notes).

## RULE 5: AUDIT TRAIL
Every action involving PHI or order pending must be logged locally to `logs/audit.jsonl` with a `snapshot_id`.
