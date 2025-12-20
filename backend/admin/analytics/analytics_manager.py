import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.event_bus import get_kafka, KafkaManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings
from core.billing import get_billing, BillingManager
from core.user_management import get_user_manager, UserManager

logger = get_logger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class TimeRange(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class MetricData:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalyticsReport:
    id: str
    report_type: str
    title: str
    data: Dict[str, Any]
    generated_at: datetime
    time_range: TimeRange
    filters: Dict[str, Any] = field(default_factory=dict)

class AnalyticsManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.billing_manager: Optional[BillingManager] = None
        self.user_manager: Optional[UserManager] = None
        self.settings = get_settings()

        self.metrics_cache: Dict[str, List[MetricData]] = {}
        self.reports_cache: Dict[str, AnalyticsReport] = {}
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AnalyticsManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            self.billing_manager = await get_billing_manager()
            self.user_manager = await get_user_manager()

            await self._setup_analytics_tables()
            await self._initialize_metrics_collection()

            self.logger.info("AnalyticsManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize AnalyticsManager: {str(e)}")
            return False

    async def _setup_analytics_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS analytics_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(255) NOT NULL,
                    metric_value DECIMAL(15,4) NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    labels JSONB,
                    metadata JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS analytics_reports (
                    id VARCHAR(255) PRIMARY KEY,
                    report_type VARCHAR(100) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    data JSONB NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    time_range VARCHAR(50) NOT NULL,
                    filters JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS analytics_dashboards (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    widgets JSONB NOT NULL,
                    created_by VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_public BOOLEAN DEFAULT FALSE
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS analytics_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_name VARCHAR(255) NOT NULL,
                    metric_name VARCHAR(255) NOT NULL,
                    condition VARCHAR(100) NOT NULL,
                    threshold DECIMAL(15,4) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0
                )
            """)

            await session.commit()

    async def _initialize_metrics_collection(self):
        try:
            # Start collecting system metrics
            await self._collect_system_metrics()
            
            # Schedule periodic collection
            asyncio.create_task(self._periodic_metrics_collection())
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics collection: {str(e)}")

    async def _collect_system_metrics(self):
        try:
            if not self.database:
                return

            # Collect user metrics
            if self.user_manager:
                total_users = await self.user_manager.get_user_statistics()
                await self._record_metric("total_users", total_users.get("total_users", 0), MetricType.GAUGE)

            # Collect billing metrics
            if self.billing_manager:
                revenue_data = await self._get_revenue_metrics()
                await self._record_metric("monthly_revenue", revenue_data.get("current_month", 0), MetricType.GAUGE)
                await self._record_metric("total_revenue", revenue_data.get("total", 0), MetricType.GAUGE)

            # Collect system performance metrics
            system_metrics = await self._get_system_performance_metrics()
            for metric_name, value in system_metrics.items():
                await self._record_metric(metric_name, value, MetricType.GAUGE)

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")

    async def _periodic_metrics_collection(self):
        while True:
            try:
                await asyncio.sleep(300)  # Collect every 5 minutes
                await self._collect_system_metrics()
            except Exception as e:
                self.logger.error(f"Periodic metrics collection failed: {str(e)}")

    async def _record_metric(self, name: str, value: float, metric_type: MetricType, 
                           labels: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        try:
            metric_data = MetricData(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {},
                metadata=metadata or {}
            )

            # Cache metric
            if name not in self.metrics_cache:
                self.metrics_cache[name] = []
            self.metrics_cache[name].append(metric_data)

            # Store in database
            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO analytics_metrics (metric_name, metric_value, metric_type, labels, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, value, metric_type.value, json.dumps(labels or {}), json.dumps(metadata or {})))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to record metric {name}: {str(e)}")

    async def _get_revenue_metrics(self) -> Dict[str, float]:
        try:
            if not self.billing_manager:
                return {"current_month": 0.0, "total": 0.0}

            # Get current month revenue
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_revenue = await self.billing_manager.get_revenue_for_period(current_month, datetime.utcnow())

            # Get total revenue
            total_revenue = await self.billing_manager.get_total_revenue()

            return {
                "current_month": current_month_revenue,
                "total": total_revenue
            }

        except Exception as e:
            self.logger.error(f"Failed to get revenue metrics: {str(e)}")
            return {"current_month": 0.0, "total": 0.0}

    async def _get_system_performance_metrics(self) -> Dict[str, float]:
        try:
            metrics = {}
            
            # Database performance
            if self.database:
                db_health = await self.database.health_check()
                metrics["database_response_time"] = db_health.get("response_time", 0.0)
                metrics["database_connections"] = db_health.get("active_connections", 0)

            # Redis performance
            if self.redis:
                redis_health = await self.redis.health_check()
                metrics["redis_response_time"] = redis_health.get("response_time", 0.0)
                metrics["redis_memory_usage"] = redis_health.get("memory_usage", 0.0)

            # Kafka performance
            if self.kafka:
                kafka_health = await self.kafka.health_check()
                metrics["kafka_lag"] = kafka_health.get("consumer_lag", 0)
                metrics["kafka_throughput"] = kafka_health.get("messages_per_second", 0.0)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to get system performance metrics: {str(e)}")
            return {}

    async def get_metric_data(self, metric_name: str, time_range: TimeRange = TimeRange.DAY,
                             filters: Dict[str, Any] = None) -> List[MetricData]:
        try:
            # Check cache first
            if metric_name in self.metrics_cache:
                cached_metrics = self.metrics_cache[metric_name]
                filtered_metrics = self._filter_metrics_by_time_range(cached_metrics, time_range)
                return filtered_metrics

            # Query database
            if not self.database:
                return []

            start_time = self._get_start_time_for_range(time_range)
            
            query = """
                SELECT metric_name, metric_value, timestamp, labels, metadata
                FROM analytics_metrics
                WHERE metric_name = %s AND timestamp >= %s
                ORDER BY timestamp ASC
            """
            params = [metric_name, start_time]

            async with self.database.get_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()

                metrics = []
                for row in rows:
                    metric = MetricData(
                        name=row[0],
                        value=float(row[1]),
                        timestamp=row[2],
                        labels=row[3] if row[3] else {},
                        metadata=row[4] if row[4] else {}
                    )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            self.logger.error(f"Failed to get metric data: {str(e)}")
            return []

    def _filter_metrics_by_time_range(self, metrics: List[MetricData], time_range: TimeRange) -> List[MetricData]:
        start_time = self._get_start_time_for_range(time_range)
        return [m for m in metrics if m.timestamp >= start_time]

    def _get_start_time_for_range(self, time_range: TimeRange) -> datetime:
        now = datetime.utcnow()
        
        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            return now - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=1)

    async def generate_business_report(self, report_type: str, time_range: TimeRange,
                                     filters: Dict[str, Any] = None) -> AnalyticsReport:
        try:
            report_id = str(uuid.uuid4())
            report_data = {}

            if report_type == "revenue_analysis":
                report_data = await self._generate_revenue_report(time_range, filters)
            elif report_type == "user_growth":
                report_data = await self._generate_user_growth_report(time_range, filters)
            elif report_type == "system_performance":
                report_data = await self._generate_system_performance_report(time_range, filters)
            elif report_type == "agent_utilization":
                report_data = await self._generate_agent_utilization_report(time_range, filters)
            else:
                report_data = await self._generate_custom_report(report_type, time_range, filters)

            report = AnalyticsReport(
                id=report_id,
                report_type=report_type,
                title=f"{report_type.replace('_', ' ').title()} Report",
                data=report_data,
                generated_at=datetime.utcnow(),
                time_range=time_range,
                filters=filters or {}
            )

            # Cache report
            self.reports_cache[report_id] = report

            # Store in database
            if self.database:
                async with self.database.get_session() as session:
                    await session.execute("""
                        INSERT INTO analytics_reports (id, report_type, title, data, time_range, filters)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (report_id, report_type, report.title, json.dumps(report_data),
                          time_range.value, json.dumps(filters or {})))
                    await session.commit()

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate business report: {str(e)}")
            raise

    async def _generate_revenue_report(self, time_range: TimeRange, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.billing_manager:
                return {}

            start_time = self._get_start_time_for_range(time_range)
            end_time = datetime.utcnow()

            # Get revenue data
            period_revenue = await self.billing_manager.get_revenue_for_period(start_time, end_time)
            
            # Get subscription data
            subscriptions = await self.billing_manager.get_subscription_statistics(start_time, end_time)
            
            # Get payment data
            payments = await self.billing_manager.get_payment_statistics(start_time, end_time)

            # Calculate growth rate
            previous_period_start = start_time - (end_time - start_time)
            previous_period_revenue = await self.billing_manager.get_revenue_for_period(previous_period_start, start_time)
            
            growth_rate = 0.0
            if previous_period_revenue > 0:
                growth_rate = ((period_revenue - previous_period_revenue) / previous_period_revenue) * 100

            return {
                "period_revenue": period_revenue,
                "previous_period_revenue": previous_period_revenue,
                "growth_rate": growth_rate,
                "subscriptions": subscriptions,
                "payments": payments,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate revenue report: {str(e)}")
            return {}

    async def _generate_user_growth_report(self, time_range: TimeRange, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.user_manager:
                return {}

            start_time = self._get_start_time_for_range(time_range)
            end_time = datetime.utcnow()

            # Get user statistics
            user_stats = await self.user_manager.get_user_statistics(days=(end_time - start_time).days)
            
            # Get user growth by day
            daily_growth = await self._get_daily_user_growth(start_time, end_time)
            
            # Get user tier distribution
            tier_distribution = await self._get_user_tier_distribution()

            return {
                "total_users": user_stats.get("total_users", 0),
                "new_users_period": user_stats.get("new_users_today", 0),
                "daily_growth": daily_growth,
                "tier_distribution": tier_distribution,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate user growth report: {str(e)}")
            return {}

    async def _generate_system_performance_report(self, time_range: TimeRange, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            start_time = self._get_start_time_for_range(time_range)
            end_time = datetime.utcnow()

            # Get system metrics
            system_metrics = await self._get_system_performance_metrics()
            
            # Get performance trends
            performance_trends = await self._get_performance_trends(start_time, end_time)
            
            # Get error rates
            error_rates = await self._get_error_rates(start_time, end_time)

            return {
                "current_metrics": system_metrics,
                "performance_trends": performance_trends,
                "error_rates": error_rates,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate system performance report: {str(e)}")
            return {}

    async def _generate_agent_utilization_report(self, time_range: TimeRange, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            start_time = self._get_start_time_for_range(time_range)
            end_time = datetime.utcnow()

            # Get agent metrics
            agent_metrics = await self._get_agent_metrics(start_time, end_time)
            
            # Get workload distribution
            workload_distribution = await self._get_workload_distribution(start_time, end_time)
            
            # Get agent efficiency
            agent_efficiency = await self._get_agent_efficiency(start_time, end_time)

            return {
                "agent_metrics": agent_metrics,
                "workload_distribution": workload_distribution,
                "agent_efficiency": agent_efficiency,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate agent utilization report: {str(e)}")
            return {}

    async def _generate_custom_report(self, report_type: str, time_range: TimeRange, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            start_time = self._get_start_time_for_range(time_range)
            end_time = datetime.utcnow()

            # Custom report logic based on type
            if report_type == "goal_progress":
                return await self._get_goal_progress_data(start_time, end_time, filters)
            elif report_type == "integration_usage":
                return await self._get_integration_usage_data(start_time, end_time, filters)
            else:
                return {
                    "message": f"Custom report type '{report_type}' not implemented",
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }

        except Exception as e:
            self.logger.error(f"Failed to generate custom report: {str(e)}")
            return {}

    async def _get_daily_user_growth(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        try:
            if not self.database:
                return []

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as new_users
                    FROM users
                    WHERE created_at >= %s AND created_at <= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (start_time, end_time))

                rows = result.fetchall()
                return [{"date": row[0].isoformat(), "new_users": row[1]} for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get daily user growth: {str(e)}")
            return []

    async def _get_user_tier_distribution(self) -> Dict[str, int]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT tier, COUNT(*) as count
                    FROM users
                    WHERE is_active = TRUE
                    GROUP BY tier
                """)

                rows = result.fetchall()
                return {row[0]: row[1] for row in rows}

        except Exception as e:
            self.logger.error(f"Failed to get user tier distribution: {str(e)}")
            return {}

    async def _get_performance_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get response time trends
                result = await session.execute("""
                    SELECT AVG(metric_value) as avg_response_time
                    FROM analytics_metrics
                    WHERE metric_name LIKE '%response_time%' AND timestamp >= %s AND timestamp <= %s
                """, (start_time, end_time))

                avg_response_time = result.scalar() or 0.0

                # Get throughput trends
                result = await session.execute("""
                    SELECT AVG(metric_value) as avg_throughput
                    FROM analytics_metrics
                    WHERE metric_name LIKE '%throughput%' AND timestamp >= %s AND timestamp <= %s
                """, (start_time, end_time))

                avg_throughput = result.scalar() or 0.0

                return {
                    "avg_response_time": avg_response_time,
                    "avg_throughput": avg_throughput
                }

        except Exception as e:
            self.logger.error(f"Failed to get performance trends: {str(e)}")
            return {}

    async def _get_error_rates(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get error counts
                result = await session.execute("""
                    SELECT COUNT(*) as error_count
                    FROM user_errors
                    WHERE timestamp >= %s AND timestamp <= %s
                """, (start_time, end_time))

                error_count = result.scalar() or 0

                # Get total requests (approximate)
                result = await session.execute("""
                    SELECT COUNT(*) as total_requests
                    FROM user_activities
                    WHERE timestamp >= %s AND timestamp <= %s
                """, (start_time, end_time))

                total_requests = result.scalar() or 1

                error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0.0

                return {
                    "error_count": error_count,
                    "total_requests": total_requests,
                    "error_rate": error_rate
                }

        except Exception as e:
            self.logger.error(f"Failed to get error rates: {str(e)}")
            return {}

    async def _get_agent_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get agent workload data
                result = await session.execute("""
                    SELECT agent_name, AVG(active_tasks) as avg_tasks, AVG(memory_usage) as avg_memory, AVG(cpu_usage) as avg_cpu
                    FROM agent_workloads
                    WHERE timestamp >= %s AND timestamp <= %s
                    GROUP BY agent_name
                """, (start_time, end_time))

                rows = result.fetchall()
                agent_metrics = {}
                
                for row in rows:
                    agent_metrics[row[0]] = {
                        "avg_tasks": float(row[1]) if row[1] else 0.0,
                        "avg_memory": float(row[2]) if row[2] else 0.0,
                        "avg_cpu": float(row[3]) if row[3] else 0.0
                    }

                return agent_metrics

        except Exception as e:
            self.logger.error(f"Failed to get agent metrics: {str(e)}")
            return {}

    async def _get_workload_distribution(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get task distribution
                result = await session.execute("""
                    SELECT task_type, COUNT(*) as count
                    FROM agent_tasks
                    WHERE assigned_at >= %s AND assigned_at <= %s
                    GROUP BY task_type
                """, (start_time, end_time))

                rows = result.fetchall()
                task_distribution = {row[0]: row[1] for row in rows}

                return {
                    "task_distribution": task_distribution,
                    "total_tasks": sum(task_distribution.values())
                }

        except Exception as e:
            self.logger.error(f"Failed to get workload distribution: {str(e)}")
            return {}

    async def _get_agent_efficiency(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get completion rates
                result = await session.execute("""
                    SELECT agent_name, 
                           COUNT(*) as total_tasks,
                           COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks
                    FROM agent_tasks
                    WHERE assigned_at >= %s AND assigned_at <= %s
                    GROUP BY agent_name
                """, (start_time, end_time))

                rows = result.fetchall()
                efficiency = {}
                
                for row in rows:
                    total = row[1]
                    completed = row[2]
                    efficiency[row[0]] = (completed / total * 100) if total > 0 else 0.0

                return efficiency

        except Exception as e:
            self.logger.error(f"Failed to get agent efficiency: {str(e)}")
            return {}

    async def _get_goal_progress_data(self, start_time: datetime, end_time: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get goal progress
                result = await session.execute("""
                    SELECT goal_type, status, COUNT(*) as count
                    FROM goals
                    WHERE created_at >= %s AND created_at <= %s
                    GROUP BY goal_type, status
                """, (start_time, end_time))

                rows = result.fetchall()
                goal_progress = {}
                
                for row in rows:
                    goal_type = row[0]
                    status = row[1]
                    count = row[2]
                    
                    if goal_type not in goal_progress:
                        goal_progress[goal_type] = {}
                    
                    goal_progress[goal_type][status] = count

                return {
                    "goal_progress": goal_progress,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }

        except Exception as e:
            self.logger.error(f"Failed to get goal progress data: {str(e)}")
            return {}

    async def _get_integration_usage_data(self, start_time: datetime, end_time: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            async with self.database.get_session() as session:
                # Get integration usage
                result = await session.execute("""
                    SELECT integration_name, COUNT(*) as usage_count
                    FROM integration_usage
                    WHERE timestamp >= %s AND timestamp <= %s
                    GROUP BY integration_name
                    ORDER BY usage_count DESC
                """, (start_time, end_time))

                rows = result.fetchall()
                integration_usage = {row[0]: row[1] for row in rows}

                return {
                    "integration_usage": integration_usage,
                    "total_usage": sum(integration_usage.values()),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }

        except Exception as e:
            self.logger.error(f"Failed to get integration usage data: {str(e)}")
            return {}

    async def get_report(self, report_id: str) -> Optional[AnalyticsReport]:
        if report_id in self.reports_cache:
            return self.reports_cache[report_id]

        if not self.database:
            return None

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, report_type, title, data, generated_at, time_range, filters
                    FROM analytics_reports WHERE id = %s
                """, (report_id,))

                row = result.fetchone()
                if row:
                    report = AnalyticsReport(
                        id=row[0],
                        report_type=row[1],
                        title=row[2],
                        data=row[3] if row[3] else {},
                        generated_at=row[4],
                        time_range=TimeRange(row[5]),
                        filters=row[6] if row[6] else {}
                    )
                    self.reports_cache[report_id] = report
                    return report

        except Exception as e:
            self.logger.error(f"Failed to get report: {str(e)}")

        return None

    async def close(self):
        self.logger.info("Closing AnalyticsManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_analytics_manager: Optional[AnalyticsManager] = None

async def init_analytics_manager() -> AnalyticsManager:
    global _analytics_manager
    if not _analytics_manager:
        _analytics_manager = AnalyticsManager()
        await _analytics_manager.initialize()
    return _analytics_manager

async def get_analytics_manager() -> AnalyticsManager:
    global _analytics_manager
    if not _analytics_manager:
        _analytics_manager = await init_analytics_manager()
    return _analytics_manager
