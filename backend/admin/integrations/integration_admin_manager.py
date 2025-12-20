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
from core.integrations import get_integration_manager, IntegrationManager

logger = get_logger(__name__)

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    RATE_LIMITED = "rate_limited"

class IntegrationHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"

@dataclass
class IntegrationMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request: Optional[datetime] = None
    error_rate: float = 0.0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

@dataclass
class IntegrationAlert:
    id: str
    integration_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class IntegrationAdminManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.integration_manager: Optional[IntegrationManager] = None
        self.settings = get_settings()

        self.integration_metrics: Dict[str, IntegrationMetrics] = {}
        self.integration_alerts: Dict[str, IntegrationAlert] = {}
        self.integration_status: Dict[str, IntegrationStatus] = {}
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing IntegrationAdminManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            self.integration_manager = await get_integration_manager()

            await self._setup_integration_admin_tables()
            await self._load_integration_data()
            await self._start_integration_monitoring()

            self.logger.info("IntegrationAdminManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize IntegrationAdminManager: {str(e)}")
            return False

    async def _setup_integration_admin_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS integration_metrics (
                    id SERIAL PRIMARY KEY,
                    integration_id VARCHAR(255) NOT NULL,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    failed_requests INTEGER DEFAULT 0,
                    avg_response_time DECIMAL(10,3) DEFAULT 0.0,
                    last_request TIMESTAMP,
                    error_rate DECIMAL(5,2) DEFAULT 0.0,
                    rate_limit_remaining INTEGER,
                    rate_limit_reset TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS integration_alerts (
                    id VARCHAR(255) PRIMARY KEY,
                    integration_id VARCHAR(255) NOT NULL,
                    alert_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by VARCHAR(255),
                    resolved_at TIMESTAMP,
                    metadata JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS integration_health_checks (
                    id SERIAL PRIMARY KEY,
                    integration_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    response_time DECIMAL(10,3),
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS integration_config_changes (
                    id SERIAL PRIMARY KEY,
                    integration_id VARCHAR(255) NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    change_type VARCHAR(100) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS integration_usage_logs (
                    id SERIAL PRIMARY KEY,
                    integration_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    operation VARCHAR(100) NOT NULL,
                    request_data JSONB,
                    response_data JSONB,
                    response_time DECIMAL(10,3),
                    status VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET
                )
            """)

            await session.commit()

    async def _load_integration_data(self):
        try:
            await self._load_integration_metrics()
            await self._load_integration_alerts()
            await self._load_integration_status()
        except Exception as e:
            self.logger.error(f"Failed to load integration data: {str(e)}")

    async def _load_integration_metrics(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT integration_id, total_requests, successful_requests, failed_requests,
                           avg_response_time, last_request, error_rate, rate_limit_remaining, rate_limit_reset
                    FROM integration_metrics
                    ORDER BY timestamp DESC
                """)

                rows = result.fetchall()
                for row in rows:
                    metrics = IntegrationMetrics(
                        total_requests=row[1],
                        successful_requests=row[2],
                        failed_requests=row[3],
                        avg_response_time=float(row[4]) if row[4] else 0.0,
                        last_request=row[5],
                        error_rate=float(row[6]) if row[6] else 0.0,
                        rate_limit_remaining=row[7],
                        rate_limit_reset=row[8]
                    )
                    self.integration_metrics[row[0]] = metrics

        except Exception as e:
            self.logger.error(f"Failed to load integration metrics: {str(e)}")

    async def _load_integration_alerts(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, integration_id, alert_type, severity, message, timestamp,
                           resolved, resolved_by, resolved_at, metadata
                    FROM integration_alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                """)

                rows = result.fetchall()
                for row in rows:
                    alert = IntegrationAlert(
                        id=row[0],
                        integration_id=row[1],
                        alert_type=row[2],
                        severity=row[3],
                        message=row[4],
                        timestamp=row[5],
                        resolved=row[6],
                        resolved_by=row[7],
                        resolved_at=row[8],
                        metadata=row[9] if row[9] else {}
                    )
                    self.integration_alerts[alert.id] = alert

        except Exception as e:
            self.logger.error(f"Failed to load integration alerts: {str(e)}")

    async def _load_integration_status(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT integration_id, status
                    FROM integration_health_checks
                    WHERE timestamp = (
                        SELECT MAX(timestamp) FROM integration_health_checks h2 
                        WHERE h2.integration_id = integration_health_checks.integration_id
                    )
                """)

                rows = result.fetchall()
                for row in rows:
                    self.integration_status[row[0]] = IntegrationStatus(row[1])

        except Exception as e:
            self.logger.error(f"Failed to load integration status: {str(e)}")

    async def _start_integration_monitoring(self):
        try:
            # Start periodic health checks
            asyncio.create_task(self._periodic_health_checks())
            
            # Start metrics collection
            asyncio.create_task(self._periodic_metrics_collection())
            
        except Exception as e:
            self.logger.error(f"Failed to start integration monitoring: {str(e)}")

    async def _periodic_health_checks(self):
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._perform_health_checks()
            except Exception as e:
                self.logger.error(f"Periodic health checks failed: {str(e)}")

    async def _periodic_metrics_collection(self):
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                await self._collect_integration_metrics()
            except Exception as e:
                self.logger.error(f"Periodic metrics collection failed: {str(e)}")

    async def _perform_health_checks(self):
        try:
            if not self.integration_manager:
                return

            integrations = await self.integration_manager.get_all_integrations()
            
            for integration in integrations:
                health_status = await self._check_integration_health(integration)
                await self._update_integration_status(integration.id, health_status)

        except Exception as e:
            self.logger.error(f"Failed to perform health checks: {str(e)}")

    async def _check_integration_health(self, integration) -> IntegrationHealth:
        try:
            # Basic health check - could be expanded based on integration type
            if not integration.is_active:
                return IntegrationHealth.OFFLINE

            # Check if integration has recent activity
            if integration.id in self.integration_metrics:
                metrics = self.integration_metrics[integration.id]
                if metrics.last_request:
                    time_since_last = datetime.utcnow() - metrics.last_request
                    if time_since_last > timedelta(hours=1):
                        return IntegrationHealth.DEGRADED

            # Check error rate
            if integration.id in self.integration_metrics:
                metrics = self.integration_metrics[integration.id]
                if metrics.error_rate > 10.0:  # More than 10% error rate
                    return IntegrationHealth.UNHEALTHY

            return IntegrationHealth.HEALTHY

        except Exception as e:
            self.logger.error(f"Failed to check integration health: {str(e)}")
            return IntegrationHealth.UNHEALTHY

    async def _update_integration_status(self, integration_id: str, health_status: IntegrationHealth):
        try:
            self.integration_status[integration_id] = health_status

            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO integration_health_checks (integration_id, status, timestamp)
                    VALUES (%s, %s, %s)
                """, (integration_id, health_status.value, datetime.utcnow()))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to update integration status: {str(e)}")

    async def _collect_integration_metrics(self):
        try:
            if not self.integration_manager:
                return

            integrations = await self.integration_manager.get_all_integrations()
            
            for integration in integrations:
                metrics = await self._get_integration_metrics(integration.id)
                if metrics:
                    self.integration_metrics[integration.id] = metrics
                    await self._save_integration_metrics(integration.id, metrics)

        except Exception as e:
            self.logger.error(f"Failed to collect integration metrics: {str(e)}")

    async def _get_integration_metrics(self, integration_id: str) -> Optional[IntegrationMetrics]:
        try:
            if not self.database:
                return None

            async with self.database.get_session() as session:
                # Get recent usage logs
                result = await session.execute("""
                    SELECT COUNT(*) as total_requests,
                           COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_requests,
                           COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_requests,
                           AVG(response_time) as avg_response_time,
                           MAX(timestamp) as last_request
                    FROM integration_usage_logs
                    WHERE integration_id = %s AND timestamp >= %s
                """, (integration_id, datetime.utcnow() - timedelta(hours=1)))

                row = result.fetchone()
                if row and row[0] > 0:
                    total_requests = row[0]
                    successful_requests = row[1]
                    failed_requests = row[2]
                    avg_response_time = float(row[3]) if row[3] else 0.0
                    last_request = row[4]
                    
                    error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0

                    return IntegrationMetrics(
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        failed_requests=failed_requests,
                        avg_response_time=avg_response_time,
                        last_request=last_request,
                        error_rate=error_rate
                    )

            return None

        except Exception as e:
            self.logger.error(f"Failed to get integration metrics: {str(e)}")
            return None

    async def _save_integration_metrics(self, integration_id: str, metrics: IntegrationMetrics):
        try:
            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO integration_metrics (integration_id, total_requests, successful_requests,
                                                   failed_requests, avg_response_time, last_request,
                                                   error_rate, rate_limit_remaining, rate_limit_reset)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    integration_id, metrics.total_requests, metrics.successful_requests,
                    metrics.failed_requests, metrics.avg_response_time, metrics.last_request,
                    metrics.error_rate, metrics.rate_limit_remaining, metrics.rate_limit_reset
                ))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to save integration metrics: {str(e)}")

    async def get_integration_overview(self) -> Dict[str, Any]:
        try:
            if not self.integration_manager:
                return {}

            integrations = await self.integration_manager.get_all_integrations()
            
            overview = {
                "total_integrations": len(integrations),
                "active_integrations": 0,
                "integrations_by_status": {},
                "integrations_by_health": {},
                "recent_alerts": [],
                "performance_summary": {}
            }

            for integration in integrations:
                # Count by status
                status = self.integration_status.get(integration.id, IntegrationStatus.INACTIVE)
                if status == IntegrationStatus.ACTIVE:
                    overview["active_integrations"] += 1

                if status.value not in overview["integrations_by_status"]:
                    overview["integrations_by_status"][status.value] = 0
                overview["integrations_by_status"][status.value] += 1

                # Count by health
                health = self.integration_status.get(integration.id, IntegrationHealth.OFFLINE)
                if health.value not in overview["integrations_by_health"]:
                    overview["integrations_by_health"][health.value] = 0
                overview["integrations_by_health"][health.value] += 1

                # Get metrics
                if integration.id in self.integration_metrics:
                    metrics = self.integration_metrics[integration.id]
                    overview["performance_summary"][integration.id] = {
                        "name": integration.name,
                        "total_requests": metrics.total_requests,
                        "error_rate": metrics.error_rate,
                        "avg_response_time": metrics.avg_response_time,
                        "last_request": metrics.last_request.isoformat() if metrics.last_request else None
                    }

            # Get recent alerts
            recent_alerts = await self.get_recent_alerts(limit=10)
            overview["recent_alerts"] = recent_alerts

            return overview

        except Exception as e:
            self.logger.error(f"Failed to get integration overview: {str(e)}")
            return {}

    async def get_integration_details(self, integration_id: str) -> Dict[str, Any]:
        try:
            if not self.integration_manager:
                return {}

            integration = await self.integration_manager.get_integration(integration_id)
            if not integration:
                return {}

            # Get metrics
            metrics = self.integration_metrics.get(integration_id)
            
            # Get status
            status = self.integration_status.get(integration_id, IntegrationStatus.INACTIVE)
            
            # Get recent alerts
            recent_alerts = await self.get_integration_alerts(integration_id, limit=5)
            
            # Get recent usage logs
            recent_logs = await self.get_integration_usage_logs(integration_id, limit=20)

            details = {
                "id": integration.id,
                "name": integration.name,
                "type": integration.integration_type.value,
                "status": status.value,
                "is_active": integration.is_active,
                "created_at": integration.created_at.isoformat(),
                "updated_at": integration.updated_at.isoformat(),
                "metrics": metrics.__dict__ if metrics else {},
                "recent_alerts": recent_alerts,
                "recent_usage": recent_logs
            }

            return details

        except Exception as e:
            self.logger.error(f"Failed to get integration details: {str(e)}")
            return {}

    async def update_integration_config(self, integration_id: str, config_updates: Dict[str, Any],
                                      admin_user_id: str, reason: str = "") -> bool:
        try:
            if not self.integration_manager:
                return False

            # Get current config
            integration = await self.integration_manager.get_integration(integration_id)
            if not integration:
                return False

            # Update configuration
            success = await self.integration_manager.update_integration_config(integration_id, config_updates)
            
            if success:
                # Log configuration change
                await self._log_config_change(integration_id, admin_user_id, "config_update", 
                                           str(integration.config), str(config_updates), reason)

            return success

        except Exception as e:
            self.logger.error(f"Failed to update integration config: {str(e)}")
            return False

    async def _log_config_change(self, integration_id: str, admin_user_id: str, change_type: str,
                               old_value: str, new_value: str, reason: str = ""):
        try:
            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO integration_config_changes (integration_id, admin_user_id, change_type, old_value, new_value, reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (integration_id, admin_user_id, change_type, old_value, new_value, reason))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to log config change: {str(e)}")

    async def create_integration_alert(self, integration_id: str, alert_type: str, severity: str,
                                     message: str, metadata: Dict[str, Any] = None) -> str:
        try:
            alert_id = str(uuid.uuid4())
            
            alert = IntegrationAlert(
                id=alert_id,
                integration_id=integration_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )

            if not self.database:
                self.integration_alerts[alert_id] = alert
                return alert_id

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO integration_alerts (id, integration_id, alert_type, severity, message, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (alert_id, integration_id, alert_type, severity, message, json.dumps(metadata or {})))
                await session.commit()

            self.integration_alerts[alert_id] = alert
            self.logger.info(f"Integration alert created: {alert_id}")
            return alert_id

        except Exception as e:
            self.logger.error(f"Failed to create integration alert: {str(e)}")
            raise

    async def get_integration_alerts(self, integration_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            alerts = list(self.integration_alerts.values())
            
            if integration_id:
                alerts = [a for a in alerts if a.integration_id == integration_id]

            # Sort by timestamp and limit
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            alerts = alerts[:limit]

            return [alert.__dict__ for alert in alerts]

        except Exception as e:
            self.logger.error(f"Failed to get integration alerts: {str(e)}")
            return []

    async def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.get_integration_alerts(limit=limit)

    async def resolve_integration_alert(self, alert_id: str, resolved_by: str) -> bool:
        try:
            if alert_id not in self.integration_alerts:
                return False

            alert = self.integration_alerts[alert_id]
            alert.resolved = True
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.utcnow()

            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE integration_alerts
                    SET resolved = TRUE, resolved_by = %s, resolved_at = %s
                    WHERE id = %s
                """, (resolved_by, alert.resolved_at, alert_id))
                await session.commit()

            self.logger.info(f"Integration alert {alert_id} resolved by {resolved_by}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve integration alert: {str(e)}")
            return False

    async def get_integration_usage_logs(self, integration_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if not self.database:
                return []

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT user_id, operation, request_data, response_data, response_time,
                           status, timestamp, ip_address
                    FROM integration_usage_logs
                    WHERE integration_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (integration_id, limit))

                rows = result.fetchall()
                logs = []
                
                for row in rows:
                    logs.append({
                        "user_id": row[0],
                        "operation": row[1],
                        "request_data": row[2] if row[2] else {},
                        "response_data": row[3] if row[3] else {},
                        "response_time": float(row[4]) if row[4] else 0.0,
                        "status": row[5],
                        "timestamp": row[6].isoformat(),
                        "ip_address": row[7]
                    })

                return logs

        except Exception as e:
            self.logger.error(f"Failed to get integration usage logs: {str(e)}")
            return []

    async def get_integration_statistics(self, days: int = 30) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.database.get_session() as session:
                # Total integrations
                result = await session.execute("SELECT COUNT(*) FROM integrations")
                total_integrations = result.scalar()

                # Active integrations
                result = await session.execute("SELECT COUNT(*) FROM integrations WHERE is_active = TRUE")
                active_integrations = result.scalar()

                # Total requests
                result = await session.execute("""
                    SELECT COUNT(*) FROM integration_usage_logs WHERE timestamp >= %s
                """, (start_date,))
                total_requests = result.scalar()

                # Successful requests
                result = await session.execute("""
                    SELECT COUNT(*) FROM integration_usage_logs 
                    WHERE timestamp >= %s AND status = 'success'
                """, (start_date,))
                successful_requests = result.scalar()

                # Failed requests
                result = await session.execute("""
                    SELECT COUNT(*) FROM integration_usage_logs 
                    WHERE timestamp >= %s AND status = 'error'
                """, (start_date,))
                failed_requests = result.scalar()

                # Average response time
                result = await session.execute("""
                    SELECT AVG(response_time) FROM integration_usage_logs 
                    WHERE timestamp >= %s AND response_time IS NOT NULL
                """, (start_date,))
                avg_response_time = result.scalar() or 0.0

                # Recent alerts
                result = await session.execute("""
                    SELECT COUNT(*) FROM integration_alerts WHERE timestamp >= %s
                """, (start_date,))
                recent_alerts = result.scalar()

                return {
                    "total_integrations": total_integrations,
                    "active_integrations": active_integrations,
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0.0,
                    "avg_response_time": float(avg_response_time),
                    "recent_alerts": recent_alerts,
                    "period_days": days
                }

        except Exception as e:
            self.logger.error(f"Failed to get integration statistics: {str(e)}")
            return {}

    async def close(self):
        self.logger.info("Closing IntegrationAdminManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_integration_admin_manager: Optional[IntegrationAdminManager] = None

async def init_integration_admin_manager() -> IntegrationAdminManager:
    global _integration_admin_manager
    if not _integration_admin_manager:
        _integration_admin_manager = IntegrationAdminManager()
        await _integration_admin_manager.initialize()
    return _integration_admin_manager

async def get_integration_admin_manager() -> IntegrationAdminManager:
    global _integration_admin_manager
    if not _integration_admin_manager:
        _integration_admin_manager = await init_integration_admin_manager()
    return _integration_admin_manager
