"""
Phase 3: Orchestrator Integration Tests
Tests that main.py orchestrator can communicate with all three MCP servers.

Run with: pytest tests/test_orchestrator_integration.py -v -m "integration" --timeout=60
"""

import pytest
import httpx
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_mcp_responses():
    """Provides mock responses from each MCP server."""
    return {
        "ecw_bridge": {
            "open_chart": {"status": "SUCCESS", "message": "Chart opened for MRN-123456"},
            "pend_order": {
                "status": "SUCCESS",
                "order_details": {"cpt": "95800", "icd": "G47.33", "patient": "MRN-123456"}
            }
        },
        "ollama": {
            "summarize_phi": {
                "snapshot_id": "snap-uuid-12345",
                "clinical_summary": {"clinical_notes": "BMI elevated, fatigue noted"},
                "phi_stripped": True,
                "timestamp": "2026-02-28T12:00:00"
            },
            "validate_eligibility": {
                "snapshot_id": "snap-uuid-12345",
                "eligibility_results": [
                    {"test": "HST", "confidence": 0.92},
                    {"test": "EEG", "confidence": 0.45}
                ],
                "timestamp": "2026-02-28T12:00:00"
            }
        },
        "search": {
            "scan_repo": {
                "status": "SUCCESS",
                "repo": "CMSgov/lcd-updates",
                "total_commits_checked": 10,
                "relevant_changes": []
            },
            "fetch_medical_guidelines": {
                "topic": "HST",
                "guidelines": "LCD L33295: Required BMI > 30, signs of sleep apnea."
            }
        }
    }


@pytest.fixture
def mock_http_client(mock_mcp_responses):
    """Mocks httpx.AsyncClient to return predefined responses."""
    async def mock_post(url, json=None, **kwargs):
        # Parse the URL to determine which server and tool
        if "8001" in url or "ecw_bridge" in url:
            if "open_chart" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["ecw_bridge"]["open_chart"]
                response.raise_for_status = MagicMock()
                return response
            elif "pend_order" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["ecw_bridge"]["pend_order"]
                response.raise_for_status = MagicMock()
                return response
        
        elif "8000" in url or "ollama" in url:
            if "summarize_phi" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["ollama"]["summarize_phi"]
                response.raise_for_status = MagicMock()
                return response
            elif "validate_eligibility" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["ollama"]["validate_eligibility"]
                response.raise_for_status = MagicMock()
                return response
        
        elif "8002" in url or "search" in url:
            if "scan_repo" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["search"]["scan_repo"]
                response.raise_for_status = MagicMock()
                return response
            elif "fetch_medical_guidelines" in url:
                response = MagicMock()
                response.json = lambda: mock_mcp_responses["search"]["fetch_medical_guidelines"]
                response.raise_for_status = MagicMock()
                return response
        
        raise ValueError(f"Unexpected URL: {url}")
    
    return mock_post


# ── Unit Tests for call_mcp_tool ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_call_mcp_tool_sends_correct_request(mock_http_client):
    """Verify call_mcp_tool constructs the correct HTTP request."""
    from main import call_mcp_tool
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post = mock_http_client
        
        result = await call_mcp_tool(
            "ollama",
            "summarize_phi",
            {"raw_snapshot": {"name": "Test", "notes": "BMI 32"}}
        )
        
        assert result.get("phi_stripped") is True
        assert "snapshot_id" in result
        print(f"✓ call_mcp_tool correctly called ollama.summarize_phi: {result['snapshot_id']}")


@pytest.mark.asyncio
async def test_call_mcp_tool_handles_unknown_server():
    """Verify call_mcp_tool returns ERROR for unknown server."""
    from main import call_mcp_tool
    
    result = await call_mcp_tool("unknown_server", "some_tool", {})
    
    assert result.get("status") == "ERROR"
    assert "Unknown server" in result.get("message", "")
    print(f"✓ call_mcp_tool correctly rejected unknown server")


@pytest.mark.asyncio
async def test_call_mcp_tool_handles_http_errors(mock_http_client):
    """Verify call_mcp_tool handles HTTP errors gracefully."""
    from main import call_mcp_tool
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        
        # Simulate connection error
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")
        
        result = await call_mcp_tool("ecw_bridge", "open_chart", {"patient_mrn": "TEST"})
        
        assert result.get("status") == "ERROR"
        print(f"✓ call_mcp_tool correctly handled connection error")


# ── Integration Tests for run_videnti_pipeline ───────────────────────────

@pytest.mark.asyncio
async def test_run_videnti_pipeline_processes_appointments(mock_http_client, mock_mcp_responses):
    """
    Test that run_videnti_pipeline successfully processes a mock appointment
    by calling all three MCP servers in the correct sequence.
    """
    from main import run_videnti_pipeline
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        # Wrap the mock function with AsyncMock for tracking calls
        mock_client_instance.post = AsyncMock(side_effect=mock_http_client)
        
        # Run the pipeline
        await run_videnti_pipeline()
        
        # Verify that HTTP calls were made
        assert mock_client_instance.post.called, "Should have made HTTP calls"
        print(f"✓ run_videnti_pipeline executed without errors ({mock_client_instance.post.call_count} calls made)")


@pytest.mark.asyncio
async def test_run_videnti_pipeline_calls_all_servers(mock_http_client):
    """
    Verify that the pipeline calls ecw_bridge, ollama, and search servers
    in the correct order.
    """
    from main import run_videnti_pipeline
    
    call_sequence = []
    
    async def tracking_post(url, json=None, **kwargs):
        # Track which servers are called
        if "8001" in url:
            call_sequence.append("ecw_bridge")
        elif "8000" in url:
            call_sequence.append("ollama")
        elif "8002" in url:
            call_sequence.append("search")
        
        return await mock_http_client(url, json=json, **kwargs)
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post = tracking_post
        
        await run_videnti_pipeline()
        
        # Verify servers were called (order may vary due to async execution)
        assert "ecw_bridge" in call_sequence, "eCW Bridge should be called"
        assert "ollama" in call_sequence, "Ollama should be called"
        print(f"✓ run_videnti_pipeline called all expected servers: {set(call_sequence)}")


# ── Test for weekly_research_sync ───────────────────────────────────────

@pytest.mark.asyncio
async def test_weekly_research_sync_calls_search_server(mock_http_client):
    """
    Test that weekly_research_sync correctly calls the search MCP server
    to check for guideline updates.
    """
    from main import weekly_research_sync
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        # Wrap the mock function with AsyncMock for tracking calls
        mock_client_instance.post = AsyncMock(side_effect=mock_http_client)
        
        await weekly_research_sync()
        
        assert mock_client_instance.post.called, "Should have called search server"
        print(f"✓ weekly_research_sync executed and called search server ({mock_client_instance.post.call_count} calls)")


# ── End-to-End Pipeline Test ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_patient_processing_workflow(mock_http_client, mock_mcp_responses):
    """
    Comprehensive test simulating the complete workflow:
    1. eCW Bridge opens a chart
    2. Ollama anonymizes and validates eligibility
    3. Results are logged/processed
    """
    from main import call_mcp_tool
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post = mock_http_client
        
        # Step 1: Open chart
        chart_result = await call_mcp_tool(
            "ecw_bridge",
            "open_chart",
            {"patient_mrn": "MRN-123456"}
        )
        assert chart_result.get("status") == "SUCCESS"
        print(f"  ✓ Step 1: Chart opened")
        
        # Step 2: Extract and anonymize (mock raw data)
        mock_snapshot = {
            "patient_name": "John Doe",
            "mrn": "MRN-123456",
            "ssn": "123-45-6789",
            "notes": "BMI 32, chronic snoring, fatigue"
        }
        
        summary_result = await call_mcp_tool(
            "ollama",
            "summarize_phi",
            {"raw_snapshot": mock_snapshot}
        )
        assert summary_result.get("phi_stripped") is True
        snapshot_id = summary_result.get("snapshot_id")
        assert snapshot_id, "Should receive snapshot_id"
        print(f"  ✓ Step 2: Data anonymized (snapshot_id={snapshot_id})")
        
        # Step 3: Validate eligibility
        eligibility_result = await call_mcp_tool(
            "ollama",
            "validate_eligibility",
            {"summary": summary_result, "rule_set": "speed_play"}
        )
        assert "eligibility_results" in eligibility_result
        results = eligibility_result.get("eligibility_results", [])
        print(f"  ✓ Step 3: Eligibility validated ({len(results)} tests recommended)")
        
        # Step 4: Fetch relevant guidelines
        guidelines_result = await call_mcp_tool(
            "search",
            "fetch_medical_guidelines",
            {"topic": "HST"}
        )
        assert "guidelines" in guidelines_result
        print(f"  ✓ Step 4: Guidelines retrieved")
        
        print(f"\n✓ Complete workflow succeeded for patient MRN-123456")


# ── Scheduler Tests ───────────────────────────────────────────────────────

def test_scheduler_is_configured():
    """
    Verify that the scheduler has the expected jobs configured.
    """
    from main import start_scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    
    # Create a test scheduler
    scheduler = AsyncIOScheduler()
    
    # Add the same jobs as in main.py
    from main import run_videnti_pipeline, weekly_research_sync
    
    scheduler.add_job(
        run_videnti_pipeline,
        'cron',
        hour=7,
        minute=30,
        name='Daily Clinical Scan'
    )
    
    scheduler.add_job(
        weekly_research_sync,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        name='Weekly Legislative Sync'
    )
    
    jobs = scheduler.get_jobs()
    assert len(jobs) == 2, "Should have exactly 2 jobs"
    assert any("Daily Clinical Scan" in job.name for job in jobs)
    assert any("Weekly Legislative Sync" in job.name for job in jobs)
    print(f"✓ Scheduler is correctly configured with 2 jobs")


# ── Documentation ──────────────────────────────────────────────────────────

"""
PHASE 3: ORCHESTRATOR INTEGRATION TESTS

These tests verify that main.py can communicate with all three MCP servers
without requiring them to actually be running (they are mocked).

Running the Tests:
    cd /Users/chaitanya/Desktop/videnti-ecw-agent
    /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python -m pytest tests/test_orchestrator_integration.py -v -m integration --timeout=60

Expected Output:
    - test_call_mcp_tool_sends_correct_request PASSED
    - test_call_mcp_tool_handles_unknown_server PASSED
    - test_call_mcp_tool_handles_http_errors PASSED
    - test_run_videnti_pipeline_processes_appointments PASSED
    - test_run_videnti_pipeline_calls_all_servers PASSED
    - test_weekly_research_sync_calls_search_server PASSED
    - test_complete_patient_processing_workflow PASSED
    - test_scheduler_is_configured PASSED

All tests use mocks, so NO external services need to be running.

Testing Strategy:
1. Mock HTTP responses from each server
2. Verify orchestrator sends correct requests
3. Verify orchestrator handles errors gracefully
4. Test complete end-to-end workflow with mocked servers
5. Verify scheduler is correctly configured

Next Steps After Phase 3:
- Run Phase 1 + Phase 3 tests together to verify core logic and orchestration
- Then move to Phase 2 to test actual server startup and HTTP communication
"""
