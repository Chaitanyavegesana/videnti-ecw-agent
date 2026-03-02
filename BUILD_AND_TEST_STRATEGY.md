# Videnti ECW Agent: Build & Test Strategy
**Last Updated:** February 28, 2026

## Overview
This document outlines a phased approach to building Videnti, with each phase being **independently testable** before moving to the next.

---

## Phase 1: Unit Tests (No External Dependencies) ✅
**Goal:** Validate core logic in isolation using mocks.

### Tasks
- [x] `test_ecw_bridge.py`: Token validation, credential saving (no RPA)
- [x] `test_ollama_mcp.py`: Snapshot ID generation, eligibility logic (no Ollama server)
- [x] `test_search_mcp.py`: Guidelines fetch, error handling (no GitHub API)

### Run Command
```bash
pytest tests/ -v -m "not integration"
```

### Expected Status
All tests should pass without any external services running.

---

## Phase 2: Server Startup Tests ⏳
**Goal:** Each MCP server can start and respond to HTTP requests.

### Tasks
- [ ] **Task 2.1**: Test eCW Bridge server startup on port 8001
  - Verify FastMCP ASGI app starts
  - Test `/tools/open_chart` endpoint responds (mocked pyautogui)
  - Test `/tools/save_credentials` endpoint responds

- [ ] **Task 2.2**: Test Ollama MCP server startup on port 8000
  - Verify FastMCP ASGI app starts
  - Test `/tools/summarize_phi` endpoint responds (mocked Ollama)
  - Test `/tools/validate_eligibility` endpoint responds

- [ ] **Task 2.3**: Test Search MCP server startup on port 8002
  - Verify FastMCP ASGI app starts
  - Test `/tools/fetch_medical_guidelines` endpoint responds
  - Test `/tools/scan_repo` endpoint responds (mocked GitHub)

### Run Commands
```bash
# Terminal 1: Start eCW Bridge
python mcp_servers/ecw_bridge/server.py

# Terminal 2: Start Ollama MCP
python mcp_servers/ollama_server/server.py

# Terminal 3: Start Search MCP
python mcp_servers/search_mcp/server.py

# Terminal 4: Run tests
pytest tests/ -v -m "integration" --timeout=10
```

### Expected Status
Each server responds to HTTP requests without errors.

---

## Phase 3: Orchestrator Integration Tests ⏳
**Goal:** `main.py` orchestrator can call all three MCP servers correctly.

### Tasks
- [ ] **Task 3.1**: Mock all three servers, test orchestrator pipeline
  - Verify orchestrator can reach all three servers
  - Verify response handling for each server

- [ ] **Task 3.2**: Test end-to-end pipeline with mocked services
  - Run `VIDENTI_TEST_RUN=1 python main.py`
  - Verify all steps execute without errors

### Run Command
```bash
VIDENTI_TEST_RUN=1 python main.py
```

### Expected Status
Orchestrator successfully calls all three servers and processes a mock patient.

---

## Phase 4: Optional Local Ollama Integration ⏳
**Goal:** Test with a real local Ollama instance (requires Ollama installed).

### Prerequisites
```bash
# Install Ollama from https://ollama.ai
# Then run:
ollama pull medgemma:27b
# or
ollama pull deepseek-r1:7b
```

### Tasks
- [ ] **Task 4.1**: Start Ollama service
  ```bash
  ollama serve
  ```

- [ ] **Task 4.2**: Test Ollama MCP server with real models
  ```bash
  # Terminal 1: Ollama service
  ollama serve

  # Terminal 2: Ollama MCP server
  python mcp_servers/ollama_server/server.py

  # Terminal 3: Run integration tests
  pytest tests/test_ollama_mcp.py -v -m "integration"
  ```

### Expected Status
Actual anonymization and eligibility validation work with real LLM.

---

## Phase 5: Dashboard UI Development ⏳
**Goal:** Build the React frontend for approving/dismissing recommendations.

### Tasks
- [ ] **Task 5.1**: Set up React + Vite build
  ```bash
  cd dashboard
  npm install
  npm run dev
  ```

- [ ] **Task 5.2**: Implement recommendation approval component
  - List pending recommendations
  - Approve/dismiss buttons
  - Call `approve_recommendation()` / `dismiss_recommendation()`

- [ ] **Task 5.3**: Implement audit log viewer
  - Show all past recommendations and outcomes
  - Filter by date, status, test type

### Run Command
```bash
cd dashboard && npm run dev
```

### Expected Status
Dashboard displays recommendations and sends approval/dismissal actions to eCW Bridge.

---

## Phase 6: RPA Testing with Real eCW (Optional) ⏳
**Goal:** Test PyAutoGUI actions against actual eCW instance.

### Prerequisites
- eCW portal account with credentials
- Credentials stored in `.env` via `save_credentials` tool

### Tasks
- [ ] **Task 6.1**: Create RPA_TESTING_GUIDE.md with coordinate mapping
  - Screenshot eCW UI
  - Identify button coordinates for your screen resolution
  - Update hardcoded coordinates in `open_chart()`, `pend_order()`

- [ ] **Task 6.2**: Test `open_chart()` with a test MRN
  - Manually trigger via dashboard or direct API call
  - Verify chart opens in eCW

- [ ] **Task 6.3**: Test `pend_order()` with a test order
  - Verify order appears as pending in eCW UI

### Run Command
```bash
# Once dashboard is running, use the UI to test approvals
# Or call directly:
curl -X POST http://localhost:8001/tools/open_chart \
  -H "Content-Type: application/json" \
  -d '{"patient_mrn": "TEST-MRN"}'
```

### Expected Status
Real orders appear as pending in eCW without manual intervention.

---

## Full Testing Checklist

### Pre-Phase 1: Setup
- [ ] Python 3.13+ installed
- [ ] Dependencies: `pip install -r requirements.txt`
- [ ] pytest configured (`pytest.ini` exists)

### Phase 1: Unit Tests
```bash
pytest tests/ -v -m "not integration"
```
- [ ] test_ecw_bridge.py: 3/3 pass
- [ ] test_ollama_mcp.py: 2/2 pass (unit only)
- [ ] test_search_mcp.py: 3/3 pass

### Phase 2: Server Tests
- [ ] eCW Bridge starts on :8001
- [ ] Ollama MCP starts on :8000
- [ ] Search MCP starts on :8002
- [ ] All endpoints respond to HTTP requests

### Phase 3: Orchestrator Tests
- [ ] `VIDENTI_TEST_RUN=1 python main.py` completes without error
- [ ] All three servers are called
- [ ] Results are logged

### Phase 4+: Advanced Testing
- [ ] Real Ollama models work
- [ ] Dashboard displays recommendations
- [ ] Real eCW integration works (if applicable)

---

## Next Immediate Actions

### Right Now (Phase 1 - Should Already Pass)
1. Run unit tests:
   ```bash
   pytest tests/ -v -m "not integration"
   ```
   Expected: 8/8 tests pass

### Next (Phase 2 - Server Startup)
1. Create test fixtures for mock servers
2. Implement server startup tests
3. Ensure each MCP server can be started and responds

### Then (Phase 3 - Orchestrator)
1. Test orchestrator communication
2. Mock all servers in `main.py` tests
3. Verify full pipeline runs

---

## Current Project Status
- **Phase 1**: ✅ Complete (unit tests exist)
- **Phase 2**: ⏳ Next: Server startup tests
- **Phase 3**: ⏳ Orchestrator integration
- **Phase 4**: ⏳ Real Ollama (optional)
- **Phase 5**: ⏳ Dashboard UI
- **Phase 6**: ⏳ Real eCW (optional)

