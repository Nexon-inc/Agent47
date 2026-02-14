
import asyncio
import httpx
import sys

async def check_agent_health(name, url):
    print(f"Checking {name} at {url}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            print(f"[{name}] Status: {response.status_code}")
            if response.status_code == 200:
                print(f"[{name}] Data: {response.json()}")
            return response.status_code == 200
    except Exception as e:
        print(f"[{name}] Failed: {str(e)}")
        return False

async def main():
    base_url = "http://localhost:8080/api/agents"
    agents = ["aria", "clara", "eric", "jackie", "joe", "purity", "shakes"]
    
    results = {}
    for agent in agents:
        # Most agents have a /health endpoint
        health_url = f"{base_url}/{agent}/health"
        # Some might have it at the root of their mount / or /status
        root_url = f"{base_url}/{agent}/"
        
        health_ok = await check_agent_health(f"{agent}_health", health_url)
        root_ok = await check_agent_health(f"{agent}_root", root_url)
        results[agent] = health_ok or root_ok

    print("\n--- Summary ---")
    for agent, ok in results.items():
        print(f"{agent.upper()}: {'ONLINE' if ok else 'OFFLINE'}")

if __name__ == "__main__":
    asyncio.run(main())
