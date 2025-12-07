import asyncio
import json
import aiohttp
import sys, os

# Ensure backend is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.core.authentication.auth_manager import auth_manager
from backend.core.database.connection import get_database
from backend.core.database.models import User
from sqlalchemy import select

BASE_URL = "http://localhost:8000"


async def get_user_id_by_email(email: str) -> int:
    db = get_database()
    async with db.get_session() as session:
        res = await session.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        return user.id if user else None


async def onboarding(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "profile": {"country": "KE", "continent": "Africa", "purpose": "Evaluate platform", "business_name": "Agent47 Test Co"},
        "social": {},
        "tutorials": {"skipped": True},
        "workflow": {"preferred_agent": "aria"}
    }
    async with session.post(f"{BASE_URL}/api/v1/onboarding/save", headers=headers, json=payload) as resp:
        return resp.status, await resp.json(), payload


async def choose_free(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(f"{BASE_URL}/api/v1/billing/choose-free", headers=headers) as resp:
        return resp.status, await resp.json()


async def get_me(session: aiohttp.ClientSession, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/api/v1/auth/me", headers=headers) as resp:
        return resp.status, await resp.json()


async def main():
    email = "kalefrancis989@gmail.com"
    user_id = await get_user_id_by_email(email)
    if not user_id:
        print("❌ User not found. Run signup first.")
        return
    token = auth_manager.create_access_token({"sub": str(user_id), "email": email, "tier": "free"})

    async with aiohttp.ClientSession() as session:
        status, me = await get_me(session, token)
        print("/me:", status)
        print(json.dumps(me, indent=2))

        status, ob, ob_payload = await onboarding(session, token)
        print("Onboarding:", status)
        print("Payload:", json.dumps(ob_payload, indent=2))
        print(json.dumps(ob, indent=2))

        status, free = await choose_free(session, token)
        print("Choose free:", status)
        print(json.dumps(free, indent=2))


if __name__ == "__main__":
    asyncio.run(main())


