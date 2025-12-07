from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.core.database import get_database
from backend.core.logs import get_logger


class RevenueTracking:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()

    async def initialize(self):
        return True

    async def kpis(self, days: int = 30) -> Dict[str, Any]:
        start = datetime.utcnow() - timedelta(days=days)
        end = datetime.utcnow()
        try:
            async with self.db.get_session() as session:
                total_res = await session.execute(
                    """
                    SELECT COALESCE(SUM(amount),0) FROM financial_transactions
                    WHERE status = 'completed' AND timestamp BETWEEN %s AND %s
                    """,
                    (start, end),
                )
                total = float(total_res.scalar() or 0.0)
                mrr_res = await session.execute(
                    """
                    SELECT COALESCE(SUM(amount),0) FROM financial_transactions
                    WHERE status = 'completed' AND transaction_type = 'subscription'
                          AND timestamp >= %s
                    """,
                    (datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),),
                )
                mrr = float(mrr_res.scalar() or 0.0)
                subs_res = await session.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                active_subs = int(subs_res.scalar() or 0)
                arpu = (mrr / active_subs) if active_subs > 0 else 0.0
                return {"period_days": days, "revenue": total, "mrr": mrr, "active_subscriptions": active_subs, "arpu": arpu}
        except Exception as e:
            self.logger.error(f"Failed revenue KPIs: {e}")
            return {"period_days": days, "revenue": 0.0, "mrr": 0.0, "active_subscriptions": 0, "arpu": 0.0}


_revenue_tracking: Optional[RevenueTracking] = None


async def get_revenue_tracking() -> RevenueTracking:
    global _revenue_tracking
    if _revenue_tracking is None:
        _revenue_tracking = RevenueTracking()
        await _revenue_tracking.initialize()
    return _revenue_tracking


async def init_revenue_tracking() -> RevenueTracking:
    rt = RevenueTracking()
    await rt.initialize()
    return rt
