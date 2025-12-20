import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import psutil
import asyncpg
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class DatabaseStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

class TableInfo:
    def __init__(self, name: str, size_bytes: int, row_count: int, last_updated: datetime):
        self.name = name
        self.size_bytes = size_bytes
        self.row_count = row_count
        self.last_updated = last_updated

class DatabaseMetrics:
    def __init__(self):
        self.connection_count = 0
        self.active_queries = 0
        self.avg_query_time = 0.0
        self.cache_hit_ratio = 0.0
        self.disk_usage_percent = 0.0
        self.memory_usage_percent = 0.0
        self.cpu_usage_percent = 0.0
        self.uptime_seconds = 0
        self.total_queries = 0
        self.slow_queries = 0

class DatabaseAdminManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.metrics = DatabaseMetrics()
        self.status = DatabaseStatus.OFFLINE
        self.last_health_check = datetime.utcnow()
        self.connection_pool = None
        self.monitoring_active = False

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing DatabaseAdminManager...")
            self.database = get_database()
            self.redis = await get_redis()
            await self._setup_monitoring()
            await self._verify_connections()
            self.status = DatabaseStatus.HEALTHY
            self.last_health_check = datetime.utcnow()
            self.logger.info("DatabaseAdminManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize DatabaseAdminManager: {str(e)}")
            self.status = DatabaseStatus.CRITICAL
            return False

    async def _setup_monitoring(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS database_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    connection_count INTEGER,
                    active_queries INTEGER,
                    avg_query_time FLOAT,
                    cache_hit_ratio FLOAT,
                    disk_usage_percent FLOAT,
                    memory_usage_percent FLOAT,
                    cpu_usage_percent FLOAT,
                    uptime_seconds INTEGER,
                    total_queries INTEGER,
                    slow_queries INTEGER,
                    status VARCHAR(20)
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS database_alerts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_type VARCHAR(50),
                    severity VARCHAR(20),
                    message TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_database_metrics_timestamp 
                ON database_metrics(timestamp)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_database_alerts_timestamp 
                ON database_alerts(timestamp)
            """))
            
            await session.commit()

    async def _verify_connections(self):
        if self.database:
            await self.database.health_check()
        if self.redis:
            await self.redis.health_check()

    async def get_database_status(self) -> Dict[str, Any]:
        try:
            await self._collect_metrics()
            return {
                "status": self.status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "last_health_check": self.last_health_check.isoformat(),
                "metrics": {
                    "connection_count": self.metrics.connection_count,
                    "active_queries": self.metrics.active_queries,
                    "avg_query_time": self.metrics.avg_query_time,
                    "cache_hit_ratio": self.metrics.cache_hit_ratio,
                    "disk_usage_percent": self.metrics.disk_usage_percent,
                    "memory_usage_percent": self.metrics.memory_usage_percent,
                    "cpu_usage_percent": self.metrics.cpu_usage_percent,
                    "uptime_seconds": self.metrics.uptime_seconds,
                    "total_queries": self.metrics.total_queries,
                    "slow_queries": self.metrics.slow_queries
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get database status: {str(e)}")
            return {
                "status": DatabaseStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _collect_metrics(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        count(*) as connection_count,
                        sum(case when state = 'active' then 1 else 0 end) as active_queries,
                        avg(extract(epoch from now() - query_start)) as avg_query_time,
                        count(*) filter (where state = 'active' and extract(epoch from now() - query_start) > 5) as slow_queries
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                
                row = result.fetchone()
                if row:
                    self.metrics.connection_count = row[0] or 0
                    self.metrics.active_queries = row[1] or 0
                    self.metrics.avg_query_time = float(row[2] or 0)
                    self.metrics.slow_queries = row[3] or 0

                result = await session.execute(text("""
                    SELECT 
                        sum(heap_blks_hit) * 100.0 / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio,
                        sum(tup_fetched) as total_queries
                    FROM pg_statio_user_tables
                """))
                
                row = result.fetchone()
                if row:
                    self.metrics.cache_hit_ratio = float(row[0] or 0)
                    self.metrics.total_queries = row[1] or 0

                result = await session.execute(text("SELECT extract(epoch from now() - pg_postmaster_start_time()) as uptime"))
                row = result.fetchone()
                if row:
                    self.metrics.uptime_seconds = int(row[0] or 0)

            self.metrics.disk_usage_percent = psutil.disk_usage('/').percent
            self.metrics.memory_usage_percent = psutil.virtual_memory().percent
            self.metrics.cpu_usage_percent = psutil.cpu_percent(interval=1)

            await self._save_metrics()
            await self._check_alerts()

        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            self.status = DatabaseStatus.CRITICAL

    async def _save_metrics(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO database_metrics (
                        connection_count, active_queries, avg_query_time, cache_hit_ratio,
                        disk_usage_percent, memory_usage_percent, cpu_usage_percent,
                        uptime_seconds, total_queries, slow_queries, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    self.metrics.connection_count,
                    self.metrics.active_queries,
                    self.metrics.avg_query_time,
                    self.metrics.cache_hit_ratio,
                    self.metrics.disk_usage_percent,
                    self.metrics.memory_usage_percent,
                    self.metrics.cpu_usage_percent,
                    self.metrics.uptime_seconds,
                    self.metrics.total_queries,
                    self.metrics.slow_queries,
                    self.status.value
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {str(e)}")

    async def _check_alerts(self):
        alerts = []
        
        if self.metrics.connection_count > 100:
            alerts.append(("HIGH_CONNECTIONS", "critical", f"High connection count: {self.metrics.connection_count}"))
        
        if self.metrics.avg_query_time > 5.0:
            alerts.append(("SLOW_QUERIES", "warning", f"Slow average query time: {self.metrics.avg_query_time:.2f}s"))
        
        if self.metrics.cache_hit_ratio < 80.0:
            alerts.append(("LOW_CACHE_HIT", "warning", f"Low cache hit ratio: {self.metrics.cache_hit_ratio:.2f}%"))
        
        if self.metrics.disk_usage_percent > 90.0:
            alerts.append(("HIGH_DISK_USAGE", "critical", f"High disk usage: {self.metrics.disk_usage_percent:.2f}%"))
        
        if self.metrics.memory_usage_percent > 90.0:
            alerts.append(("HIGH_MEMORY_USAGE", "critical", f"High memory usage: {self.metrics.memory_usage_percent:.2f}%"))

        for alert_type, severity, message in alerts:
            await self._create_alert(alert_type, severity, message)

    async def _create_alert(self, alert_type: str, severity: str, message: str):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO database_alerts (alert_type, severity, message)
                    VALUES (%s, %s, %s)
                """), (alert_type, severity, message))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to create alert: {str(e)}")

    async def get_table_info(self) -> List[TableInfo]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                        n_tup_ins + n_tup_upd + n_tup_del as row_count,
                        last_vacuum as last_updated
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                """))
                
                tables = []
                for row in result.fetchall():
                    tables.append(TableInfo(
                        name=row[1],
                        size_bytes=row[2],
                        row_count=row[3],
                        last_updated=row[4] or datetime.utcnow()
                    ))
                
                return tables
        except Exception as e:
            self.logger.error(f"Failed to get table info: {str(e)}")
            return []

    async def get_database_size(self) -> Dict[str, int]:
        if not self.database:
            return {"total_size": 0, "data_size": 0, "index_size": 0}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        pg_database_size(current_database()) as total_size,
                        pg_size_pretty(pg_database_size(current_database())) as total_size_pretty
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_size": row[0],
                        "total_size_pretty": row[1],
                        "data_size": row[0] * 0.7,
                        "index_size": row[0] * 0.3
                    }
                return {"total_size": 0, "data_size": 0, "index_size": 0}
        except Exception as e:
            self.logger.error(f"Failed to get database size: {str(e)}")
            return {"total_size": 0, "data_size": 0, "index_size": 0}

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            start_time = datetime.utcnow()
            async with self.database.get_session() as session:
                result = await session.execute(text(query), params or {})
                
                if query.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    columns = result.keys()
                    return {
                        "success": True,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows),
                        "execution_time": (datetime.utcnow() - start_time).total_seconds()
                    }
                else:
                    await session.commit()
                    return {
                        "success": True,
                        "affected_rows": result.rowcount,
                        "execution_time": (datetime.utcnow() - start_time).total_seconds()
                    }
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }

    async def get_connection_pool_status(self) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            pool = self.database.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            self.logger.error(f"Failed to get connection pool status: {str(e)}")
            return {"error": str(e)}

    async def start_monitoring(self):
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        self.monitoring_active = False

    async def _monitoring_loop(self):
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, timestamp, alert_type, severity, message, resolved, resolved_at
                    FROM database_alerts 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """), (limit,))
                
                alerts = []
                for row in result.fetchall():
                    alerts.append({
                        "id": row[0],
                        "timestamp": row[1].isoformat(),
                        "alert_type": row[2],
                        "severity": row[3],
                        "message": row[4],
                        "resolved": row[5],
                        "resolved_at": row[6].isoformat() if row[6] else None
                    })
                
                return alerts
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {str(e)}")
            return []

    async def resolve_alert(self, alert_id: int) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE database_alerts 
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """), (alert_id,))
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {str(e)}")
            return False

    async def cleanup_old_metrics(self, days: int = 30):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    DELETE FROM database_metrics 
                    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {str(e)}")

    async def shutdown(self):
        self.logger.info("Shutting down DatabaseAdminManager...")
        await self.stop_monitoring()
        if self.database:
            await self.database.close()
        self.logger.info("DatabaseAdminManager shutdown complete")
