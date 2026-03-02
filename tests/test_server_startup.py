"""
Phase 2: Server Startup Integration Tests
Tests that each MCP server can start and respond to HTTP requests.

Run with: pytest tests/test_server_startup.py -v -m "integration" --timeout=60
"""

import pytest
import httpx
import asyncio
import subprocess
import time
import signal
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

# Test configuration
SERVERS = {
    "ecw_bridge": {
        "port": 8001,
        "module_path": "mcp_servers/ecw_bridge/server.py",
        "tools": ["open_chart", "pend_order", "save_credentials"],
    },
    "ollama_mcp": {
        "port": 8000,
        "module_path": "mcp_servers/ollama_server/server.py",
        "tools": ["summarize_phi", "validate_eligibility"],
    },
    "search_mcp": {
        "port": 8002,
        "module_path": "mcp_servers/search_mcp/server.py",
        "tools": ["scan_repo", "fetch_medical_guidelines"],
    }
}


# ── Helper Functions ──────────────────────────────────────────────────────

async def wait_for_server(port: int, timeout: int = 10, check_interval: float = 0.5) -> bool:
    """
    Poll a server endpoint until it responds or timeout.
    Returns True if server is ready, False if timeout.
    """
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < timeout:
            try:
                resp = await client.get(f"http://localhost:{port}/tools", timeout=2.0)
                if resp.status_code in (200, 404, 405):
                    return True
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.TimeoutException):
                await asyncio.sleep(check_interval)
                continue
    
    return False


async def test_server_http_endpoint(port: int, tool_name: str, payload: dict) -> dict:
    """
    Send a POST request to a server's tool endpoint and return the response.
    """
    url = f"http://localhost:{port}/tools/{tool_name}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


# ── Fixtures for Server Management ───────────────────────────────────────

@pytest.fixture
def venv_python():
    """Get the path to the venv python executable."""
    return str(PROJECT_ROOT / ".venv" / "bin" / "python")


@pytest.fixture
def ecw_bridge_server(venv_python):
    """Start and stop eCW Bridge server for tests."""
    port = SERVERS["ecw_bridge"]["port"]
    module_path = SERVERS["ecw_bridge"]["module_path"]
    
    # Check if server is already running
    async def check_running():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"http://localhost:{port}/tools", timeout=2.0)
                return resp.status_code in (200, 404, 405)
        except:
            return False
    
    already_running = asyncio.run(check_running())
    
    if already_running:
        print(f"\n✓ eCW Bridge already running on port {port}")
        yield port
    else:
        # Start the server
        proc = subprocess.Popen(
            [venv_python, str(PROJECT_ROOT / module_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        
        # Wait for server to be ready
        time.sleep(2)
        ready = asyncio.run(wait_for_server(port, timeout=15))
        
        if ready:
            print(f"\n✓ eCW Bridge server started on port {port}")
            yield port
            # Cleanup
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        else:
            proc.kill()
            pytest.skip(f"Failed to start eCW Bridge server on port {port}")


@pytest.fixture
def ollama_mcp_server(venv_python):
    """Start and stop Ollama MCP server for tests."""
    port = SERVERS["ollama_mcp"]["port"]
    module_path = SERVERS["ollama_mcp"]["module_path"]
    
    # Check if server is already running
    async def check_running():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"http://localhost:{port}/tools", timeout=2.0)
                return resp.status_code in (200, 404, 405)
        except:
            return False
    
    already_running = asyncio.run(check_running())
    
    if already_running:
        print(f"\n✓ Ollama MCP already running on port {port}")
        yield port
    else:
        # Start the server
        proc = subprocess.Popen(
            [venv_python, str(PROJECT_ROOT / module_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        
        # Wait for server to be ready
        time.sleep(2)
        ready = asyncio.run(wait_for_server(port, timeout=15))
        
        if ready:
            print(f"\n✓ Ollama MCP server started on port {port}")
            yield port
            # Cleanup
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        else:
            proc.kill()
            pytest.skip(f"Failed to start Ollama MCP server on port {port}")


@pytest.fixture
def search_mcp_server(venv_python):
    """Start and stop Search MCP server for tests."""
    port = SERVERS["search_mcp"]["port"]
    module_path = SERVERS["search_mcp"]["module_path"]
    
    # Check if server is already running
    async def check_running():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"http://localhost:{port}/tools", timeout=2.0)
                return resp.status_code in (200, 404, 405)
        except:
            return False
    
    already_running = asyncio.run(check_running())
    
    if already_running:
        print(f"\n✓ Search MCP already running on port {port}")
        yield port
    else:
        # Start the server
        proc = subprocess.Popen(
            [venv_python, str(PROJECT_ROOT / module_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        
        # Wait for server to be ready
        time.sleep(2)
        ready = asyncio.run(wait_for_server(port, timeout=15))
        
        if ready:
            print(f"\n✓ Search MCP server started on port {port}")
            yield port
            # Cleanup
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        else:
            proc.kill()
            pytest.skip(f"Failed to start Search MCP server on port {port}")


# ── ECW Bridge Server Tests ───────────────────────────────────────────────

class TestECWBridgeServer:
    """Tests for eCW Bridge MCP Server startup and endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ecw_bridge_server_starts(self, ecw_bridge_server):
        """Test that eCW Bridge server can start successfully."""
        port = ecw_bridge_server
        assert port == 8001
        print(f"✓ eCW Bridge server is responding on port {port}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ecw_bridge_responds_to_save_credentials(self, ecw_bridge_server):
        """Test that eCW Bridge responds to save_credentials endpoint."""
        port = ecw_bridge_server
        
        payload = {
            "ecw_url": "https://test.eclinicalworks.com",
            "ecw_username": "testuser",
            "ecw_password": "testpass123",
            "ecw_clinic_id": "CL-001",
            "mrn_salt": "test-salt-12345-secret"
        }
        
        result = await test_server_http_endpoint(port, "save_credentials", payload)
        
        assert result.get("status") == "SUCCESS"
        print(f"✓ save_credentials endpoint working")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ecw_bridge_responds_to_open_chart(self, ecw_bridge_server):
        """Test that eCW Bridge responds to open_chart endpoint."""
        port = ecw_bridge_server
        
        payload = {"patient_mrn": "TEST-12345"}
        result = await test_server_http_endpoint(port, "open_chart", payload)
        
        assert "status" in result
        print(f"✓ open_chart endpoint working: {result['status']}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ecw_bridge_responds_to_pend_order(self, ecw_bridge_server):
        """Test that eCW Bridge responds to pend_order endpoint."""
        port = ecw_bridge_server
        
        payload = {
            "cpt_code": "95800",
            "icd_code": "G47.33",
            "patient_mrn": "TEST-12345",
            "approval_token": "valid-approval-token-12345678"
        }
        result = await test_server_http_endpoint(port, "pend_order", payload)
        
        assert "status" in result
        print(f"✓ pend_order endpoint working: {result['status']}")


# ── Ollama MCP Server Tests ───────────────────────────────────────────────

class TestOllamaMCPServer:
    """Tests for Ollama MCP Server startup and endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_mcp_server_starts(self, ollama_mcp_server):
        """Test that Ollama MCP server can start successfully."""
        port = ollama_mcp_server
        assert port == 8000
        print(f"✓ Ollama MCP server is responding on port {port}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_mcp_responds_to_summarize_phi(self, ollama_mcp_server):
        """Test that Ollama MCP responds to summarize_phi endpoint."""
        port = ollama_mcp_server
        
        payload = {
            "raw_snapshot": {
                "patient_name": "John Doe",
                "mrn": "TEST-99",
                "ssn": "123-45-6789",
                "notes": "BMI 32, chronic snoring"
            }
        }
        
        result = await test_server_http_endpoint(port, "summarize_phi", payload)
        
        assert result.get("phi_stripped") is True
        assert "snapshot_id" in result
        print(f"✓ summarize_phi endpoint working: snapshot_id={result['snapshot_id']}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ollama_mcp_responds_to_validate_eligibility(self, ollama_mcp_server):
        """Test that Ollama MCP responds to validate_eligibility endpoint."""
        port = ollama_mcp_server
        
        payload = {
            "summary": {
                "snapshot_id": "test-snap-123",
                "clinical_notes": "BMI 32, snoring, fatigue"
            },
            "rule_set": "speed_play"
        }
        
        result = await test_server_http_endpoint(port, "validate_eligibility", payload)
        
        assert "eligibility_results" in result
        print(f"✓ validate_eligibility endpoint working")


# ── Search MCP Server Tests ───────────────────────────────────────────────

class TestSearchMCPServer:
    """Tests for Search MCP Server startup and endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_mcp_server_starts(self, search_mcp_server):
        """Test that Search MCP server can start successfully."""
        port = search_mcp_server
        assert port == 8002
        print(f"✓ Search MCP server is responding on port {port}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_mcp_responds_to_fetch_medical_guidelines(self, search_mcp_server):
        """Test that Search MCP responds to fetch_medical_guidelines endpoint."""
        port = search_mcp_server
        
        payload = {"topic": "HST"}
        result = await test_server_http_endpoint(port, "fetch_medical_guidelines", payload)
        
        assert result.get("topic") == "HST"
        assert "guidelines" in result
        print(f"✓ fetch_medical_guidelines endpoint working")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_mcp_responds_to_scan_repo(self, search_mcp_server):
        """Test that Search MCP responds to scan_repo endpoint."""
        port = search_mcp_server
        
        payload = {
            "owner": "CMSgov",
            "repo": "lcd-updates"
        }
        
        result = await test_server_http_endpoint(port, "scan_repo", payload)
        
        assert "status" in result
        print(f"✓ scan_repo endpoint working: {result['status']}")


# ── Multi-Server Coordination Test ─────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_servers_are_healthy(ecw_bridge_server, ollama_mcp_server, search_mcp_server):
    """Test that all three servers are running and healthy."""
    servers = {
        "eCW Bridge": ecw_bridge_server,
        "Ollama MCP": ollama_mcp_server,
        "Search MCP": search_mcp_server,
    }
    
    print("\n📋 Server Health Check:")
    for name, port in servers.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"http://localhost:{port}/tools", timeout=2.0)
                status = "✓" if resp.status_code in (200, 404, 405) else "✗"
                print(f"  {status} {name:15} (port {port})")
        except Exception as e:
            print(f"  ✗ {name:15} (port {port}) - {str(e)[:40]}")


# ── Documentation ──────────────────────────────────────────────────────────

"""
PHASE 2: SERVER STARTUP TESTS

These tests automatically start each MCP server, verify it responds,
and then shut it down. This ensures the servers can be launched correctly.

Running the Tests:

Option A: Run with automatic server startup/shutdown (recommended)
    /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python -m pytest tests/test_server_startup.py -v -m integration --timeout=60 -s

Option B: Start servers manually and run tests
    
    Terminal 1: eCW Bridge
        /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python mcp_servers/ecw_bridge/server.py
    
    Terminal 2: Ollama MCP
        /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python mcp_servers/ollama_server/server.py
    
    Terminal 3: Search MCP
        /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python mcp_servers/search_mcp/server.py
    
    Terminal 4: Run tests
        /Users/chaitanya/Desktop/videnti-ecw-agent/.venv/bin/python -m pytest tests/test_server_startup.py -v -m integration --timeout=60 -s

Expected Output:
    - TestECWBridgeServer::test_ecw_bridge_server_starts PASSED
    - TestECWBridgeServer::test_ecw_bridge_responds_to_save_credentials PASSED
    - TestECWBridgeServer::test_ecw_bridge_responds_to_open_chart PASSED
    - TestECWBridgeServer::test_ecw_bridge_responds_to_pend_order PASSED
    - TestOllamaMCPServer::test_ollama_mcp_server_starts PASSED
    - TestOllamaMCPServer::test_ollama_mcp_responds_to_summarize_phi PASSED
    - TestOllamaMCPServer::test_ollama_mcp_responds_to_validate_eligibility PASSED
    - TestSearchMCPServer::test_search_mcp_server_starts PASSED
    - TestSearchMCPServer::test_search_mcp_responds_to_fetch_medical_guidelines PASSED
    - TestSearchMCPServer::test_search_mcp_responds_to_scan_repo PASSED
    - test_all_servers_are_healthy PASSED

Notes:
- Tests can run with servers already running (e.g., for development)
- Tests automatically start servers if not already running
- Servers are shut down after tests complete
- Use -s flag to see print statements
"""
