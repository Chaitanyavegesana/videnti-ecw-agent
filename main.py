"""
Videnti Clinical AI — Main Orchestrator
Core pipeline for eCW schedule scanning and eligibility validation.

This script manages the daily schedule and coordinates between local MCP servers.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ─── Configuration ───────────────────────────────────────────────────────────

MCP_ENDPOINTS = {
    "ollama": "http://localhost:8000",
    "ecw_bridge": "http://localhost:8001",
    "search": "http://localhost:8002"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ORCHESTRATOR] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── MCP Communication Helpers ───────────────────────────────────────────────

async def call_mcp_tool(server: str, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Calls a tool on a specific local MCP server."""
    base_url = MCP_ENDPOINTS.get(server)
    if not base_url:
        logger.error(f"Unknown server: {server}")
        return {"status": "ERROR", "message": f"Unknown server: {server}"}
        
    url = f"{base_url}/tools/{tool}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to call tool {tool} on {server}: {e}")
            return {"status": "ERROR", "message": str(e)}

# ─── Core Functional Pipeline ───────────────────────────────────────────────

async def run_videnti_pipeline():
    """
    Main clinical AI pipeline:
    1. Scan schedule.
    2. Extract snapshots.
    3. Anonymized logic via Ollama.
    4. Flag recommendations.
    """
    logger.info("━━━ Starting Videnti Daily Pipeline ━━━")
    
    # Step 1: Fetch provider schedule (Mocking appointment retrieval for demo)
    # real app would call ecw_bridge.get_schedule()
    appointments = [
        {"patient_mrn": "MRN-123456", "time": "09:00 AM"},
        {"patient_mrn": "MRN-789012", "time": "09:15 AM"}
    ]
    
    for apt in appointments:
        mrn = apt["patient_mrn"]
        logger.info(f"Processing patient {mrn}...")
        
        # Step 2: Open chart
        await call_mcp_tool("ecw_bridge", "open_chart", {"patient_mrn": mrn})
        
        # Step 3: Extract & Anonymize (Simplified for orchestrator logic)
        # In real usage, ecw_bridge.extract() -> ollama.summarize_phi()
        mock_snapshot = {"mrn": mrn, "pmh": "BMI 32, Snoring", "notes": "Chronic fatigue"}
        
        anonymized = await call_mcp_tool("ollama", "summarize_phi", {"raw_snapshot": mock_snapshot})
        
        if anonymized.get("phi_stripped"):
            # Step 4: Validate Eligibility
            eligibility = await call_mcp_tool(
                "ollama", 
                "validate_eligibility", 
                {"summary": anonymized, "rule_set": "speed_play"}
            )
            
            logger.info(f"Analysis for {anonymized.get('snapshot_id')}: {eligibility.get('eligibility_results')}")
        
    logger.info("━━━ Pipeline Completed ━━━")

async def weekly_research_sync():
    """Weekly task to check for guideline updates."""
    logger.info("Running weekly CPT/ICD research sync...")
    search_results = await call_mcp_tool("search", "scan_repo", {"owner": "CMSgov", "repo": "lcd-updates"})
    logger.info(f"Search results: {search_results}")

# ─── Scheduler Setup ─────────────────────────────────────────────────────────

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Daily Clinical Pipeline at 7:30 AM
    scheduler.add_job(
        run_videnti_pipeline, 
        'cron', 
        hour=7, 
        minute=30,
        name='Daily Clinical Scan'
    )
    
    # Weekly Research Scan (Mondays at 8:00 AM)
    scheduler.add_job(
        weekly_research_sync,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        name='Weekly Legislative Sync'
    )
    
    scheduler.start()
    logger.info("Scheduler started (Daily 7:30 AM, Weekly Mon 8:00 AM)")

# ─── Main Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    # Start scheduler in the background
    start_scheduler()
    
    # For testing: Run once immediately if VIDENTI_TEST_RUN is set
    if os.environ.get("VIDENTI_TEST_RUN") == "1":
        loop.create_task(run_videnti_pipeline())
        
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Videnti Orchestrator shutting down.")
