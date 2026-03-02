"""
Module Tests: Search MCP Server
Tests scan_repo and fetch_medical_guidelines tools.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.asyncio
async def test_fetch_medical_guidelines_hst(monkeypatch):
    """fetch_medical_guidelines should return HST guidelines for 'HST' topic."""
    from mcp_servers.search_mcp.server import fetch_medical_guidelines

    result = await fetch_medical_guidelines("HST")
    assert result["topic"] == "HST"
    assert "L33295" in result["guidelines"], "HST guidelines should reference LCD L33295"
    print(f"PASS: fetch_medical_guidelines returned: {result['guidelines'][:60]}...")


@pytest.mark.asyncio
async def test_fetch_medical_guidelines_unknown(monkeypatch):
    """fetch_medical_guidelines should return a fallback for unknown topics."""
    from mcp_servers.search_mcp.server import fetch_medical_guidelines

    result = await fetch_medical_guidelines("UNKNOWN_TOPIC")
    assert "No specific guidelines" in result["guidelines"]
    print("PASS: fetch_medical_guidelines correctly returned fallback response")


@pytest.mark.asyncio
async def test_scan_repo_handles_connection_error(monkeypatch):
    """scan_repo should return ERROR status on network failure."""
    import httpx
    from mcp_servers.search_mcp.server import scan_repo

    # Mock httpx to simulate a connection failure
    async def mock_get(*args, **kwargs):
        raise httpx.ConnectError("Simulated network error")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await scan_repo("CMSgov", "lcd-updates")
    assert result["status"] == "ERROR", "Should return ERROR on connection failure"
    print(f"PASS: scan_repo returned ERROR gracefully: {result['message']}")
