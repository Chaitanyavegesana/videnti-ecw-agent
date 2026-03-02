"""
Videnti Clinical AI — Application Test Suite
Comprehensive testing of all MCP servers, orchestrator, and dashboard.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TEST] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Test Configuration ──────────────────────────────────────────────────────

MCP_ENDPOINTS = {
    "ollama": "http://localhost:8000",
    "ecw_bridge": "http://localhost:8001",
    "search": "http://localhost:8002"
}

DASHBOARD_URL = "http://localhost:5173"

# ─── Test Results Tracking ──────────────────────────────────────────────────

test_results = {
    "timestamp": datetime.now().isoformat(),
    "servers": {},
    "dashboard": {},
    "integration": {}
}

# ─── Helper Functions ───────────────────────────────────────────────────────

async def test_server_connectivity(server_name: str, endpoint: str) -> bool:
    """Test if an MCP server is running and responsive."""
    logger.info(f"Testing {server_name} at {endpoint}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(endpoint)
            if resp.status_code in (200, 404, 405):  # 404/405 means server is up but no root endpoint
                logger.info(f"✓ {server_name} is ONLINE")
                return True
            else:
                logger.warning(f"✗ {server_name} returned status {resp.status_code}")
                return False
    except Exception as e:
        logger.error(f"✗ {server_name} FAILED: {e}")
        return False

async def test_ollama_tools() -> dict:
    """Test Ollama MCP tools."""
    logger.info("\n━━━ Testing Ollama MCP Server Tools ━━━")
    results = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: summarize_phi
            logger.info("Testing summarize_phi tool...")
            raw_snapshot = {
                "patient_name": "John Doe",
                "mrn": "MRN-123456",
                "dob": "1980-01-15",
                "pmh": "BMI 32, Snoring, Chronic fatigue",
                "notes": "Patient reports daytime sleepiness"
            }
            
            response = await client.post(
                f"{MCP_ENDPOINTS['ollama']}/tools/summarize_phi",
                json={"raw_snapshot": raw_snapshot},
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                results["summarize_phi"] = {
                    "status": "PASS",
                    "snapshot_id": data.get("snapshot_id"),
                    "phi_stripped": data.get("phi_stripped")
                }
                logger.info(f"✓ summarize_phi PASSED (ID: {data.get('snapshot_id')})")
            else:
                results["summarize_phi"] = {"status": "FAIL", "error": response.text}
                logger.warning(f"✗ summarize_phi FAILED: {response.status_code}")
                
    except Exception as e:
        logger.error(f"✗ Ollama tools test error: {e}")
        results["error"] = str(e)
    
    return results

async def test_ecw_bridge_tools() -> dict:
    """Test eCW Bridge MCP tools."""
    logger.info("\n━━━ Testing eCW Bridge MCP Server Tools ━━━")
    results = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: open_chart
            logger.info("Testing open_chart tool...")
            response = await client.post(
                f"{MCP_ENDPOINTS['ecw_bridge']}/tools/open_chart",
                json={"patient_mrn": "MRN-TEST-001"}
            )
            
            if response.status_code == 200:
                results["open_chart"] = {"status": "PASS"}
                logger.info("✓ open_chart PASSED")
            else:
                results["open_chart"] = {"status": "FAIL", "error": response.text}
                logger.warning(f"✗ open_chart FAILED: {response.status_code}")
            
            # Test 2: save_credentials
            logger.info("Testing save_credentials tool...")
            response = await client.post(
                f"{MCP_ENDPOINTS['ecw_bridge']}/tools/save_credentials",
                json={
                    "ecw_url": "https://demo.eclinicalworks.com",
                    "ecw_username": "test_user",
                    "ecw_password": "test_pass",
                    "ecw_clinic_id": "CLINIC-001"
                }
            )
            
            if response.status_code == 200:
                results["save_credentials"] = {"status": "PASS"}
                logger.info("✓ save_credentials PASSED")
            else:
                results["save_credentials"] = {"status": "FAIL"}
                logger.warning(f"✗ save_credentials FAILED")
                
    except Exception as e:
        logger.error(f"✗ eCW Bridge tools test error: {e}")
        results["error"] = str(e)
    
    return results

async def test_search_mcp_tools() -> dict:
    """Test Search MCP tools."""
    logger.info("\n━━━ Testing Search MCP Server Tools ━━━")
    results = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: fetch_medical_guidelines
            logger.info("Testing fetch_medical_guidelines tool...")
            response = await client.post(
                f"{MCP_ENDPOINTS['search']}/tools/fetch_medical_guidelines",
                json={"topic": "HST"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results["fetch_medical_guidelines"] = {"status": "PASS", "topic": "HST"}
                logger.info("✓ fetch_medical_guidelines PASSED")
            else:
                results["fetch_medical_guidelines"] = {"status": "FAIL"}
                logger.warning(f"✗ fetch_medical_guidelines FAILED")
                
    except Exception as e:
        logger.error(f"✗ Search MCP tools test error: {e}")
        results["error"] = str(e)
    
    return results

async def test_dashboard_accessibility() -> bool:
    """Test if dashboard is accessible."""
    logger.info(f"\n━━━ Testing Dashboard Accessibility ━━━")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(DASHBOARD_URL)
            if resp.status_code == 200:
                logger.info(f"✓ Dashboard is ONLINE at {DASHBOARD_URL}")
                return True
            else:
                logger.warning(f"✗ Dashboard returned status {resp.status_code}")
                return False
    except Exception as e:
        logger.warning(f"✗ Dashboard not yet accessible (this may be normal): {e}")
        return False

# ─── Main Test Runner ───────────────────────────────────────────────────────

async def run_all_tests():
    """Execute all tests and generate report."""
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║  VIDENTI CLINICAL AI — APPLICATION TEST SUITE          ║")
    logger.info("╚════════════════════════════════════════════════════════╝\n")
    
    # Step 1: Test Server Connectivity
    logger.info("STEP 1: Server Connectivity Tests")
    logger.info("─" * 50)
    for server_name, endpoint in MCP_ENDPOINTS.items():
        is_online = await test_server_connectivity(server_name, endpoint)
        test_results["servers"][server_name] = "ONLINE" if is_online else "OFFLINE"
    
    # Step 2: Test MCP Tools (if servers are online)
    logger.info("\n\nSTEP 2: MCP Tools Functionality Tests")
    logger.info("─" * 50)
    
    if test_results["servers"]["ollama"] == "ONLINE":
        test_results["integration"]["ollama_tools"] = await test_ollama_tools()
    else:
        logger.warning("Skipping Ollama tools test (server offline)")
    
    if test_results["servers"]["ecw_bridge"] == "ONLINE":
        test_results["integration"]["ecw_bridge_tools"] = await test_ecw_bridge_tools()
    else:
        logger.warning("Skipping eCW Bridge tools test (server offline)")
    
    if test_results["servers"]["search"] == "ONLINE":
        test_results["integration"]["search_mcp_tools"] = await test_search_mcp_tools()
    else:
        logger.warning("Skipping Search MCP tools test (server offline)")
    
    # Step 3: Test Dashboard
    logger.info("\n\nSTEP 3: Dashboard Accessibility Test")
    logger.info("─" * 50)
    dashboard_online = await test_dashboard_accessibility()
    test_results["dashboard"]["accessible"] = dashboard_online
    
    # Step 4: Print Summary
    print_test_summary()

def print_test_summary():
    """Print a formatted test summary."""
    logger.info("\n\n╔════════════════════════════════════════════════════════╗")
    logger.info("║              TEST SUMMARY & RESULTS                    ║")
    logger.info("╚════════════════════════════════════════════════════════╝\n")
    
    logger.info("📊 SERVER STATUS:")
    for server, status in test_results["servers"].items():
        emoji = "✓" if status == "ONLINE" else "✗"
        logger.info(f"  {emoji} {server.upper()}: {status}")
    
    if test_results.get("integration"):
        logger.info("\n🔧 TOOLS FUNCTIONALITY:")
        for tool_group, results in test_results["integration"].items():
            if isinstance(results, dict):
                for tool_name, tool_result in results.items():
                    if isinstance(tool_result, dict) and "status" in tool_result:
                        status_emoji = "✓" if tool_result["status"] == "PASS" else "✗"
                        logger.info(f"  {status_emoji} {tool_name}: {tool_result['status']}")
    
    logger.info(f"\n🌐 DASHBOARD:")
    status_emoji = "✓" if test_results["dashboard"].get("accessible") else "⚠"
    logger.info(f"  {status_emoji} Dashboard accessible: {test_results['dashboard'].get('accessible', False)}")
    if test_results["dashboard"].get("accessible"):
        logger.info(f"  📍 Open in browser: {DASHBOARD_URL}")
    
    # Save test results to file
    results_file = "/Users/chaitanya/Desktop/videnti-ecw-agent/test_results.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"\n💾 Test results saved to: {results_file}")
    
    logger.info("\n" + "="*60)
    logger.info("NEXT STEPS:")
    logger.info("="*60)
    logger.info("1. Check MCP Server status above")
    logger.info("2. Open Dashboard: http://localhost:5173")
    logger.info("3. Click 'Start Daily Scan' to test the orchestrator pipeline")
    logger.info("4. Check 'Audit Log' for execution logs")
    logger.info("5. Verify HIPAA guardrails in 'Settings'")
    logger.info("="*60 + "\n")

# ─── Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        logger.info("\nTest suite interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)
