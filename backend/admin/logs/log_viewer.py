"""
Log Viewer for Agent47 Admin Panel
Centralized log viewing, filtering, and analysis
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogSource(Enum):
    SYSTEM = "system"
    AGENT = "agent"
    API = "api"
    DATABASE = "database"
    AUTH = "auth"
    BILLING = "billing"
    INTEGRATION = "integration"

@dataclass
class LogEntry:
    id: str
    timestamp: datetime
    level: LogLevel
    source: str
    module: str
    message: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = None
    stack_trace: Optional[str] = None

@dataclass
class LogFilter:
    levels: List[LogLevel] = None
    sources: List[str] = None
    modules: List[str] = None
    search_text: Optional[str] = None
    user_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    has_error: Optional[bool] = None

class LogViewer(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        self.logger = logger
        
        self.log_buffer: List[LogEntry] = []
        self.buffer_size = 1000
        self.max_log_age_days = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing LogViewer...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            await self._setup_log_tables()
            await self._start_log_cleanup_task()
            
            self.logger.info("LogViewer initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LogViewer: {str(e)}")
            return False

    async def _setup_log_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id VARCHAR(255) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    module VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    user_id VARCHAR(255),
                    request_id VARCHAR(255),
                    ip_address INET,
                    metadata JSONB,
                    stack_trace TEXT
                )
            """))
            
            # Create indexes for faster queries
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON admin_logs(timestamp DESC)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_level ON admin_logs(level)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_source ON admin_logs(source)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_module ON admin_logs(module)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_user_id ON admin_logs(user_id)
            """))
            
            await session.commit()

    async def _start_log_cleanup_task(self):
        """Start background task to clean up old logs"""
        async def cleanup_old_logs():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await self._cleanup_old_logs()
                except Exception as e:
                    self.logger.error(f"Error in log cleanup task: {str(e)}")
        
        asyncio.create_task(cleanup_old_logs())

    async def _cleanup_old_logs(self):
        """Remove logs older than max_log_age_days"""
        if not self.database:
            return
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.max_log_age_days)
            
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        DELETE FROM admin_logs
                        WHERE timestamp < :cutoff_date
                        RETURNING id
                    """),
                    {"cutoff_date": cutoff_date}
                )
                
                deleted_count = len(result.fetchall())
                await session.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old log entries")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {str(e)}")

    async def log_entry(self, level: LogLevel, source: str, module: str, message: str,
                       user_id: Optional[str] = None, request_id: Optional[str] = None,
                       ip_address: Optional[str] = None, metadata: Dict[str, Any] = None,
                       stack_trace: Optional[str] = None) -> str:
        """Log an entry to the database"""
        import uuid
        
        log_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        log_entry = LogEntry(
            id=log_id,
            timestamp=timestamp,
            level=level,
            source=source,
            module=module,
            message=message,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            metadata=metadata or {},
            stack_trace=stack_trace
        )
        
        # Add to buffer
        self.log_buffer.append(log_entry)
        
        # Flush buffer if full
        if len(self.log_buffer) >= self.buffer_size:
            await self._flush_log_buffer()
        
        return log_id

    async def _flush_log_buffer(self):
        """Flush log buffer to database"""
        if not self.database or not self.log_buffer:
            return
        
        try:
            async with self.database.get_session() as session:
                for entry in self.log_buffer:
                    await session.execute(
                        text("""
                            INSERT INTO admin_logs (
                                id, timestamp, level, source, module, message,
                                user_id, request_id, ip_address, metadata, stack_trace
                            )
                            VALUES (:id, :timestamp, :level, :source, :module, :message,
                                    :user_id, :request_id, :ip_address, :metadata, :stack_trace)
                        """),
                        {
                            "id": entry.id,
                            "timestamp": entry.timestamp,
                            "level": entry.level.value,
                            "source": entry.source,
                            "module": entry.module,
                            "message": entry.message,
                            "user_id": entry.user_id,
                            "request_id": entry.request_id,
                            "ip_address": entry.ip_address,
                            "metadata": json.dumps(entry.metadata) if entry.metadata else None,
                            "stack_trace": entry.stack_trace
                        }
                    )
                
                await session.commit()
                self.log_buffer.clear()
        
        except Exception as e:
            self.logger.error(f"Failed to flush log buffer: {str(e)}")

    async def get_logs(self, filter: LogFilter, page: int = 1, limit: int = 100) -> Tuple[List[LogEntry], int]:
        """Get logs with filtering and pagination"""
        # Flush buffer first
        await self._flush_log_buffer()
        
        if not self.database:
            return [], 0
        
        try:
            # Build query
            query = "SELECT id, timestamp, level, source, module, message, user_id, request_id, ip_address, metadata, stack_trace FROM admin_logs WHERE 1=1"
            params = {}
            
            if filter.levels:
                query += " AND level = ANY(:levels)"
                params["levels"] = [level.value for level in filter.levels]
            
            if filter.sources:
                query += " AND source = ANY(:sources)"
                params["sources"] = filter.sources
            
            if filter.modules:
                query += " AND module = ANY(:modules)"
                params["modules"] = filter.modules
            
            if filter.search_text:
                query += " AND (message ILIKE :search OR module ILIKE :search)"
                params["search"] = f"%{filter.search_text}%"
            
            if filter.user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = filter.user_id
            
            if filter.start_time:
                query += " AND timestamp >= :start_time"
                params["start_time"] = filter.start_time
            
            if filter.end_time:
                query += " AND timestamp <= :end_time"
                params["end_time"] = filter.end_time
            
            if filter.has_error is not None:
                if filter.has_error:
                    query += " AND level IN ('ERROR', 'CRITICAL')"
                else:
                    query += " AND level NOT IN ('ERROR', 'CRITICAL')"
            
            # Get total count
            count_query = query.replace("SELECT id, timestamp, level, source, module, message, user_id, request_id, ip_address, metadata, stack_trace", "SELECT COUNT(*)")
            
            async with self.database.get_session() as session:
                count_result = await session.execute(text(count_query), params)
                total_count = count_result.scalar()
                
                # Add pagination
                query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = (page - 1) * limit
                
                result = await session.execute(text(query), params)
                
                logs = []
                for row in result.fetchall():
                    metadata = json.loads(row[9]) if row[9] else {}
                    logs.append(LogEntry(
                        id=row[0],
                        timestamp=row[1],
                        level=LogLevel(row[2]),
                        source=row[3],
                        module=row[4],
                        message=row[5],
                        user_id=row[6],
                        request_id=row[7],
                        ip_address=row[8],
                        metadata=metadata,
                        stack_trace=row[10]
                    ))
                
                return logs, total_count
        
        except Exception as e:
            self.logger.error(f"Failed to get logs: {str(e)}")
            return [], 0

    async def get_log_statistics(self, start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get log statistics"""
        if not self.database:
            return {}
        
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=1)
            if not end_time:
                end_time = datetime.utcnow()
            
            async with self.database.get_session() as session:
                # Total logs
                result = await session.execute(
                    text("""
                        SELECT COUNT(*) FROM admin_logs
                        WHERE timestamp >= :start_time AND timestamp <= :end_time
                    """),
                    {"start_time": start_time, "end_time": end_time}
                )
                total_logs = result.scalar()
                
                # Logs by level
                result = await session.execute(
                    text("""
                        SELECT level, COUNT(*) FROM admin_logs
                        WHERE timestamp >= :start_time AND timestamp <= :end_time
                        GROUP BY level
                    """),
                    {"start_time": start_time, "end_time": end_time}
                )
                logs_by_level = {row[0]: row[1] for row in result.fetchall()}
                
                # Logs by source
                result = await session.execute(
                    text("""
                        SELECT source, COUNT(*) FROM admin_logs
                        WHERE timestamp >= :start_time AND timestamp <= :end_time
                        GROUP BY source
                    """),
                    {"start_time": start_time, "end_time": end_time}
                )
                logs_by_source = {row[0]: row[1] for row in result.fetchall()}
                
                # Error rate
                result = await session.execute(
                    text("""
                        SELECT COUNT(*) FROM admin_logs
                        WHERE timestamp >= :start_time AND timestamp <= :end_time
                        AND level IN ('ERROR', 'CRITICAL')
                    """),
                    {"start_time": start_time, "end_time": end_time}
                )
                error_count = result.scalar()
                error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
                
                # Top error modules
                result = await session.execute(
                    text("""
                        SELECT module, COUNT(*) as error_count FROM admin_logs
                        WHERE timestamp >= :start_time AND timestamp <= :end_time
                        AND level IN ('ERROR', 'CRITICAL')
                        GROUP BY module
                        ORDER BY error_count DESC
                        LIMIT 10
                    """),
                    {"start_time": start_time, "end_time": end_time}
                )
                top_error_modules = [{"module": row[0], "count": row[1]} for row in result.fetchall()]
                
                return {
                    "total_logs": total_logs,
                    "logs_by_level": logs_by_level,
                    "logs_by_source": logs_by_source,
                    "error_count": error_count,
                    "error_rate": round(error_rate, 2),
                    "top_error_modules": top_error_modules,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
        
        except Exception as e:
            self.logger.error(f"Failed to get log statistics: {str(e)}")
            return {}

    async def search_logs(self, query: str, limit: int = 100) -> List[LogEntry]:
        """Search logs with full-text search"""
        filter = LogFilter(search_text=query)
        logs, _ = await self.get_logs(filter, page=1, limit=limit)
        return logs

    async def get_user_activity_logs(self, user_id: str, hours: int = 24) -> List[LogEntry]:
        """Get activity logs for a specific user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        filter = LogFilter(user_id=user_id, start_time=start_time)
        logs, _ = await self.get_logs(filter, page=1, limit=1000)
        return logs

    async def get_error_logs(self, hours: int = 24, limit: int = 100) -> List[LogEntry]:
        """Get error and critical logs"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        filter = LogFilter(
            levels=[LogLevel.ERROR, LogLevel.CRITICAL],
            start_time=start_time,
            has_error=True
        )
        logs, _ = await self.get_logs(filter, page=1, limit=limit)
        return logs

    async def export_logs(self, filter: LogFilter, format: str = "json") -> str:
        """Export logs in specified format"""
        logs, _ = await self.get_logs(filter, page=1, limit=10000)
        
        if format == "json":
            import json
            return json.dumps([{
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value,
                "source": log.source,
                "module": log.module,
                "message": log.message,
                "user_id": log.user_id,
                "request_id": log.request_id,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "metadata": log.metadata,
                "stack_trace": log.stack_trace
            } for log in logs], indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Timestamp", "Level", "Source", "Module", "Message", "User ID", "IP Address"])
            
            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat(),
                    log.level.value,
                    log.source,
                    log.module,
                    log.message,
                    log.user_id or "",
                    str(log.ip_address) if log.ip_address else ""
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def close(self):
        """Close log viewer and flush buffer"""
        await self._flush_log_buffer()
        self.logger.info("LogViewer closed")

# Global instances
_log_viewer: Optional[LogViewer] = None

async def init_log_viewer() -> LogViewer:
    global _log_viewer
    if not _log_viewer:
        _log_viewer = LogViewer()
        await _log_viewer.initialize()
    return _log_viewer

async def get_log_viewer() -> LogViewer:
    global _log_viewer
    if not _log_viewer:
        _log_viewer = await init_log_viewer()
    return _log_viewer

