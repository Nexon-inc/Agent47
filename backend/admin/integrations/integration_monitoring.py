import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger


class IntegrationMonitoring:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()

    async def initialize(self):
        async with self.db.get_session() as session:
            await session.execute(
                """
                CREATE TABLE IF NOT EXISTS integration_metrics (
                    id SERIAL PRIMARY KEY,
                    integration_name VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    latency_ms DOUBLE PRECISION NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    status_code INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            await session.commit()
        return True

    async def record_call(self, name: str, latency_ms: float, success: bool, status_code: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        try:
            async with self.db.get_session() as session:
                await session.execute(
                    """
                    INSERT INTO integration_metrics (integration_name, timestamp, latency_ms, success, status_code, error_message)
                    VALUES (:name, :ts, :lat, :succ, :code, :err)
                    """,
                    {"name": name, "ts": datetime.utcnow(), "lat": latency_ms, "succ": success, "code": status_code, "err": error_message},
                )
                await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to record integration call: {e}")
            return False

    async def get_status(self, name: str, minutes: int = 60) -> Dict[str, Any]:
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            async with self.db.get_session() as session:
                res = await session.execute(
                    """
                    SELECT COUNT(*) total,
                           COUNT(CASE WHEN success THEN 1 END) ok,
                           AVG(latency_ms) avg_lat,
                           MAX(latency_ms) max_lat
                    FROM integration_metrics
                    WHERE integration_name = %s AND timestamp >= %s
                    """,
                    (name, cutoff),
                )
                row = res.fetchone()
                total = int(row.total or 0)
                ok = int(row.ok or 0)
                uptime = (ok / total * 100.0) if total > 0 else 0.0
                return {
                    "integration": name,
                    "period_minutes": minutes,
                    "uptime_percent": uptime,
                    "avg_latency_ms": float(row.avg_lat or 0.0),
                    "max_latency_ms": float(row.max_lat or 0.0),
                    "total_calls": total,
                    "errors": total - ok,
                }
        except Exception as e:
            self.logger.error(f"Failed to get integration status: {e}")
            return {}


_integration_monitoring: Optional[IntegrationMonitoring] = None


async def get_integration_monitoring() -> IntegrationMonitoring:
    global _integration_monitoring
    if _integration_monitoring is None:
        _integration_monitoring = IntegrationMonitoring()
        await _integration_monitoring.initialize()
    return _integration_monitoring


async def init_integration_monitoring() -> IntegrationMonitoring:
    m = IntegrationMonitoring()
    await m.initialize()
    return m
