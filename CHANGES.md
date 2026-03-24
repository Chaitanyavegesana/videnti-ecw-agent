# Videnti ECW Agent — Changes & Status

> **Branch:** `copilot/create-rpa-agent-architecture`
> **Base:** `Feature-03052026-EOD`
> **Date:** March 2026

---

## 1. New Features & Changes

### 1.1 Chrome Extension — DOM-Based Data Extraction

A full Manifest V3 Chrome Extension (`chrome-extension/`) replaces fragile
pixel-level OCR with direct DOM reading.

| File | What it does |
|------|-------------|
| `manifest.json` | MV3 manifest; `all_frames: true` injects into every eCW iframe |
| `content_script.js` | Reads demographics, vitals, PMH, medications, allergies, labs, HPI, and assessment directly from the live DOM |
| `background.js` | Persistent service-worker; maintains WebSocket to `ws://localhost:8001/ws/extension`; exponential back-off (`RECONNECT_BACKOFF_MULTIPLIER = 1.5`); pending message queue capped at `PENDING_QUEUE_MAX = 50` |
| `popup.html / popup.js` | Live connection-status badge; manual "Extract Now" buttons for schedule and chart |

**What the content script extracts from eCW:**

```
demographics  → name, DOB, MRN, sex, age
vitals        → height, weight, BMI, blood pressure, HR, temperature
pmh           → problem list / past medical history
medications   → active medication list
allergies     → allergy list
chief_complaint, HPI, assessment
recent_labs   → lab result rows
```

---

### 1.2 Hybrid Architecture in `mcp-servers/ecw-bridge/server.py`

The ecw-bridge now operates in **two modes** for `get_schedule` and
`extract_chart_data`:

```
Mode A — Chrome Extension (preferred)
  Extension connected?  YES →  send command to extension over WebSocket
                               wait up to 10 s for DOM data to arrive
                               return real patient data

Mode B — PyAutoGUI RPA (fallback)
  Extension connected?  NO  →  launch screen-level automation
                               (mock data returned in development)
```

**New HTTP endpoints** (consumed by the dashboard):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/login-status` | GET | Returns `{ is_active, login_time, last_check }` — polled every 10 s by `LoginStatusBanner` |
| `/login-complete` | POST | Called when the user confirms manual Cloudflare login |
| `/session-check` | GET | Lightweight health check for the active eCW session |
| `/health` | GET | Returns server status + active extension connection count |

**WebSocket bridge** at `ws://localhost:8001/ws/extension`:

| Message direction | Message type | Description |
|------------------|-------------|-------------|
| Extension → Server | `schedule_data` | Pushes appointment list into `_schedule_queue` |
| Extension → Server | `chart_data` | Pushes patient snapshot into `_chart_queue` |
| Extension → Server | `frame_ready` | Reports which eCW screen is loaded |
| Extension → Server | `error` | Propagates extraction errors to server log |
| Server → Extension | `request_schedule` | Triggers schedule extraction |
| Server → Extension | `request_chart` | Triggers chart extraction for a given MRN |
| Server → Extension | `pend_order` | Forwards order-pend request to popup for user confirmation |

---

### 1.3 PHI Encryption — `phi_crypto.py`

New module providing HIPAA-compliant in-memory protection:

| Function | Description |
|----------|-------------|
| `encrypt_phi(plaintext)` | AES-256-GCM; random 96-bit nonce per call; returns Base64 `<nonce ‖ ciphertext+tag>` |
| `decrypt_phi(token)` | Validates GCM authentication tag; raises `ValueError` on any tampering |
| `encrypt_snapshot(dict)` | JSON-serialises a snapshot dict then encrypts it |
| `decrypt_snapshot(token)` | Decrypts and deserialises a snapshot token |
| `deidentify_text(str)` | Regex-strips the 18 HIPAA Safe Harbor identifiers (`[NAME]`, `[DATE]`, `[SSN]`, `[PHONE]`, `[ZIP]`, `[EMAIL]`, `[MRN]`, `[ID]`) |
| `deidentify_snapshot(dict)` | Recursively de-identifies all string leaves in a nested dict/list; preserves numeric leaves (vitals) |
| `mrn_to_snapshot_id(mrn)` | One-way SHA-256 HMAC → 8-char hex prefixed `v-`; emits `UserWarning` when `ICS_MRN_SALT` is missing |

**In-memory chart cache** (`CHART_DATA_CACHE`):
- Raw PHI is **never** stored in plaintext.
- Each entry is an `(AES-256-GCM ciphertext, inserted_at)` tuple.
- TTL: **1 hour** (`_CACHE_TTL_SECONDS = 3600`).
- Hard cap: **200 entries** (`_CACHE_MAX_ENTRIES = 200`); oldest evicted first.

---

### 1.4 React Dashboard Improvements

| Component | Change |
|-----------|--------|
| `LoginStatusBanner.jsx` | New component — polls `/login-status` every 10 s; shows warning banner when eCW session is inactive; "I've Logged In" button calls `/login-complete` |
| `LoginStatusBanner.css` | Matching styles (green success / amber warning) |
| `AuditLogPage.jsx` | Audit log viewer — reads `logs/audit.jsonl` entries via backend |
| `SettingsPage.jsx` | Credential management UI — calls `save_credentials` MCP tool |
| `App.jsx` | Wires `LoginStatusBanner` into the header of every page |

---

### 1.5 `visual_driver.py` — Lazy PyAutoGUI Imports

`import pyautogui` was at the **top level**, causing `KeyError: 'DISPLAY'` in
headless CI environments.  The import is now **inside** the two functions that
need a display:

```python
def navigate_to_schedule():
    import pyautogui as pag   # ← moved here

def get_schedule_snapshot():
    import pyautogui as pag   # ← moved here
```

The same lazy-import pattern was applied to `open_chart` and `pend_order`
inside the ecw-bridge server.

---

### 1.6 `.gitignore` Fix — Inline Comments

Git does **not** support inline `pattern  # comment` syntax; patterns with
inline comments were being matched literally, so `.env` was accidentally
tracked.  All inline comments were split onto their own lines:

```diff
- .env  # Contains eCW credentials
+ # Contains eCW credentials
+ .env
```

`.env` was also removed from the Git index (`git rm --cached .env`).

---

### 1.7 `mcp_servers/` Symlink Replacement

The `mcp_servers/` directory contained broken symlinks pointing to
`/Users/chaitanya/…` (absolute paths from the original developer's Mac).
These were replaced with real file copies so the project works on any
machine.

---

### 1.8 New Tests (24 added)

| Test file | Count | Covers |
|-----------|-------|--------|
| `tests/test_phi_crypto.py` | 16 | encrypt/decrypt round-trip, unique nonces, wrong-key rejection, tampered-token rejection, HIPAA de-identification (names, dates, SSN, email, MRN), snapshot de-identification, numeric vital preservation, `mrn_to_snapshot_id` format/determinism/uniqueness/one-way |
| `tests/test_extension_bridge.py` | 8 | `is_extension_connected`, WebSocket handler (schedule queue, chart queue, ACK, disconnect cleanup), `get_schedule` extension path, `extract_chart_data` extension path |

`tests/test_ecw_bridge.py` was updated to mock `pyautogui` via `sys.modules`
instead of a direct import patch, preventing `KeyError: 'DISPLAY'` in CI.

---

## 2. How the Overall Flow Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AUTOMATED (7:30 AM daily)                     │
└─────────────────────────────────────────────────────────────────────┘

  main.py (Orchestrator)
      │
      ▼
  get_schedule()  ──────────────────────────────────────────────────────┐
      │                                                                  │
      │  Chrome Extension connected?                                     │
      │  YES → send "request_schedule" via WebSocket                     │
      │        wait ≤ 10 s for schedule_data from extension              │
      │  NO  → PyAutoGUI RPA navigates eCW schedule screen              │
      │                                                                  │
      ▼  [{ mrn, time, provider, visitType }, ...]                       │
                                                                         │
  For each appointment:                                                  │
      │                                                                  │
      ▼                                                                  │
  open_chart(mrn)                                                        │
      │  Extension connected? → request navigation via WS               │
      │  No extension?        → PyAutoGUI types MRN, presses Enter      │
      │                                                                  │
      ▼                                                                  │
  extract_chart_data(mrn)                                                │
      │  Extension connected? → send "request_chart"; wait ≤ 10 s      │
      │         content_script.js reads DOM → background.js → WS       │
      │  No extension?        → PyAutoGUI RPA mock (real screen later)  │
      │                                                                  │
      │  Result encrypted with AES-256-GCM and stored in cache          │
      │                                                                  │
      ▼  { demographics, vitals, pmh, medications, allergies, labs, … } │
                                                                         │
  summarize_phi()   [Ollama MCP Server :8000]                           │
      │  Strips 18 HIPAA identifiers                                     │
      │  Generates anonymised clinical summary                           │
      │  Returns snapshot_id (UUID, NOT traceable to MRN)               │
      │                                                                  │
      ▼  { snapshot_id, clinical_summary, phi_stripped: true }          │
                                                                         │
  validate_eligibility()   [Ollama MCP Server :8000]                    │
      │  Local LLM (medgemma/deepseek/llama) evaluates:                 │
      │    • Home Sleep Test (BMI > 30, snoring, fatigue)               │
      │    • EEG (seizures, syncope, loss of consciousness)             │
      │    • Allergy Panel (chronic rhinitis, asthma)                   │
      │                                                                  │
      ▼  [{ test: "HST", confidence: 0.94 }, ...]                       │
                                                                         │
  Dashboard displays recommendation ◄────────────────────────────────────┘
  http://localhost:5173
      │
      │  Clinician sees:
      │    Snapshot v-9a1b | MRN-7721 | Home Sleep Test | 94% | Pending
      │    [Approve]  [Dismiss]
      │
      ▼

┌─────────────────────────────────────────────────────────────────────┐
│                        MANUAL (clinician action)                     │
└─────────────────────────────────────────────────────────────────────┘

  Clinician clicks [Approve]
      │
      ▼
  approve_recommendation(snapshot_id)   [eCW Bridge :8001]
      │  Looks up encrypted snapshot in cache → decrypts → retrieves MRN
      │  Writes audit entry to logs/audit.jsonl
      │
      ▼
  pend_order(cpt_code, icd_code, mrn, approval_token)
      │  Security check: approval_token ≥ 10 chars
      │  PyAutoGUI types CPT code (e.g. 95800)
      │  PyAutoGUI types ICD-10 code (e.g. G47.33)
      │  PyAutoGUI presses Enter
      │
      ▼
  ✅ Order is now PENDING in eCW for provider signature

  Clinician clicks [Dismiss]
      │
      ▼
  dismiss_recommendation(snapshot_id)
      │  Audit entry written — no order placed
      ▼
  ✅ Dismissal logged
```

### Component Port Map

| Service | Port | Tech |
|---------|------|------|
| Ollama MCP Server | 8000 | FastMCP + Ollama |
| eCW Bridge MCP Server | 8001 | FastMCP + Starlette + WebSocket |
| Search MCP Server | 8002 | FastMCP |
| React Dashboard | 5173 | Vite + React |
| Ollama LLM Runtime | 11434 | Ollama |

### Data-Residency Guarantee

All data flows **locally only**:

```
eCW browser page
  └─→ content_script.js (DOM read)
        └─→ background.js (service worker)
              └─→ ws://localhost:8001  (never leaves machine)
                    └─→ phi_crypto.py (encrypt before caching)
                          └─→ Ollama @ localhost:11434 (local LLM)
                                └─→ Dashboard @ localhost:5173
```

No patient data is transmitted to any remote server at any stage.

---

## 3. What Is Pending

### 3.1 Critical / Blockers

| # | Item | Details |
|---|------|---------|
| P1 | **Real eCW RPA coordinate calibration** | `ANCHOR_MAP` in `visual_driver.py` uses placeholder coordinates `(800,300)`, `(850,350)`, etc. These must be calibrated against the actual eCW instance screen layout using `logs/anchors/anchor_map.json`. |
| P2 | **Live Ollama model** | Ollama is not installed in the current environment. Install Ollama and pull a model: `ollama pull medgemma:27b` (or `deepseek-r1:14b`). Without this, `summarize_phi` and `validate_eligibility` will fail in production. |
| P3 | **Chrome Extension selector validation** | CSS selectors in `content_script.js` (e.g. `tr.appt-row`, `[data-vital='bmi']`) were written against a generic eCW DOM and may not match the exact build/version used in your clinic. Each selector family needs smoke-testing against the real eCW UI. |
| P4 | **`.env` / production secrets** | `.env` is now git-ignored. It must be created on each deployment with real values: `ECW_URL`, `ECW_USERNAME`, `ECW_PASSWORD`, `ECW_CLINIC_ID`, `ICS_MRN_SALT`, `OLLAMA_BASE_URL`. |

---

### 3.2 High Priority

| # | Item | Details |
|---|------|---------|
| H1 | **`approve_recommendation` → `pend_order` wiring** | `approve_recommendation()` currently returns a success stub but does **not** yet call `pend_order()`. The lookup of the cached snapshot (to retrieve MRN) and the automatic order-penning call must be wired in. |
| H2 | **Cloudflare / MFA login automation** | `ecw_login.py` and `session_monitor.py` exist but the Cloudflare-protected login flow is not fully automated. See `CLOUDFLARE_LOGIN_FIX_PLAN.md`. The `LoginStatusBanner` provides a manual workaround (user clicks "I've Logged In"). |
| H3 | **Search MCP integration** | `mcp-servers/search-mcp/server.py` provides `scan_repo` and `fetch_medical_guidelines` tools but the orchestrator only calls Ollama and eCW-bridge. Weekly guideline sync is stubbed in `main.py` but not yet consuming real LCD/CMS data. |
| H4 | **Approval token issuance** | `pend_order` requires an `approval_token` of ≥ 10 characters, but there is no UI flow that generates or distributes this token. A token generation/validation mechanism (e.g. time-based OTP) needs to be designed and implemented. |

---

### 3.3 Medium Priority (Dashboard & UX)

| # | Item | Details |
|---|------|---------|
| M1 | **Live data in dashboard** | Stats cards (Total Scans, Revenue Identified, etc.) and the recommendation queue use hard-coded `MOCK_STATS` / `MOCK_QUEUE` arrays. These need to be driven by real API calls to the eCW Bridge. |
| M2 | **Audit log backend endpoint** | `AuditLogPage.jsx` exists but the backend endpoint that serves `logs/audit.jsonl` content to the dashboard has not been added to `build_app()`. |
| M3 | **Patient search by MRN** | The dashboard has no free-form search. Clinicians need to look up a patient manually to trigger a chart extraction outside the daily pipeline. |
| M4 | **Real-time MCP status** | Server health badges (Ollama, eCW Bridge, Search MCP) are hard-coded as "Online". They need to poll real health endpoints. |
| M5 | **Recommendation rationale** | AI confidence values are shown without supporting evidence. The dashboard should display which clinical indicators triggered the recommendation (e.g. "BMI 30.8 + snoring + fatigue → HST"). |

---

### 3.4 Lower Priority / Future Work

| # | Item | Details |
|---|------|---------|
| L1 | **Persistent audit database** | Currently audit entries are appended to a flat `logs/audit.jsonl` file. For compliance and analytics, this should be migrated to a local SQLite database. |
| L2 | **End-to-end integration tests against staging eCW** | All tests currently run against mocks. A staging-eCW test suite is needed before any production deployment. |
| L3 | **PyAutoGUI → WebDriver fallback** | PyAutoGUI is screen-position brittle. For order penning, a Selenium/ChromeDriver approach that targets eCW DOM elements directly would be more reliable. |
| L4 | **Multi-provider support** | The schedule pipeline processes one provider. Multi-provider clinics need parameterisation. |
| L5 | **iOS / remote access support** | The Chrome Extension requires Chrome running locally. Remote desktop or thin-client setups are not yet addressed. |
| L6 | **Dashboard production build** | `dashboard/` is currently run with `npm run dev`. A `npm run build` + static-file serving setup is needed for production. |
| L7 | **Dependency versions pinned** | `requirements.txt` / `pyproject.toml` does not pin exact versions. This should be locked before production deployment to prevent silent breakages. |

---

## Quick-Start Checklist

```bash
# 1. Create .env from template
cp .env.example .env          # (create .env.example if it does not exist)
# Fill in: ECW_URL, ECW_USERNAME, ECW_PASSWORD, ECW_CLINIC_ID, ICS_MRN_SALT

# 2. Install Python dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # (or pyproject.toml)

# 3. Install and start Ollama
# Download from https://ollama.com/
ollama pull medgemma:27b
ollama serve &

# 4. Start all MCP servers
bash start_services.sh

# 5. Start the dashboard
cd dashboard && npm install && npm run dev

# 6. Load the Chrome Extension
# Chrome → More tools → Extensions → Load unpacked → select chrome-extension/

# 7. Run tests
python -m pytest tests/ -v --timeout=30
```
