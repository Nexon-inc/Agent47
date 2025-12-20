from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.database import get_database
from core.logs import get_logger


class IntegrationAnalytics:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()

    async def initialize(self):
        return True

    async def usage_summary(self, days: int = 7) -> Dict[str, Any]:
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            async with self.db.get_session() as session:
                result = await session.execute(
                    """
                    SELECT integration_name,
                           COUNT(*) total,
                           COUNT(CASE WHEN success THEN 1 END) ok,
                           AVG(latency_ms) avg_lat
                    FROM integration_metrics
                    WHERE timestamp >= %s
                    GROUP BY integration_name
                    ORDER BY total DESC
                    """,
                    (cutoff,),
                )
                rows = result.fetchall()
                summary = {}
                for r in rows:
                    total = int(r.total or 0)
                    ok = int(r.ok or 0)
                    summary[r.integration_name] = {
                        "calls": total,
                        "success": ok,
                        "errors": total - ok,
                        "avg_latency_ms": float(r.avg_lat or 0.0),
                        "success_rate": (ok / total * 100.0) if total > 0 else 0.0,
                    }
                return {"period_days": days, "integrations": summary}
        except Exception as e:
            self.logger.error(f"Failed integration usage summary: {e}")
            return {}


_integration_analytics: Optional[IntegrationAnalytics] = None


async def get_integration_analytics() -> IntegrationAnalytics:
    global _integration_analytics
    if _integration_analytics is None:
        _integration_analytics = IntegrationAnalytics()
        await _integration_analytics.initialize()
    return _integration_analytics


async def init_integration_analytics() -> IntegrationAnalytics:
    ia = IntegrationAnalytics()
    await ia.initialize()
    return ia
