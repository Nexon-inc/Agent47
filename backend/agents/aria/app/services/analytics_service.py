from typing import Dict, Any, List
from statistics import mean
from core.database.connection import get_supabase
from ..models import AnalyticsSnapshot


class AnalyticsService:
    async def get_post_summary(self, user_id: int, post_ref: str) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AnalyticsSnapshot).where(
                    (AnalyticsSnapshot.user_id == user_id) & (AnalyticsSnapshot.post_ref == post_ref)
                )
            )
            snaps: List[AnalyticsSnapshot] = result.scalars().all()
            if not snaps:
                return {"post_ref": post_ref, "metrics": {}}
            impressions = sum(s.impressions for s in snaps)
            likes = sum(s.likes for s in snaps)
            comments = sum(s.comments for s in snaps)
            shares = sum(s.shares for s in snaps)
            saves = sum(s.saves for s in snaps)
            clicks = sum(s.clicks for s in snaps)
            ctr = mean([s.ctr for s in snaps if s.ctr is not None]) if snaps else 0.0
            sentiment = mean([s.sentiment_score for s in snaps]) if snaps else 0.0
            velocity = mean([s.velocity_score for s in snaps]) if snaps else 0.0
            virality = self._virality_score(impressions, likes, comments, shares, saves, clicks, velocity, sentiment)
            return {
                "post_ref": post_ref,
                "metrics": {
                    "impressions": impressions,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "saves": saves,
                    "clicks": clicks,
                    "ctr": ctr,
                    "sentiment": sentiment,
                    "velocity": velocity,
                    "virality": virality,
                },
            }

    def _virality_score(self, impressions: int, likes: int, comments: int, shares: int, saves: int, clicks: int, velocity: float, sentiment: float) -> float:
        if impressions <= 0:
            return 0.0
        engagement = (likes + 2 * comments + 3 * shares + 2 * saves + 1.5 * clicks) / max(1, impressions)
        score = 0.6 * engagement + 0.2 * velocity + 0.2 * max(0.0, min(1.0, (sentiment + 1) / 2))
        return round(min(1.0, score), 4)


