from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.core.database import get_database
from backend.core.logs import get_logger


class ExpenseManagement:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()

    async def initialize(self):
        return True

    async def create_category(self, name: str, description: Optional[str] = None, budget_limit: Optional[float] = None, currency: str = "USD") -> bool:
        async with self.db.get_session() as session:
            await session.execute(
                """
                INSERT INTO expense_categories (category_name, description, budget_limit, currency)
                VALUES (:name, :desc, :limit, :cur)
                """,
                {"name": name, "desc": description, "limit": budget_limit, "cur": currency},
            )
            await session.commit()
            return True

    async def add_expense(self, category_id: int, amount: float, description: str, vendor: Optional[str] = None, invoice_number: Optional[str] = None, currency: str = "USD") -> bool:
        async with self.db.get_session() as session:
            await session.execute(
                """
                INSERT INTO expenses (category_id, amount, currency, description, vendor, invoice_number, expense_date)
                VALUES (:cid, :amt, :cur, :desc, :vendor, :inv, :date)
                """,
                {"cid": category_id, "amt": amount, "cur": currency, "desc": description, "vendor": vendor, "inv": invoice_number, "date": datetime.utcnow().date()},
            )
            await session.commit()
            return True

    async def category_spend(self) -> Dict[str, float]:
        async with self.db.get_session() as session:
            res = await session.execute(
                """
                SELECT c.category_name, COALESCE(SUM(e.amount),0) total
                FROM expense_categories c LEFT JOIN expenses e ON c.id = e.category_id
                GROUP BY c.category_name
                ORDER BY total DESC
                """
            )
            rows = res.fetchall()
            return {row[0]: float(row[1]) for row in rows}


_expense_management: Optional[ExpenseManagement] = None


async def get_expense_management() -> ExpenseManagement:
    global _expense_management
    if _expense_management is None:
        _expense_management = ExpenseManagement()
        await _expense_management.initialize()
    return _expense_management


async def init_expense_management() -> ExpenseManagement:
    em = ExpenseManagement()
    await em.initialize()
    return em
