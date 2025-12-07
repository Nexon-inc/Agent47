from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.core.database import get_database
from backend.core.logs import get_logger


class FinancialReporting:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()

    async def initialize(self):
        return True

    async def profit_and_loss(self, days: int = 30) -> Dict[str, Any]:
        start = datetime.utcnow() - timedelta(days=days)
        end = datetime.utcnow()
        try:
            async with self.db.get_session() as session:
                rev_res = await session.execute(
                    """
                    SELECT COALESCE(SUM(amount),0) FROM financial_transactions
                    WHERE status = 'completed' AND transaction_type IN ('subscription','payment')
                      AND timestamp BETWEEN %s AND %s
                    """,
                    (start, end),
                )
                revenue = float(rev_res.scalar() or 0.0)
                exp_res = await session.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date BETWEEN %s AND %s", (start.date(), end.date()))
                expenses = float(exp_res.scalar() or 0.0)
                return {"period_days": days, "revenue": revenue, "expenses": expenses, "profit": revenue - expenses}
        except Exception as e:
            self.logger.error(f"Failed P&L: {e}")
            return {"period_days": days, "revenue": 0.0, "expenses": 0.0, "profit": 0.0}


_financial_reporting: Optional[FinancialReporting] = None


async def get_financial_reporting() -> FinancialReporting:
    global _financial_reporting
    if _financial_reporting is None:
        _financial_reporting = FinancialReporting()
        await _financial_reporting.initialize()
    return _financial_reporting


async def init_financial_reporting() -> FinancialReporting:
    fr = FinancialReporting()
    await fr.initialize()
    return fr
