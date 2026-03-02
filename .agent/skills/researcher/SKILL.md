---
name: researcher
description: >
  Monitors medical coding repositories, CMS/LCD databases, and FDA guideline sources
  for CPT/ICD code updates and clinical coverage policy changes. Feeds updated
  guidelines back into the agent's local Rulebook (./guidelines/current_rules.md).
---

# Researcher Skill — Medical Coding & Guidelines Monitor

## Purpose
This skill keeps the Videnti Clinical AI current with evolving medical billing regulations,
Local Coverage Determinations (LCDs), and clinical practice guidelines. It uses the
`search-mcp` server locally for GitHub searches and internet-based guideline fetching.
All research is unauthenticated — no PHI is involved in this skill.

## MCP Server Backend
- **Server**: `mcp-servers/search-mcp/server.py`
- **Endpoint**: `http://localhost:8002`
- **Protocol**: MCP over HTTP (FastMCP)
- **External APIs**: GitHub REST API, CMS LCD Database, FDA Drug Database

---

## TOOLS

### `scan_repo(url: str, keywords: list[str] = None) -> dict`
**Description**: Analyzes a GitHub repository for CPT/ICD code changes, policy amendments,
or updated billing guidelines. Uses the GitHub REST API to search commits, issues, and
file diffs.

**Parameters**:
- `url`: Full GitHub repository URL (e.g., `https://github.com/cms-gov/lcd-updates`).
- `keywords`: Optional list of search terms (e.g., `["HST", "95800", "G47.33", "sleep apnea"]`).
  Defaults to the master keyword list in `./guidelines/watch_keywords.json`.

**Returns**:
```json
{
  "repo_url": "https://github.com/...",
  "last_commit_date": "2026-01-15",
  "changes_detected": true,
  "relevant_changes": [
    {
      "file": "LCD_L33295_HST.md",
      "change_type": "AMENDMENT",
      "summary": "Updated BMI threshold from ≥30 to ≥27 for HST eligibility",
      "effective_date": "2026-04-01",
      "diff_url": "https://github.com/.../commit/abc123"
    }
  ]
}
```

**Priority Repositories to Monitor**:
```
https://github.com/CMSgov/beneficiary-fhir-data      # CMS billing data
https://github.com/CMSgov/dpc-app                     # Data at Point of Care
https://github.com/HL7/FHIR                            # FHIR coding standards
https://github.com/cqframework/clinical_quality_language  # CQL logic updates
https://www.cms.gov/medicare-coverage-database          # LCD portal (scraped)
```

---

### `summarize_guidelines(topic: str, year: int = None) -> str`
**Description**: Returns a structured markdown summary of the latest clinical coverage
requirements for a specific diagnostic test or condition.

**Parameters**:
- `topic`: Clinical topic (e.g., "Sleep Apnea HST", "EEG Seizure", "Allergy Testing").
- `year`: Optional year filter (defaults to current year).

**Returns**: Markdown-formatted string with:
- Current CPT codes and reimbursement rates
- ICD-10 codes that qualify for coverage
- LCD/NCD references with effective dates
- Required documentation elements
- Lookback period rules

**Data Sources**:
1. CMS LCD Database (`https://www.cms.gov/medicare-coverage-database`)
2. AMA CPT code changes (annual, published October)
3. AAP/AAO/AASM clinical practice guidelines
4. FDA drug/device approval updates (for relevant diagnostic equipment)

**Example Call**:
```python
summary = await researcher.summarize_guidelines("Sleep Apnea HST", year=2026)
# Returns: Full markdown with G47.3x codes, LCD L33295 requirements, etc.
```

---

### `fetch_lcd_updates(lcd_numbers: list[str]) -> list[dict]`
**Description**: Directly polls the CMS Medicare Coverage Database for updates to
specific LCD numbers.

**Parameters**:
- `lcd_numbers`: List of LCD identifiers (e.g., `["L33295", "L34950", "L35010"]`).

**Returns**: List of LCD status objects:
```json
[
  {
    "lcd_number": "L33295",
    "title": "Home Sleep Tests (HST)",
    "status": "Active",
    "last_updated": "2025-11-01",
    "effective_date": "2025-12-01",
    "changes_since_last_check": ["BMI criteria clarified", "New documentation requirement added"],
    "full_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=33295"
  }
]
```

**LCDs to Monitor**:
- `L33295` — Home Sleep Testing (HST)
- `L34950` — Electroencephalogram (EEG)
- `L35010` — Allergy Testing
- `L33797` — Continuous Positive Airway Pressure (CPAP)

---

### `update_rulebook(guidelines_markdown: str, source: str) -> bool`
**Description**: Writes updated clinical guidelines to the local rulebook file and
logs the change for audit purposes.

**Parameters**:
- `guidelines_markdown`: The new guideline content to merge into the rulebook.
- `source`: Citation string (e.g., "CMS LCD L33295, updated 2026-01-15").

**Returns**: `true` if rulebook updated successfully.

**Side Effects**:
- Overwrites relevant sections of `./guidelines/current_rules.md`.
- Appends a change log entry to `./logs/guideline_updates.jsonl`:
  ```json
  { "timestamp": "2026-02-28T08:00:00-05:00", "source": "CMS LCD L33295", "updated_rules": ["HST BMI threshold"] }
  ```

---

## SCHEDULED EXECUTION

This skill runs on a weekly schedule:

```
SCHEDULE: Every Monday at 08:00 AM (clinic local time)
TRIGGER: main.py → scheduler.run_weekly_research()
WORKFLOW:
  1. scan_repo() for all priority repositories
  2. fetch_lcd_updates(["L33295", "L34950", "L35010", "L33797"])
  3. summarize_guidelines() for each monitored topic
  4. update_rulebook() if changes detected
  5. Log completion to ./logs/research_runs.jsonl
  6. Alert agent via internal message: "Rulebook updated. Re-validate clinical logic."
```

## WATCH KEYWORDS (./guidelines/watch_keywords.json)
```json
{
  "cpt_codes": ["95800", "95801", "95806", "95807", "95816", "95819", "95953", "95004", "95024", "95165"],
  "icd_codes": ["G47.30", "G47.31", "G47.33", "G40.x", "J30.x", "J45.x", "E11.9", "I10"],
  "topics": ["home sleep test", "polysomnography", "EEG", "allergy panel", "CPAP", "sleep apnea", "seizure"],
  "lcd_numbers": ["L33295", "L34950", "L35010", "L33797"],
  "sources": ["CMS", "AMA", "AASM", "AAP", "FDA"]
}
```
