"""
Videnti Clinical AI — Search MCP Server
FastMCP-based local server for GitHub scanning and guideline lookups.

Endpoint: http://localhost:8002
"""

import logging
from typing import Any, Dict, List

import httpx
from mcp.server.fastmcp import FastMCP

# ─── Configuration ───────────────────────────────────────────────────────────

SERVER_PORT = 8002
GITHUB_API_BASE = "https://api.github.com"

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SEARCH-MCP] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastMCP Server Init ─────────────────────────────────────────────────────

mcp = FastMCP(
    name="videnti-search-mcp",
    instructions="Medical coding repository and guideline search server",
)

# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def scan_repo(owner: str, repo: str) -> Dict[str, Any]:
    """
    Scans a GitHub repository for recent commits related to CPT/ICD changes.
    
    Args:
        owner: Repo owner (e.g., 'CMSgov').
        repo: Repo name (e.g., 'lcd-updates').
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    logger.info(f"Scanning repository: {owner}/{repo}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            commits = resp.json()
            
            # Simple keyword matching in commit messages
            keywords = ["CPT", "ICD", "95800", "95816", "CMS", "guideline"]
            relevant_commits = []
            
            for commit in commits[:10]:
                msg = commit.get("commit", {}).get("message", "")
                if any(kw in msg for kw in keywords):
                    relevant_commits.append({
                        "sha": commit["sha"],
                        "message": msg,
                        "date": commit["commit"]["author"]["date"]
                    })
            
            return {
                "status": "SUCCESS",
                "repo": f"{owner}/{repo}",
                "total_commits_checked": len(commits[:10]),
                "relevant_changes": relevant_commits
            }
        except Exception as e:
            logger.error(f"Failed to scan repo: {e}")
            return {"status": "ERROR", "message": str(e)}

@mcp.tool()
async def fetch_medical_guidelines(topic: str) -> Dict[str, Any]:
    """
    Simulates fetching clinical guidelines for a specific topic (e.g., 'HST').
    """
    # In a real implementation, this would search CMS or local DBs.
    guidelines = {
        "HST": "LCD L33295: Required BMI > 30, signs of sleep apnea.",
        "EEG": "LCD L34950: Baseline EEG for suspected seizures or syncope.",
        "ALLERGY": "LCD L35010: Persistent rhinitis symptoms > 6 months."
    }
    
    result = guidelines.get(topic.upper(), "No specific guidelines found for this topic.")
    return {"topic": topic, "guidelines": result}

if __name__ == "__main__":
    logger.info(f"Starting Videnti Search MCP Server on port {SERVER_PORT}")
    mcp.run(transport="streamable-http", host="localhost", port=SERVER_PORT)
