"""
Health Check - Service Connectivity Verification
Tests all service endpoints to verify system is operational.
"""

import asyncio
import httpx
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HEALTH-CHECK] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

SERVICES = {
    "eCW Bridge": "http://localhost:8001",
    "Dashboard": "http://localhost:5173",
    "Ollama": "http://localhost:8000",
    "Search": "http://localhost:8002"
}


async def check_service(name: str, url: str, timeout: float = 5.0) -> tuple[str, bool]:
    """Check if a service is responding."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            success = response.status_code == 200
    except Exception:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                success = 200 <= response.status_code < 500
        except Exception:
            success = False
    
    return name, success


async def check_mcp_endpoints(base_url: str = "http://localhost:8001") -> dict:
    """Check FastMCP server endpoints."""
    endpoints = {
        "/health": None,
        "/login-status": None,
        "/session-check": None,
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{base_url}{endpoint}")
                    endpoints[endpoint] = response.status_code == 200
                except Exception:
                    endpoints[endpoint] = False
    except Exception as e:
        logger.error(f"Error checking MCP endpoints: {e}")
        for endpoint in endpoints:
            endpoints[endpoint] = False
    
    return endpoints


async def main():
    """Run all health checks."""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH CHECK")
    print("=" * 60 + "\n")
    
    # Check services
    print("Service Status:")
    print("-" * 60)
    
    tasks = [check_service(name, url) for name, url in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    operational = 0
    for name, status in results:
        icon = "🟢" if status else "🔴"
        print(f"{icon} {name:20} {'Online' if status else 'Offline'}")
        if status:
            operational += 1
    
    print("\neCW Bridge Endpoints:")
    print("-" * 60)
    
    endpoints = await check_mcp_endpoints()
    for endpoint, status in endpoints.items():
        icon = "🟢" if status else "🔴"
        print(f"{icon} {endpoint:20} {'Ready' if status else 'Not Ready'}")
    
    # Summary
    print("\n" + "=" * 60)
    if operational == len(SERVICES):
        print("Status: 🟢 All systems online!")
    elif operational >= len(SERVICES) // 2:
        print(f"Status: 🟡 {operational}/{len(SERVICES)} services online")
    else:
        print(f"Status: 🔴 {operational}/{len(SERVICES)} services online")
    print("=" * 60 + "\n")
    
    return operational == len(SERVICES)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

