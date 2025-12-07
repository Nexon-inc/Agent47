import asyncio
import json
import aiohttp

BASE_URL = "http://localhost:8000"


async def login(session: aiohttp.ClientSession, email: str, password: str):
    payload = {"email": email, "password": password}
    async with session.post(f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        return resp.status, await resp.json()


async def onboarding(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    onboarding_payload = {
        "profile": {"country": "KE", "continent": "Africa", "purpose": "Evaluate platform", "business_name": "Agent47 Test Co"},
        "social": {},
        "tutorials": {},
        "workflow": {"preferred_agent": "aria"}
    }
    async with session.post(f"{BASE_URL}/api/v1/onboarding/save", headers=headers, json=onboarding_payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        return resp.status, await resp.json()


async def choose_free(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(f"{BASE_URL}/api/v1/billing/choose-free", headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        return resp.status, await resp.json()


async def get_me(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/api/v1/auth/me", headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        return resp.status, await resp.json()


async def main():
    email = "kalefrancis989@gmail.com"
    password = "TestPass!234"
    async with aiohttp.ClientSession() as session:
        print("\n🧪 Login → onboarding → choose-free → /me\n")
        status, data = await login(session, email, password)
        print("Login:", status)
        print(json.dumps(data, indent=2))
        if status != 200:
            return
        token = data.get("access_token")
        status, me = await get_me(session, token)
        print("/me:", status)
        print(json.dumps(me, indent=2))
        status, ob = await onboarding(session, token)
        print("Onboarding:", status)
        print(json.dumps(ob, indent=2))
        status, free = await choose_free(session, token)
        print("Choose free:", status)
        print(json.dumps(free, indent=2))


if __name__ == "__main__":
    asyncio.run(main())


