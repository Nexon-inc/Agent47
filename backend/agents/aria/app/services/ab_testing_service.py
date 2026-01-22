from typing import Dict, Any, List
from core.database.connection import get_supabase
from ..models import AriaPostVariant


class ABTestingService:
    async def record_variant_metrics(self, variant_id: int, metrics: Dict[str, Any]) -> bool:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            res = await session.execute(select(AriaPostVariant).where(AriaPostVariant.id == variant_id))
            pv: AriaPostVariant = res.scalar_one_or_none()
            if not pv:
                return False
            merged = dict((pv.metrics or {}))
            merged.update(metrics)
            pv.metrics = merged
            await session.commit()
            return True

    def pick_winner(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Simple weighted pick by clicks and reactions
        def score(v: Dict[str, Any]) -> float:
            m = v.get("metrics", {})
            return 3 * m.get("clicks", 0) + 2 * m.get("likes", 0) + 2 * m.get("shares", 0) + m.get("comments", 0)
        return max(variants, key=score) if variants else {}


