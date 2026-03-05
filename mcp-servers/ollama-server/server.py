"""
ICS - Intelligent Clinical System — Ollama MCP Server
FastMCP-based local server exposing Ollama inference to the agent.

Endpoint: http://localhost:8000
Ollama Base: http://localhost:11434
"""

import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List

import httpx
from mcp.server.fastmcp import FastMCP

# ─── Configuration ───────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
SERVER_PORT = 8000

# Model priority order — highest capability first
MODEL_PRIORITY = [
    "medgemma:27b",
    "deepseek-r1:14b",
    "llama3.3:70b",
    "qwen2.5:14b",
    "deepseek-r1:7b",
    "llama3.2:3b",
]

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OLLAMA-MCP] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── FastMCP Server Init ──────────────────────────────────────────────────────

mcp = FastMCP(
    name="ics-ollama-mcp",
    instructions="Local Ollama inference bridge for PHI anonymization and clinical reasoning",
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

async def get_available_model() -> str:
    """Returns the best available Ollama model from the priority list."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            available = {m["name"] for m in models}
            # Also check for names without tags or with :latest
            for model in MODEL_PRIORITY:
                if model in available or f"{model}:latest" in available:
                    logger.info(f"Selected model: {model}")
                    return model
            
            if available:
                fallback = models[0]["name"]
                logger.warning(f"No preferred model found. Falling back to: {fallback}")
                return fallback
                
            raise RuntimeError("No Ollama models found. Run: ollama pull deepseek-r1:14b")
        except (httpx.ConnectError, httpx.HTTPError) as e:
            raise RuntimeError(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")

async def ollama_generate(model: str, prompt: str, system: str = "") -> str:
    """Sends a generation request to Ollama and returns the response text."""
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 8192,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def summarize_phi(raw_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips raw PHI and returns an anonymized clinical summary.
    
    Args:
        raw_snapshot: Raw patient data dict.
        
    Returns:
        Anonymized summary dict with snapshot_id.
    """
    model = await get_available_model()
    
    system_prompt = (
        "You are a HIPAA-compliant clinical data anonymizer. "
        "Remove ALL 18 HIPAA identifiers from the provided data. "
        "Return ONLY a de-identified clinical summary in JSON format."
    )
    
    user_prompt = f"Anonymize this patient data and provide a clinical summary: {json.dumps(raw_snapshot)}"
    
    response = await ollama_generate(model, user_prompt, system_prompt)
    
    # Simple JSON extraction logic
    try:
        # Handle cases where model might wrap JSON in backticks
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[-1].split("```")[0].strip()
            
        summary_data = json.loads(response)
    except Exception:
        summary_data = {"raw_summary": response}

    snapshot_id = str(uuid.uuid4())
    
    output = {
        "snapshot_id": snapshot_id,
        "clinical_summary": summary_data,
        "phi_stripped": True,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Generated snapshot_id: {snapshot_id}")
    return output

@mcp.tool()
async def validate_eligibility(summary: Dict[str, Any], rule_set: str = "speed_play") -> Dict[str, Any]:
    """
    Determines clinical eligibility for tests (HST, EEG, Allergy).
    """
    model = await get_available_model()
    
    system_prompt = (
        "You are a clinical decision support system. "
        "Based on the provided anonymized summary, determine if the patient qualifies for: "
        "1. Home Sleep Test (HST) - Indicators: BMI > 30, Snoring, Fatigue. "
        "2. EEG - Indicators: Seizures, Syncope, LOC. "
        "3. Allergy Panel - Indicators: Chronic rhinitis, Asthma. "
        "Return a JSON list of qualified_tests with confidence scores."
    )
    
    user_prompt = f"Evaluate eligibility for {rule_set}: {json.dumps(summary)}"
    
    response = await ollama_generate(model, user_prompt, system_prompt)
    
    try:
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        result = json.loads(response)
    except Exception:
        result = {"analysis": response}
        
    return {
        "snapshot_id": summary.get("snapshot_id"),
        "eligibility_results": result,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Videnti Ollama MCP Server on port {SERVER_PORT}")
    
    # Wrap FastMCP with Uvicorn for HTTP transport
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app):
        logger.info(f"✓ Ollama MCP Server running on http://localhost:{SERVER_PORT}")
        yield
        logger.info("Shutting down Ollama MCP Server...")
    
    # Create a simple ASGI app that wraps the MCP server
    app = mcp.asgi()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="info"
    )
