import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
import re

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class PerformanceStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class QueryMetrics:
    query_id: str
    query_text: str
    execution_time_ms: float
    rows_returned: int
    rows_affected: int
    cpu_time_ms: float
    io_wait_ms: float
    memory_usage_mb: float
    timestamp: datetime
    user_id: str
    application: str

@dataclass
class TablePerformance:
    table_name: str
    total_size_mb: float
    index_size_mb: float
    row_count: int
    avg_row_size_bytes: int
    last_vacuum: datetime
    last_analyze: datetime
    cache_hit_ratio: float
    sequential_scans: int
    index_scans: int

class PerformanceMetric(Enum):
    QUERY_TIME = "query_time"
    CONNECTIONS = "connections"
    CACHE_HIT_RATIO = "cache_hit_ratio"
    TABLE_SIZE = "table_size"
    INDEX_USAGE = "index_usage"

class PerformanceLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class DatabaseMetrics:
    id: str
    metric_type: PerformanceMetric
    value: float
    unit: str
    level: PerformanceLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DatabasePerformanceMonitor(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.monitoring_active = False
        self.performance_thresholds = {
            "slow_query_threshold_ms": 1000,
            "high_cpu_threshold_percent": 80,
            "high_memory_threshold_percent": 85,
            "low_cache_hit_threshold": 70,
            "high_connection_threshold": 100
        }
        self.query_cache = {}
        self.performance_history = []
        self.db = get_database()
    
    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing DatabasePerformanceMonitor...")
            self.database = get_database()
            await self._setup_performance_tables()
            await self._load_performance_history()
            self.logger.info("DatabasePerformanceMonitor initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize DatabasePerformanceMonitor: {str(e)}")
            return False

    async def _setup_performance_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS query_performance (
                    id SERIAL PRIMARY KEY,
                    query_id VARCHAR(255) NOT NULL,
                    query_text TEXT NOT NULL,
                    execution_time_ms FLOAT NOT NULL,
                    rows_returned INTEGER,
                    rows_affected INTEGER,
                    cpu_time_ms FLOAT,
                    io_wait_ms FLOAT,
                    memory_usage_mb FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id VARCHAR(255),
                    application VARCHAR(100),
                    normalized_query TEXT,
                    query_hash VARCHAR(64)
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS table_performance (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    total_size_mb FLOAT,
                    index_size_mb FLOAT,
                    row_count BIGINT,
                    avg_row_size_bytes INTEGER,
                    last_vacuum TIMESTAMP,
                    last_analyze TIMESTAMP,
                    cache_hit_ratio FLOAT,
                    sequential_scans BIGINT,
                    index_scans BIGINT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    metric_value FLOAT,
                    threshold_value FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_performance_timestamp 
                ON query_performance(timestamp)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_query_performance_execution_time 
                ON query_performance(execution_time_ms)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_table_performance_timestamp 
                ON table_performance(timestamp)
            """))
            
            await session.commit()

    async def _load_performance_history(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT timestamp, execution_time_ms, rows_returned, cpu_time_ms
                    FROM query_performance 
                    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    ORDER BY timestamp DESC
                """))
                
                self.performance_history = []
                for row in result.fetchall():
                    self.performance_history.append({
                        "timestamp": row[0],
                        "execution_time_ms": row[1],
                        "rows_returned": row[2],
                        "cpu_time_ms": row[3]
                    })
        except Exception as e:
            self.logger.error(f"Failed to load performance history: {str(e)}")

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
                await self._collect_performance_metrics()
                await self._analyze_performance()
                await self._check_alerts()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Performance monitoring loop error: {str(e)}")
                await asyncio.sleep(60)

    async def _collect_performance_metrics(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await self._collect_query_metrics(session)
                await self._collect_table_metrics(session)
                await self._collect_system_metrics(session)
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {str(e)}")

    async def _collect_query_metrics(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                shared_blks_written,
                shared_blks_dirtied,
                temp_blks_read,
                temp_blks_written,
                blk_read_time,
                blk_write_time
            FROM pg_stat_statements 
            ORDER BY total_time DESC 
            LIMIT 100
        """))
        
        for row in result.fetchall():
            query_metrics = QueryMetrics(
                query_id=f"query_{hash(row[0])}",
                query_text=row[0],
                execution_time_ms=row[3] * 1000,
                rows_returned=row[4],
                rows_affected=0,
                cpu_time_ms=row[3] * 1000,
                io_wait_ms=row[11] + row[12],
                memory_usage_mb=0,
                timestamp=datetime.utcnow(),
                user_id="system",
                application="database"
            )
            
            await self._save_query_metrics(query_metrics)

    async def _collect_table_metrics(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_total_relation_size(schemaname||'.'||tablename) as total_size,
                pg_relation_size(schemaname||'.'||tablename) as table_size,
                n_tup_ins + n_tup_upd + n_tup_del as row_count,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_analyze,
                heap_blks_hit,
                heap_blks_read,
                idx_blks_hit,
                idx_blks_read,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
        """))
        
        for row in result.fetchall():
            total_size_mb = row[2] / (1024 * 1024)
            index_size_mb = (row[2] - row[3]) / (1024 * 1024)
            cache_hit_ratio = 0
            
            if row[10] + row[11] > 0:
                cache_hit_ratio = row[10] / (row[10] + row[11]) * 100
            
            table_performance = TablePerformance(
                table_name=row[1],
                total_size_mb=total_size_mb,
                index_size_mb=index_size_mb,
                row_count=row[4],
                avg_row_size_bytes=row[3] // max(row[4], 1),
                last_vacuum=row[7] or datetime.utcnow(),
                last_analyze=row[8] or datetime.utcnow(),
                cache_hit_ratio=cache_hit_ratio,
                sequential_scans=row[13],
                index_scans=row[15]
            )
            
            await self._save_table_metrics(table_performance)

    async def _collect_system_metrics(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                count(*) as active_connections,
                sum(case when state = 'active' then 1 else 0 end) as active_queries,
                avg(extract(epoch from now() - query_start)) as avg_query_time
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """))
        
        row = result.fetchone()
        if row:
            system_metrics = {
                "active_connections": row[0],
                "active_queries": row[1],
                "avg_query_time_ms": (row[2] or 0) * 1000,
                "timestamp": datetime.utcnow()
            }
            
            await self._check_system_alerts(system_metrics)

    async def _save_query_metrics(self, metrics: QueryMetrics):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO query_performance (
                        query_id, query_text, execution_time_ms, rows_returned, rows_affected,
                        cpu_time_ms, io_wait_ms, memory_usage_mb, user_id, application,
                        normalized_query, query_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    metrics.query_id,
                    metrics.query_text[:1000],
                    metrics.execution_time_ms,
                    metrics.rows_returned,
                    metrics.rows_affected,
                    metrics.cpu_time_ms,
                    metrics.io_wait_ms,
                    metrics.memory_usage_mb,
                    metrics.user_id,
                    metrics.application,
                    self._normalize_query(metrics.query_text),
                    str(hash(metrics.query_text))
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save query metrics: {str(e)}")

    async def _save_table_metrics(self, metrics: TablePerformance):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO table_performance (
                        table_name, total_size_mb, index_size_mb, row_count, avg_row_size_bytes,
                        last_vacuum, last_analyze, cache_hit_ratio, sequential_scans, index_scans
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    metrics.table_name,
                    metrics.total_size_mb,
                    metrics.index_size_mb,
                    metrics.row_count,
                    metrics.avg_row_size_bytes,
                    metrics.last_vacuum,
                    metrics.last_analyze,
                    metrics.cache_hit_ratio,
                    metrics.sequential_scans,
                    metrics.index_scans
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save table metrics: {str(e)}")

    def _normalize_query(self, query: str) -> str:
        normalized = query.lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'--.*$', '', normalized, flags=re.MULTILINE)
        return normalized.strip()

    async def _analyze_performance(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await self._analyze_slow_queries(session)
                await self._analyze_table_performance(session)
                await self._analyze_index_usage(session)
        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {str(e)}")

    async def _analyze_slow_queries(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                normalized_query,
                COUNT(*) as execution_count,
                AVG(execution_time_ms) as avg_execution_time,
                MAX(execution_time_ms) as max_execution_time,
                SUM(execution_time_ms) as total_execution_time
            FROM query_performance 
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            GROUP BY normalized_query
            HAVING AVG(execution_time_ms) > %s
            ORDER BY avg_execution_time DESC
        """), (self.performance_thresholds["slow_query_threshold_ms"],))
        
        for row in result.fetchall():
            if row[2] > self.performance_thresholds["slow_query_threshold_ms"] * 2:
                await self._create_alert(
                    "SLOW_QUERY",
                    "critical",
                    f"Very slow query detected: {row[2]:.2f}ms average",
                    row[2],
                    self.performance_thresholds["slow_query_threshold_ms"]
                )

    async def _analyze_table_performance(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                table_name,
                cache_hit_ratio,
                sequential_scans,
                index_scans
            FROM table_performance 
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY timestamp DESC
        """))
        
        for row in result.fetchall():
            if row[1] < self.performance_thresholds["low_cache_hit_threshold"]:
                await self._create_alert(
                    "LOW_CACHE_HIT",
                    "warning",
                    f"Low cache hit ratio for table {row[0]}: {row[1]:.2f}%",
                    row[1],
                    self.performance_thresholds["low_cache_hit_threshold"]
                )

    async def _analyze_index_usage(self, session: AsyncSession):
        result = await session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_scan ASC
        """))
        
        for row in result.fetchall():
            if row[3] == 0:
                await self._create_alert(
                    "UNUSED_INDEX",
                    "warning",
                    f"Unused index detected: {row[2]} on {row[1]}",
                    0,
                    1
                )

    async def _check_system_alerts(self, metrics: Dict[str, Any]):
        if metrics["active_connections"] > self.performance_thresholds["high_connection_threshold"]:
            await self._create_alert(
                "HIGH_CONNECTIONS",
                "critical",
                f"High connection count: {metrics['active_connections']}",
                metrics["active_connections"],
                self.performance_thresholds["high_connection_threshold"]
            )

    async def _create_alert(self, alert_type: str, severity: str, message: str, 
                           metric_value: float, threshold_value: float):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO performance_alerts (alert_type, severity, message, metric_value, threshold_value)
                    VALUES (%s, %s, %s, %s, %s)
                """), (alert_type, severity, message, metric_value, threshold_value))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to create alert: {str(e)}")

    async def get_performance_summary(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(execution_time_ms) as avg_execution_time,
                        MAX(execution_time_ms) as max_execution_time,
                        SUM(execution_time_ms) as total_execution_time,
                        COUNT(*) FILTER (WHERE execution_time_ms > %s) as slow_queries
                    FROM query_performance 
                    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                """), (self.performance_thresholds["slow_query_threshold_ms"],))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_queries": row[0],
                        "avg_execution_time_ms": row[1] or 0,
                        "max_execution_time_ms": row[2] or 0,
                        "total_execution_time_ms": row[3] or 0,
                        "slow_queries_count": row[4],
                        "slow_queries_percentage": (row[4] / max(row[0], 1)) * 100
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {str(e)}")
            return {}

    async def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        query_text, execution_time_ms, rows_returned, timestamp, user_id, application
                    FROM query_performance 
                    WHERE execution_time_ms > %s
                    ORDER BY execution_time_ms DESC 
                    LIMIT %s
                """), (self.performance_thresholds["slow_query_threshold_ms"], limit))
                
                slow_queries = []
                for row in result.fetchall():
                    slow_queries.append({
                        "query_text": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                        "execution_time_ms": row[1],
                        "rows_returned": row[2],
                        "timestamp": row[3].isoformat(),
                        "user_id": row[4],
                        "application": row[5]
                    })
                
                return slow_queries
        except Exception as e:
            self.logger.error(f"Failed to get slow queries: {str(e)}")
            return []

    async def get_table_performance(self) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        table_name, total_size_mb, index_size_mb, row_count, 
                        cache_hit_ratio, sequential_scans, index_scans, timestamp
                    FROM table_performance 
                    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                    ORDER BY total_size_mb DESC
                """))
                
                tables = []
                for row in result.fetchall():
                    tables.append({
                        "table_name": row[0],
                        "total_size_mb": row[1],
                        "index_size_mb": row[2],
                        "row_count": row[3],
                        "cache_hit_ratio": row[4],
                        "sequential_scans": row[5],
                        "index_scans": row[6],
                        "timestamp": row[7].isoformat()
                    })
                
                return tables
        except Exception as e:
            self.logger.error(f"Failed to get table performance: {str(e)}")
            return []

    async def get_performance_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT id, alert_type, severity, message, metric_value, threshold_value, 
                           timestamp, resolved, resolved_at
                    FROM performance_alerts 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """), (limit,))
                
                alerts = []
                for row in result.fetchall():
                    alerts.append({
                        "id": row[0],
                        "alert_type": row[1],
                        "severity": row[2],
                        "message": row[3],
                        "metric_value": row[4],
                        "threshold_value": row[5],
                        "timestamp": row[6].isoformat(),
                        "resolved": row[7],
                        "resolved_at": row[8].isoformat() if row[8] else None
                    })
                
                return alerts
        except Exception as e:
            self.logger.error(f"Failed to get performance alerts: {str(e)}")
            return []

    async def resolve_alert(self, alert_id: int) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE performance_alerts 
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """), (alert_id,))
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {str(e)}")
            return False

    async def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        recommendations = []
        
        try:
            performance_summary = await self.get_performance_summary()
            
            if performance_summary.get("slow_queries_percentage", 0) > 10:
                recommendations.append({
                    "type": "slow_queries",
                    "severity": "high",
                    "title": "High percentage of slow queries",
                    "description": f"{performance_summary['slow_queries_percentage']:.1f}% of queries are slow",
                    "action": "Review and optimize slow queries, consider adding indexes"
                })
            
            table_performance = await self.get_table_performance()
            for table in table_performance:
                if table["cache_hit_ratio"] < 80:
                    recommendations.append({
                        "type": "cache_hit",
                        "severity": "medium",
                        "title": f"Low cache hit ratio for {table['table_name']}",
                        "description": f"Cache hit ratio: {table['cache_hit_ratio']:.1f}%",
                        "action": "Consider increasing shared_buffers or optimizing queries"
                    })
                
                if table["sequential_scans"] > table["index_scans"] * 10:
                    recommendations.append({
                        "type": "index_usage",
                        "severity": "medium",
                        "title": f"High sequential scans for {table['table_name']}",
                        "description": f"Sequential scans: {table['sequential_scans']}, Index scans: {table['index_scans']}",
                        "action": "Consider adding indexes for frequently scanned columns"
                    })
            
        except Exception as e:
            self.logger.error(f"Failed to get performance recommendations: {str(e)}")
        
        return recommendations

    async def cleanup_old_metrics(self, days: int = 7):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    DELETE FROM query_performance 
                    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                
                await session.execute(text("""
                    DELETE FROM table_performance 
                    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {str(e)}")

    async def shutdown(self):
        self.logger.info("Shutting down DatabasePerformanceMonitor...")
        await self.stop_monitoring()
        self.logger.info("DatabasePerformanceMonitor shutdown complete")

# Singleton instance
_db_performance_monitor = None

def get_db_performance_monitor() -> DatabasePerformanceMonitor:
    global _db_performance_monitor
    if _db_performance_monitor is None:
        _db_performance_monitor = DatabasePerformanceMonitor()
    return _db_performance_monitor

def init_db_performance_monitor():
    """Initialize database performance monitoring system"""
    global _db_performance_monitor
    _db_performance_monitor = DatabasePerformanceMonitor()
    return _db_performance_monitor
