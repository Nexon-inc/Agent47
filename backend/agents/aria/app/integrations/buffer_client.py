from typing import Dict, Any, List, Optional
import httpx
from backend.core.config import settings
from backend.core.integrations.integration_manager import get_integration_manager


class BufferClient:
    def __init__(self):
        self.base_url = settings.buffer.base_url.rstrip("/")
        self.token = settings.buffer.access_token

    async def create_update(self, profile_ids: List[str], text: str, media: Optional[List[str]] = None, scheduled_at: Optional[str] = None) -> Dict[str, Any]:
        params = {"access_token": self.token}
        data: Dict[str, Any] = {"text": text, "profile_ids[]": profile_ids, "now": not bool(scheduled_at)}
        if scheduled_at:
            data["scheduled_at"] = scheduled_at
        if media:
            for i, m in enumerate(media):
                data[f"media[photo][{i}]"] = m
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/updates/create.json", params=params, data=data, timeout=30.0)
            if resp.status_code in (200, 201):
                return {"success": True, "response": resp.json()}
            return {"success": False, "error": f"buffer_status_{resp.status_code}", "response": resp.text}

    async def list_profiles(self) -> Dict[str, Any]:
        mgr = await get_integration_manager()
        return await mgr.call_integration_api(
            user_id=0,  # system context; replace with real user if needed
            integration_name="buffer",
            endpoint="/profiles.json",
            method="GET",
            params={"access_token": self.token},
        )


