import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings
from core.billing import get_billing, BillingManager

logger = get_logger(__name__)

class TransactionType(Enum):
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    ADJUSTMENT = "adjustment"
    EXPENSE = "expense"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

@dataclass
class FinancialTransaction:
    id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    user_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    reference_id: Optional[str] = None

@dataclass
class FinancialMetrics:
    total_revenue: float = 0.0
    monthly_recurring_revenue: float = 0.0
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    churn_rate: float = 0.0
    average_revenue_per_user: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0

class FinanceManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.billing_manager: Optional[BillingManager] = None
        self.settings = get_settings()

        self.financial_transactions: Dict[str, FinancialTransaction] = {}
        self.financial_metrics: FinancialMetrics = FinancialMetrics()
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing FinanceManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            self.billing_manager = await get_billing_manager()

            await self._setup_finance_tables()
            await self._load_financial_data()
            await self._start_financial_monitoring()

            self.logger.info("FinanceManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize FinanceManager: {str(e)}")
            return False

    async def _setup_finance_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS financial_transactions (
                    id VARCHAR(255) PRIMARY KEY,
                    transaction_type VARCHAR(100) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    description TEXT,
                    metadata JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    reference_id VARCHAR(255)
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS financial_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(15,4) NOT NULL,
                    currency VARCHAR(10) DEFAULT 'USD',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    period VARCHAR(50) NOT NULL
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS revenue_streams (
                    id SERIAL PRIMARY KEY,
                    stream_name VARCHAR(255) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency VARCHAR(10) DEFAULT 'USD',
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    subscription_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS expense_categories (
                    id SERIAL PRIMARY KEY,
                    category_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    budget_limit DECIMAL(15,2),
                    currency VARCHAR(10) DEFAULT 'USD',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    category_id INTEGER NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency VARCHAR(10) DEFAULT 'USD',
                    description TEXT NOT NULL,
                    vendor VARCHAR(255),
                    invoice_number VARCHAR(255),
                    expense_date DATE NOT NULL,
                    approved_by VARCHAR(255),
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES expense_categories(id)
                )
            """)

            await session.commit()

    async def _load_financial_data(self):
        try:
            await self._load_financial_transactions()
            await self._calculate_financial_metrics()
        except Exception as e:
            self.logger.error(f"Failed to load financial data: {str(e)}")

    async def _load_financial_transactions(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, transaction_type, amount, currency, status, user_id,
                           description, metadata, timestamp, processed_at, reference_id
                    FROM financial_transactions
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)

                rows = result.fetchall()
                for row in rows:
                    transaction = FinancialTransaction(
                        id=row[0],
                        transaction_type=TransactionType(row[1]),
                        amount=float(row[2]),
                        currency=row[3],
                        status=TransactionStatus(row[4]),
                        user_id=row[5],
                        description=row[6],
                        metadata=row[7] if row[7] else {},
                        timestamp=row[8],
                        processed_at=row[9],
                        reference_id=row[10]
                    )
                    self.financial_transactions[transaction.id] = transaction

        except Exception as e:
            self.logger.error(f"Failed to load financial transactions: {str(e)}")

    async def _calculate_financial_metrics(self):
        try:
            if not self.database:
                return

            # Use billing manager for accurate calculations
            if self.billing_manager:
                revenue_analytics = await self.billing_manager.get_revenue_analytics()
                
                # Update metrics with real data
                self.financial_metrics.total_revenue = revenue_analytics.get("total_revenue", 0.0)
                self.financial_metrics.monthly_recurring_revenue = revenue_analytics.get("monthly_recurring_revenue", 0.0)
                self.financial_metrics.total_subscriptions = revenue_analytics.get("total_subscriptions", 0)
                self.financial_metrics.active_subscriptions = revenue_analytics.get("active_subscriptions", 0)
                self.financial_metrics.churn_rate = revenue_analytics.get("churn_rate", 0.0)
                self.financial_metrics.average_revenue_per_user = revenue_analytics.get("average_revenue_per_user", 0.0)
            else:
                # Fallback to direct database calculations
                total_revenue = await self._calculate_total_revenue()
                mrr = await self._calculate_monthly_recurring_revenue()
                subscription_metrics = await self._calculate_subscription_metrics()
                
                self.financial_metrics.total_revenue = total_revenue
                self.financial_metrics.monthly_recurring_revenue = mrr
                self.financial_metrics.total_subscriptions = subscription_metrics.get("total", 0)
                self.financial_metrics.active_subscriptions = subscription_metrics.get("active", 0)
                self.financial_metrics.churn_rate = subscription_metrics.get("churn_rate", 0.0)
                self.financial_metrics.average_revenue_per_user = subscription_metrics.get("arpu", 0.0)
            
            # Calculate expenses
            total_expenses = await self._calculate_total_expenses()
            self.financial_metrics.total_expenses = total_expenses
            self.financial_metrics.net_profit = self.financial_metrics.total_revenue - total_expenses

        except Exception as e:
            self.logger.error(f"Failed to calculate financial metrics: {str(e)}")

    async def _start_financial_monitoring(self):
        try:
            # Start periodic metrics calculation
            asyncio.create_task(self._periodic_metrics_calculation())
            
        except Exception as e:
            self.logger.error(f"Failed to start financial monitoring: {str(e)}")

    async def _periodic_metrics_calculation(self):
        while True:
            try:
                await asyncio.sleep(3600)  # Calculate every hour
                await self._calculate_financial_metrics()
                await self._save_financial_metrics()
            except Exception as e:
                self.logger.error(f"Periodic metrics calculation failed: {str(e)}")

    async def _calculate_total_revenue(self) -> float:
        try:
            if not self.database:
                return 0.0

            async with self.database.get_session() as session:
                # Sum from real payments table
                result = await session.execute(text("""
                    SELECT COALESCE(SUM(amount_usd), 0)
                    FROM payments
                    WHERE status = 'successful'
                """))
                
                return float(result.scalar() or 0.0)

        except Exception as e:
            self.logger.error(f"Failed to calculate total revenue: {str(e)}")
            return 0.0

    async def _calculate_monthly_recurring_revenue(self) -> float:
        try:
            if not self.database:
                return 0.0

            # Get current month's recurring revenue
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT COALESCE(SUM(amount_usd), 0)
                    FROM payments
                    WHERE status = 'successful' 
                    AND created_at >= :start_date
                """), {"start_date": current_month_start})
                
                return float(result.scalar() or 0.0)

        except Exception as e:
            self.logger.error(f"Failed to calculate MRR: {str(e)}")
            return 0.0

    async def _calculate_subscription_metrics(self) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Total subscriptions
                result = await session.execute(text("SELECT COUNT(*) FROM subscriptions"))
                total_subscriptions = result.scalar() or 0

                # Active subscriptions
                result = await session.execute(text("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"))
                active_subscriptions = result.scalar() or 0

                # Calculate churn rate (simplified)
                if total_subscriptions > 0:
                    churn_rate = ((total_subscriptions - active_subscriptions) / total_subscriptions) * 100
                else:
                    churn_rate = 0.0

                # Calculate ARPU (Average Revenue Per User)
                result = await session.execute(text("""
                    SELECT COALESCE(AVG(amount_usd), 0)
                    FROM payments
                    WHERE status = 'successful'
                """))
                arpu = float(result.scalar() or 0.0)

                return {
                    "total": total_subscriptions,
                    "active": active_subscriptions,
                    "churn_rate": churn_rate,
                    "arpu": arpu
                }

        except Exception as e:
            self.logger.error(f"Failed to calculate subscription metrics: {str(e)}")
            return {}

    async def _calculate_total_expenses(self) -> float:
        try:
            if not self.database:
                return 0.0

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM expenses
                """)
                
                return float(result.scalar() or 0.0)

        except Exception as e:
            self.logger.error(f"Failed to calculate total expenses: {str(e)}")
            return 0.0

    async def _save_financial_metrics(self):
        try:
            if not self.database:
                return

            current_time = datetime.utcnow()
            
            async with self.database.get_session() as session:
                # Save current metrics
                metrics_to_save = [
                    ("total_revenue", self.financial_metrics.total_revenue, "USD"),
                    ("monthly_recurring_revenue", self.financial_metrics.monthly_recurring_revenue, "USD"),
                    ("total_subscriptions", self.financial_metrics.total_subscriptions, "count"),
                    ("active_subscriptions", self.financial_metrics.active_subscriptions, "count"),
                    ("churn_rate", self.financial_metrics.churn_rate, "percentage"),
                    ("average_revenue_per_user", self.financial_metrics.average_revenue_per_user, "USD"),
                    ("total_expenses", self.financial_metrics.total_expenses, "USD"),
                    ("net_profit", self.financial_metrics.net_profit, "USD")
                ]

                for metric_name, metric_value, currency in metrics_to_save:
                    await session.execute("""
                        INSERT INTO financial_metrics (metric_name, metric_value, currency, timestamp, period)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (metric_name, metric_value, currency, current_time, "current"))

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to save financial metrics: {str(e)}")

    async def record_transaction(self, transaction_type: TransactionType, amount: float, currency: str,
                               user_id: Optional[str] = None, description: str = "", 
                               metadata: Dict[str, Any] = None, reference_id: Optional[str] = None) -> str:
        try:
            transaction_id = str(uuid.uuid4())
            
            transaction = FinancialTransaction(
                id=transaction_id,
                transaction_type=transaction_type,
                amount=amount,
                currency=currency,
                status=TransactionStatus.PENDING,
                user_id=user_id,
                description=description,
                metadata=metadata or {},
                reference_id=reference_id
            )

            # Add to cache
            self.financial_transactions[transaction_id] = transaction

            # Store in database
            if not self.database:
                return transaction_id

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO financial_transactions (id, transaction_type, amount, currency, status,
                                                      user_id, description, metadata, reference_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    transaction_id, transaction_type.value, amount, currency, TransactionStatus.PENDING.value,
                    user_id, description, json.dumps(metadata or {}), reference_id
                ))
                await session.commit()

            self.logger.info(f"Financial transaction recorded: {transaction_id}")
            return transaction_id

        except Exception as e:
            self.logger.error(f"Failed to record transaction: {str(e)}")
            raise

    async def update_transaction_status(self, transaction_id: str, new_status: TransactionStatus,
                                      processed_at: Optional[datetime] = None) -> bool:
        try:
            if transaction_id not in self.financial_transactions:
                return False

            transaction = self.financial_transactions[transaction_id]
            old_status = transaction.status
            transaction.status = new_status
            
            if processed_at:
                transaction.processed_at = processed_at
            elif new_status == TransactionStatus.COMPLETED:
                transaction.processed_at = datetime.utcnow()

            # Update database
            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE financial_transactions
                    SET status = %s, processed_at = %s
                    WHERE id = %s
                """, (new_status.value, transaction.processed_at, transaction_id))
                await session.commit()

            # Recalculate metrics if status changed significantly
            if old_status != new_status and new_status in [TransactionStatus.COMPLETED, TransactionStatus.FAILED]:
                await self._calculate_financial_metrics()

            self.logger.info(f"Transaction {transaction_id} status updated to {new_status.value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update transaction status: {str(e)}")
            return False

    async def get_financial_overview(self) -> Dict[str, Any]:
        try:
            overview = {
                "current_metrics": {
                    "total_revenue": self.financial_metrics.total_revenue,
                    "monthly_recurring_revenue": self.financial_metrics.monthly_recurring_revenue,
                    "total_subscriptions": self.financial_metrics.total_subscriptions,
                    "active_subscriptions": self.financial_metrics.active_subscriptions,
                    "churn_rate": self.financial_metrics.churn_rate,
                    "average_revenue_per_user": self.financial_metrics.average_revenue_per_user,
                    "total_expenses": self.financial_metrics.total_expenses,
                    "net_profit": self.financial_metrics.net_profit
                },
                "recent_transactions": [],
                "revenue_trends": {},
                "expense_breakdown": {}
            }

            # Get recent transactions
            recent_transactions = await self.get_recent_transactions(limit=10)
            overview["recent_transactions"] = recent_transactions

            # Get revenue trends
            revenue_trends = await self._get_revenue_trends()
            overview["revenue_trends"] = revenue_trends

            # Get expense breakdown
            expense_breakdown = await self._get_expense_breakdown()
            overview["expense_breakdown"] = expense_breakdown

            return overview

        except Exception as e:
            self.logger.error(f"Failed to get financial overview: {str(e)}")
            return {}

    async def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if not self.database:
                return []
                
            async with self.database.get_session() as session:
                # Fetch recent successful payments
                result = await session.execute(text("""
                    SELECT id, amount_usd, currency, status, created_at, 'payment' as type
                    FROM payments
                    ORDER BY created_at DESC
                    LIMIT :limit
                """), {"limit": limit})
                
                payments = []
                for row in result.fetchall():
                    payments.append({
                        "id": str(row[0]),
                        "amount": float(row[1]),
                        "currency": row[2],
                        "status": row[3],
                        "timestamp": row[4].isoformat() if row[4] else None,
                        "type": row[5],
                        "description": f"Payment #{row[0]}"
                    })
                return payments

        except Exception as e:
            self.logger.error(f"Failed to get recent transactions: {str(e)}")
            return []

    async def _get_revenue_trends(self) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            # Get revenue for last 6 months
            trends = {}
            for i in range(6):
                month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end.replace(day=1) - timedelta(seconds=1)

                async with self.database.get_session() as session:
                    result = await session.execute("""
                        SELECT COALESCE(SUM(amount), 0)
                        FROM financial_transactions
                        WHERE status = 'completed' 
                        AND transaction_type IN ('subscription', 'payment')
                        AND timestamp >= %s AND timestamp <= %s
                    """, (month_start, month_end))
                    
                    month_revenue = float(result.scalar() or 0.0)
                    month_key = month_start.strftime("%Y-%m")
                    trends[month_key] = month_revenue

            return trends

        except Exception as e:
            self.logger.error(f"Failed to get revenue trends: {str(e)}")
            return {}

    async def _get_expense_breakdown(self) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT c.category_name, COALESCE(SUM(e.amount), 0) as total_amount
                    FROM expense_categories c
                    LEFT JOIN expenses e ON c.id = e.category_id
                    WHERE c.is_active = TRUE
                    GROUP BY c.id, c.category_name
                    ORDER BY total_amount DESC
                """)

                rows = result.fetchall()
                breakdown = {}
                
                for row in rows:
                    breakdown[row[0]] = float(row[1])

                return breakdown

        except Exception as e:
            self.logger.error(f"Failed to get expense breakdown: {str(e)}")
            return {}

    async def get_financial_statistics(self, days: int = 30) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.database.get_session() as session:
                # Total transactions
                result = await session.execute("""
                    SELECT COUNT(*) FROM financial_transactions WHERE timestamp >= %s
                """, (start_date,))
                total_transactions = result.scalar()

                # Total revenue
                result = await session.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM financial_transactions
                    WHERE timestamp >= %s AND status = 'completed' 
                    AND transaction_type IN ('subscription', 'payment')
                """, (start_date,))
                period_revenue = float(result.scalar() or 0.0)

                # Total expenses
                result = await session.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date >= %s
                """, (start_date.date(),))
                period_expenses = float(result.scalar() or 0.0)

                # Transaction types breakdown
                result = await session.execute("""
                    SELECT transaction_type, COUNT(*) FROM financial_transactions
                    WHERE timestamp >= %s GROUP BY transaction_type
                """, (start_date,))
                transaction_types = {row[0]: row[1] for row in result.fetchall()}

                return {
                    "total_transactions": total_transactions,
                    "period_revenue": period_revenue,
                    "period_expenses": period_expenses,
                    "period_profit": period_revenue - period_expenses,
                    "transaction_types": transaction_types,
                    "period_days": days
                }

        except Exception as e:
            self.logger.error(f"Failed to get financial statistics: {str(e)}")
            return {}

    async def close(self):
        self.logger.info("Closing FinanceManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_finance_manager: Optional[FinanceManager] = None

async def init_finance_manager() -> FinanceManager:
    global _finance_manager
    if not _finance_manager:
        _finance_manager = FinanceManager()
        await _finance_manager.initialize()
    return _finance_manager

async def get_finance_manager() -> FinanceManager:
    global _finance_manager
    if not _finance_manager:
        _finance_manager = await init_finance_manager()
    return _finance_manager
