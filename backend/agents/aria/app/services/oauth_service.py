from typing import Dict, Any
import httpx
from backend.core.config import settings
from backend.core.database.connection import get_supabase
from backend.core.platforms.models import PlatformCredential, SocialPlatform, CredentialStatus
from sqlalchemy import select


class OAuthService:
    async def exchange_code_linkedin(self, user_id: int, code: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.linkedin.redirect_uri,
            "client_id": settings.linkedin.client_id,
            "client_secret": settings.linkedin.client_secret,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(settings.linkedin.token_url, data=data, timeout=20.0)
            if resp.status_code != 200:
                return {"success": False, "error": resp.text}
            token = resp.json().get("access_token")
        return await self._store_token(user_id, "linkedin", token)

    async def exchange_code_facebook(self, user_id: int, code: str) -> Dict[str, Any]:
        params = {
            "client_id": settings.facebook.app_id,
            "redirect_uri": settings.facebook.redirect_uri,
            "client_secret": settings.facebook.app_secret,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.facebook.token_url, params=params, timeout=20.0)
            if resp.status_code != 200:
                return {"success": False, "error": resp.text}
            token = resp.json().get("access_token")
        return await self._store_token(user_id, "facebook", token)

    async def _store_token(self, user_id: int, platform_name: str, access_token: str) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            plat = (await session.execute(select(SocialPlatform).where(SocialPlatform.name == platform_name))).scalar_one_or_none()
            cred = PlatformCredential(user_id=user_id, platform_id=plat.id, credential_type="oauth2", access_token=access_token, status=CredentialStatus.VALID)
            session.add(cred)
            await session.commit()
            return {"success": True, "platform": platform_name}


