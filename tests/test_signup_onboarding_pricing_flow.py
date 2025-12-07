import asyncio
import json
import sys
import os
from typing import Dict, Any
from pathlib import Path

import aiohttp


BASE_URL = "http://localhost:8000"

# Make backend package importable for fallback auth fix
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "backend"))


async def signup(session: aiohttp.ClientSession, email: str, password: str, username: str, first_name: str, last_name: str) -> Dict[str, Any]:
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
    }
    async with session.post(f"{BASE_URL}/api/v1/auth/signup", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data, "payload": payload}


async def login(session: aiohttp.ClientSession, email: str, password: str) -> Dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
    }
    async with session.post(f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data}


async def onboarding(session: aiohttp.ClientSession, token: str, email: str, username: str, full_name: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    onboarding_payload = {
        "profile": {
            "role": "Founder",
            "industry": "SaaS",
            "goals": ["automate", "scale"],
            "otherGoal": "",
            "business_name": "Agent47 Test Co",
            "business_website": "https://example.com",
            "business_size": "1-10",
            "business_stage": "early",
            "country": "KE",
            "continent": "Africa",
            "purpose": "Evaluate platform",
            "name": full_name,
            "full_name": full_name,
            "nickname": username,
            "username": username,
            "email": email
        }
    }
    async with session.post(
        f"{BASE_URL}/api/v1/onboarding/save",
        headers=headers,
        json=onboarding_payload,
        timeout=aiohttp.ClientTimeout(total=120),
    ) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data, "payload": onboarding_payload}


async def choose_free(session: aiohttp.ClientSession, token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(
        f"{BASE_URL}/api/v1/billing/choose-free",
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=120),
    ) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data}


async def select_agents(session: aiohttp.ClientSession, token: str, agents: list[str]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(
        f"{BASE_URL}/api/v1/account/selected-agents",
        headers=headers,
        json={"agents": agents},
        timeout=aiohttp.ClientTimeout(total=120),
    ) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data}


async def aria_chat(session: aiohttp.ClientSession, token: str, message: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(
        f"{BASE_URL}/api/agents/aria/aria-chat/message",
        headers=headers,
        params={"message": message},
        timeout=aiohttp.ClientTimeout(total=2000),  # Increased to 33 minutes for long LLM responses with 16k tokens
    ) as resp:
        # Some agent endpoints may return plain text/streamed content; be robust
        text_body = await resp.text()
        try:
            parsed = json.loads(text_body)
        except Exception:
            parsed = {"text": text_body}
        return {"status": resp.status, "data": parsed}


async def get_me(session: aiohttp.ClientSession, token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/api/v1/auth/me", headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        data = await resp.json()
        return {"status": resp.status, "data": data}


async def build_internal_token_for_email(email: str) -> str:
    try:
        from backend.core.authentication.auth_manager import auth_manager
        from backend.core.database.connection import get_database
        from backend.core.database.models import User
        from sqlalchemy import select

        db = get_database()
        async with db.get_session() as session:
            res = await session.execute(select(User).where(User.email == email))
            user = res.scalar_one_or_none()
            if not user:
                return None
            return auth_manager.create_access_token({"sub": str(user.id), "email": email, "tier": "free"})
    except Exception:
        return None


async def main():
    email = "kalefrancis989@gmail.com"
    password = "TestPass!234"
    username = "kalefrancis989"
    first_name = "Kale"
    last_name = "Francis"

    async with aiohttp.ClientSession() as session:
        print("\n🧪 Running signup → onboarding → pricing (free) flow...\n")

        # 1) Signup
        signup_result = await signup(session, email, password, username, first_name, last_name)
        print("Signup status:", signup_result["status"])
        print("Signup payload:", json.dumps(signup_result["payload"], indent=2))
        print("Signup response keys:", list(signup_result["data"].keys()))
        if signup_result["status"] not in (200, 201):
            print("❌ Signup failed:", json.dumps(signup_result["data"], indent=2))
            return

        access_token = signup_result["data"].get("access_token")
        if not access_token:
            print("❌ No access_token returned from signup")
            return

        # 2) Onboarding
        full_name = f"{first_name} {last_name}"
        onboarding_result = await onboarding(session, access_token, email, username, full_name)
        print("Onboarding status:", onboarding_result["status"])
        print("Onboarding payload:", json.dumps(onboarding_result["payload"], indent=2))
        if onboarding_result["status"] not in (200, 201):
            print("Onboarding failed with signup token, attempting internal-token fallback...")
            internal_token = await build_internal_token_for_email(email)
            if not internal_token:
                print("❌ Could not build internal token; aborting.")
                return
            onboarding_result = await onboarding(session, internal_token, email, username, full_name)
            print("Onboarding (fallback) status:", onboarding_result["status"])
            if onboarding_result["status"] not in (200, 201):
                print("❌ Onboarding failed:", json.dumps(onboarding_result["data"], indent=2))
                return
            access_token = internal_token

        # 3) Choose free pricing
        free_result = await choose_free(session, access_token)
        print("Choose-free status:", free_result["status"])
        print("Choose-free response:", json.dumps(free_result["data"], indent=2))
        if free_result["status"] not in (200, 201):
            print("❌ Choose free plan failed:", json.dumps(free_result["data"], indent=2))
            return

        # 4) Refresh token after choosing free so JWT carries tier=free
        login_result = await login(session, email, password)
        if login_result["status"] in (200, 201) and login_result["data"].get("access_token"):
            access_token = login_result["data"]["access_token"]
            print("Refreshed login after choose-free: 200")
        else:
            print("⚠️ Token refresh after choose-free failed; proceeding with existing token")

        # 5) Select one agent (free tier allows one)
        selected = await select_agents(session, access_token, ["aria"])
        print("Selected-agents status:", selected["status"]) 
        print("Selected-agents response:", json.dumps(selected["data"], indent=2))
        if selected["status"] not in (200, 201):
            print("❌ Selecting agent failed:", json.dumps(selected["data"], indent=2))
            return

        # 6) Verify profile
        me_result = await get_me(session, access_token)
        print("\n/me status:", me_result["status"])
        print("/me:", json.dumps(me_result["data"], indent=2))

        # 7) Send 1 comprehensive chat to Aria (social media management)
        # Using a single comprehensive prompt to test full completion
        prompt = "Create a comprehensive and detailed 30-day social media content calendar for a SaaS product launch. Include specific post ideas for Instagram, Twitter, and LinkedIn with exact captions, hashtags, posting times, and content themes for each day. Provide complete, actionable plans with step-by-step implementation details. Make sure to cover all 30 days with unique content for each day, including weekends."
        
        print(f"\n📝 Sending comprehensive chat request to Aria...")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Expected: Complete 30-day calendar with full details\n")
        
        res = await aria_chat(session, access_token, prompt)
        ok = res["status"] in (200, 201)
        
        # Extract full response text for better visibility
        response_text = ""
        if ok and "data" in res:
            data = res["data"]
            # Try to extract the actual response text from nested structure
            if isinstance(data, dict):
                if "response" in data:
                    response_text = data["response"]
                elif "data" in data and isinstance(data["data"], dict) and "response" in data["data"]:
                    response_text = data["data"]["response"]
                elif "text" in data:
                    response_text = data["text"]
                elif "content" in data:
                    response_text = data["content"]
                else:
                    # Fallback to JSON string
                    response_text = json.dumps(data, indent=2)
            else:
                response_text = str(data)
        
        # Show full response length and a longer preview (2000 chars for better visibility)
        response_length = len(response_text)
        preview = response_text[:2000] if response_text else json.dumps(res["data"])[:2000]
        truncation_indicator = "..." if len(response_text) > 2000 else ""
        
        print(f"\n✅ Chat Response:")
        print(f"   Status: {res['status']} ({'SUCCESS' if ok else 'FAILED'})")
        print(f"   Response length: {response_length:,} characters")
        print(f"   Response length: {response_length / 1024:.2f} KB")
        print(f"\n   Preview (first 2000 chars):")
        print(f"   {'='*80}")
        print(f"   {preview}{truncation_indicator}")
        print(f"   {'='*80}\n")
        
        # Check for truncation warnings and token usage
        if ok and isinstance(res.get("data"), dict):
            data = res["data"]
            if "truncated" in data and data["truncated"]:
                print(f"   ⚠️  WARNING: Response was truncated by token limit!")
            else:
                print(f"   ✓ Response completed fully (not truncated)")
            
            if "finish_reason" in data:
                finish_reason = data["finish_reason"]
                print(f"   Finish reason: {finish_reason}")
                if finish_reason == "stop":
                    print(f"   ✓ Model finished naturally (complete response)")
                elif finish_reason == "length":
                    print(f"   ⚠️  Model hit max_tokens limit (response may be incomplete)")
            
            if "usage" in data:
                usage = data["usage"]
                if isinstance(usage, dict):
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    print(f"\n   Token Usage:")
                    print(f"   - Prompt tokens: {prompt_tokens:,}")
                    print(f"   - Completion tokens: {completion_tokens:,}")
                    print(f"   - Total tokens: {total_tokens:,}")
                    print(f"   - Token usage: {completion_tokens / 12000 * 100:.1f}% of max_tokens (12,000)")
                    
                    if completion_tokens >= 11000:
                        print(f"   ⚠️  High token usage - approaching limit!")
                    elif completion_tokens >= 10000:
                        print(f"   ⚠️  Very high token usage - near limit!")
        else:
            print(f"   ❌ Chat failed: {json.dumps(res.get('data', {}), indent=2)}")

        # 8) Show DB snapshot via manage_users for verification
        try:
            import subprocess
            print("\n📋 backend/scripts/manage_users.py list:")
            result = subprocess.run([sys.executable, str(ROOT_DIR / "backend" / "scripts" / "manage_users.py"), "list"], capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print("Failed to run manage_users.py list:", e)


if __name__ == "__main__":
    asyncio.run(main())


