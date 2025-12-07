import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.core.database import get_database
from backend.core.cache import get_redis
from backend.core.logs import get_logger


class UserInsights:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()

    async def initialize(self):
        return True

    async def cohort_retention(self, weeks: int = 8) -> List[Dict[str, Any]]:
        try:
            async with self.db.get_session() as session:
                results = []
                start_week = datetime.utcnow() - timedelta(weeks=weeks)
                for i in range(weeks):
                    cohort_start = (start_week + timedelta(weeks=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                    cohort_end = cohort_start + timedelta(weeks=1)
                    # users signed up during cohort
                    cohort_users = await session.execute(
                        """
                        SELECT id FROM users WHERE created_at >= %s AND created_at < %s
                        """,
                        (cohort_start, cohort_end),
                    )
                    user_ids = [row[0] for row in cohort_users.fetchall()]
                    if not user_ids:
                        results.append({"cohort": cohort_start.date().isoformat(), "size": 0, "retention": 0.0})
                        continue
                    retained = await session.execute(
                        """
                        SELECT COUNT(DISTINCT user_id) FROM user_activities
                        WHERE user_id = ANY(%s) AND timestamp >= %s AND timestamp < %s
                        """,
                        (user_ids, cohort_end, cohort_end + timedelta(weeks=1)),
                    )
                    retained_count = int(retained.scalar() or 0)
                    results.append({
                        "cohort": cohort_start.date().isoformat(),
                        "size": len(user_ids),
                        "retained_next_week": retained_count,
                        "retention": (retained_count / len(user_ids)) * 100.0,
                    })
                return results
        except Exception as e:
            self.logger.error(f"Failed cohort retention: {e}")
            return []

    async def feature_adoption(self, days: int = 30) -> Dict[str, Any]:
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            async with self.db.get_session() as session:
                result = await session.execute(
                    """
                    SELECT activity_type, COUNT(*) cnt
                    FROM user_activities
                    WHERE timestamp >= %s
                    GROUP BY activity_type ORDER BY cnt DESC
                    """,
                    (cutoff,),
                )
                rows = result.fetchall()
                top = {row[0]: row[1] for row in rows}
                return {"period_days": days, "top_features": top}
        except Exception as e:
            self.logger.error(f"Failed feature adoption: {e}")
            return {}


_user_insights: Optional[UserInsights] = None


async def get_user_insights() -> UserInsights:
    global _user_insights
    if _user_insights is None:
        _user_insights = UserInsights()
        await _user_insights.initialize()
    return _user_insights


async def init_user_insights() -> UserInsights:
    insights = UserInsights()
    await insights.initialize()
    return insights
