from typing import Dict, Any, Optional
from core.database.connection import get_supabase
from ..models import AriaBrandProfile


class BrandService:
    async def get_or_create_profile(self, user_id: int) -> AriaBrandProfile:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            res = await session.execute(select(AriaBrandProfile).where(AriaBrandProfile.user_id == user_id))
            bp: Optional[AriaBrandProfile] = res.scalar_one_or_none()
            if bp:
                return bp
            bp = AriaBrandProfile(user_id=user_id, voice={}, banned_keywords=[], hashtags_bank=[], compliance_rules={})
            session.add(bp)
            await session.commit()
            return bp

    async def update_profile(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            res = await session.execute(select(AriaBrandProfile).where(AriaBrandProfile.user_id == user_id))
            bp: Optional[AriaBrandProfile] = res.scalar_one_or_none()
            if not bp:
                bp = AriaBrandProfile(user_id=user_id)
                session.add(bp)
            for k, v in updates.items():
                if hasattr(bp, k):
                    setattr(bp, k, v)
            await session.commit()
            return {"updated": True}


