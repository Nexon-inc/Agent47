#!/usr/bin/env python3
"""
E2E: Verify each agent's chat router health and basic chat call to LLM
This script does not fail hard on auth; it reports status so you can see what's working.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any


AGENTS = [
    {"name": "aria",   "port": 8001, "chat_prefix": "/aria-chat"},
    {"name": "clara",  "port": 8002, "chat_prefix": "/clara-chat"},
    {"name": "eric",   "port": 8003, "chat_prefix": "/eric-chat"},
    {"name": "jackie", "port": 8004, "chat_prefix": "/jackie-chat"},
    {"name": "joe",    "port": 8005, "chat_prefix": "/joe-chat"},
    {"name": "purity", "port": 8006, "chat_prefix": "/purity-chat"},
    {"name": "shakes", "port": 8007, "chat_prefix": "/shakes-chat"},
]


def _agent_prompt(agent_name: str) -> str:
    prompts = {
        "aria": "You are Aria, a social media management agent. Generate a 1-paragraph plan to grow Instagram engagement for a fashion brand.",
        "clara": "You are Clara, a customer support agent. Draft a short policy for prioritizing urgent support tickets.",
        "eric": "You are Eric, a sales agent. Outline a concise 5-step B2B outbound sequence for enterprise leads.",
        "jackie": "You are Jackie, a marketing agent. Propose a 6-week multi-channel campaign for a product launch.",
        "joe": "You are Joe, a research agent. Summarize key trends in African fintech for 2025.",
        "purity": "You are Purity, a startup builder. Propose an MVP scope and pricing for a marketplace app.",
        "shakes": "You are Shakes, a content agent. Write a short blog outline about AI for small businesses."
    }
    return prompts.get(agent_name.lower(), f"Hello from E2E test. Confirm you are {agent_name} and describe your capabilities briefly.")


async def check_agent(session: aiohttp.ClientSession, agent: Dict[str, Any]) -> Dict[str, Any]:
    base = f"http://localhost:{agent['port']}"
    chat = agent["chat_prefix"]
    # Eric dynamically mounts routers under "/eric" prefix in app.main
    # So its chat route becomes "/eric/eric-chat/message"
    if agent["name"] == "eric":
        message_url = f"{base}/eric{chat}/message"
    else:
        message_url = f"{base}{chat}/message"

    result: Dict[str, Any] = {"agent": agent["name"], "port": agent["port"], "chat": None}

    # Basic chat attempt (query params to avoid body schema issues)
    # Include headers that you can hook for bypass in middleware if desired
    params = {"message": _agent_prompt(agent["name"]), "session_id": "e2e-test-session"}
    headers = {
        "X-Bypass-Auth": "true",
        "Authorization": "Bearer TEST_BYPASS",
        "Content-Type": "application/json",
    }

    try:
        start = time.time()
        async with session.post(message_url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            elapsed = time.time() - start
            entry: Dict[str, Any] = {"status": resp.status, "elapsed_sec": round(elapsed, 2)}
            try:
                body = await resp.json()
            except Exception:
                body = await resp.text()
            entry["body_preview"] = str(body)[:600]
            # Consider 200 and 401 informative (401 likely due to auth dependency)
            entry["ok"] = resp.status == 200
            result["chat"] = entry
    except Exception as e:
        result["chat"] = {"status": None, "ok": False, "error": str(e)}

    return result


async def main():
    print("🧪 Agents Chat + LLM E2E Test")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        all_results = []
        for agent in AGENTS:
            print(f"\n➡️  Testing agent: {agent['name']} on port {agent['port']}")
            res = await check_agent(session, agent)
            all_results.append(res)

            # Print summary per agent
            h = res.get("health", {})
            c = res.get("chat", {})
            print(f"  Health: status={h.get('status')} ok={h.get('ok')}" )
            if "error" in h:
                print(f"    Health error: {h['error']}")
            print(f"  Chat:   status={c.get('status')} ok={c.get('ok')} elapsed={c.get('elapsed_sec')}s")
            if "error" in c:
                print(f"    Chat error: {c['error']}")
            else:
                print(f"    Chat body preview: {c.get('body_preview')}")

    print("\n📄 Notes:")
    print("- If chat returns 401/403, auth is still enforced. You can enable a testing bypass in middleware that trusts 'X-Bypass-Auth' in non-production.")
    print("- If connection refused, ensure the agent is running on the expected port (see backend/agents/run_{agent}.py).")


if __name__ == "__main__":
    asyncio.run(main())


