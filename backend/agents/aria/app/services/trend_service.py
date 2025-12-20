from typing import Dict, Any, List, Optional
import httpx
from core.config import settings
from core.integrations.integration_manager import get_integration_manager
from core.database.connection import get_supabase
from ..models import TrendSignal


class TrendService:
    async def ingest_google_trends(self, topic: str, region: str = "global") -> Dict[str, Any]:
        # Lightweight usage of Google Trends public endpoints (no key) is intentionally omitted; placeholder for authenticated approach via third-party
        # Use SEMrush and Brandwatch for authenticated ingestion
        return {"success": True, "source": "google_trends", "topic": topic, "region": region}

    async def ingest_seo_semrush(self, keyword: str, region: str = "us") -> Dict[str, Any]:
        mgr = await get_integration_manager()
        res = await mgr.call_integration_api(
            user_id=0,
            integration_name="semrush",
            endpoint="/",
            method="GET",
            params={"type": "phrase_this", "key": settings.semrush.api_key, "phrase": keyword, "database": region},
        )
        await self._save_signal(keyword, region, [keyword], "semrush", 0.5)
        return {"success": True, "response_status": res.get("status_code", 0)}

    async def ingest_brandwatch_alert(self, topic: str, keywords: List[str], region: str = "global") -> Dict[str, Any]:
        await self._save_signal(topic, region, keywords, "brandwatch", 0.7)
        return {"success": True}

    async def _save_signal(self, topic: str, region: str, keywords: List[str], source: str, score: float):
        db = await get_supabase()
        async with db.get_session() as session:
            ts = TrendSignal(topic=topic, region=region, keywords=keywords, source=source, score=score)
            session.add(ts)
            await session.commit()


