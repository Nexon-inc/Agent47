import asyncio
import json
import traceback
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorStatus(Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    ESCALATED = "escalated"

class ErrorCategory(Enum):
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class ErrorEvent:
    id: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    category: ErrorCategory
    status: ErrorStatus
    source_file: str
    line_number: int
    function_name: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    fingerprint: str = ""
    occurrence_count: int = 1
    first_occurrence: datetime = field(default_factory=datetime.utcnow)
    last_occurrence: datetime = field(default_factory=datetime.utcnow)
    resolution_notes: str = ""
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class ErrorCorrelation:
    error_id: str
    correlated_errors: List[str]
    correlation_score: float
    common_patterns: List[str]
    correlation_type: str
    timestamp: datetime

class ErrorMonitor(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()
        
        self.active_errors: Dict[str, ErrorEvent] = {}
        self.error_patterns: Dict[str, Dict[str, Any]] = {}
        self.correlation_cache: Dict[str, ErrorCorrelation] = {}
        self.logger = logger
        
        self._setup_error_patterns()
        self._setup_alert_thresholds()

    def _setup_error_patterns(self):
        self.error_patterns = {
            "database_connection": {
                "patterns": [
                    r"connection.*refused",
                    r"timeout.*connection",
                    r"database.*unreachable",
                    r"connection.*pool.*exhausted"
                ],
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "tags": ["database", "connection", "infrastructure"]
            },
            "authentication_failure": {
                "patterns": [
                    r"invalid.*token",
                    r"authentication.*failed",
                    r"unauthorized.*access",
                    r"expired.*session"
                ],
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "tags": ["auth", "security", "user"]
            },
            "validation_error": {
                "patterns": [
                    r"validation.*failed",
                    r"invalid.*input",
                    r"required.*field",
                    r"format.*error"
                ],
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "tags": ["validation", "input", "user"]
            },
            "external_api_error": {
                "patterns": [
                    r"api.*timeout",
                    r"rate.*limit.*exceeded",
                    r"service.*unavailable",
                    r"http.*error"
                ],
                "category": ErrorCategory.EXTERNAL_API,
                "severity": ErrorSeverity.MEDIUM,
                "tags": ["api", "external", "integration"]
            },
            "business_logic_error": {
                "patterns": [
                    r"insufficient.*permissions",
                    r"business.*rule.*violation",
                    r"workflow.*error",
                    r"state.*invalid"
                ],
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.MEDIUM,
                "tags": ["business", "logic", "workflow"]
            }
        }

    def _setup_alert_thresholds(self):
        self.alert_thresholds = {
            ErrorSeverity.LOW: {"count": 100, "time_window": 3600},      # 100 errors per hour
            ErrorSeverity.MEDIUM: {"count": 50, "time_window": 3600},     # 50 errors per hour
            ErrorSeverity.HIGH: {"count": 20, "time_window": 3600},       # 20 errors per hour
            ErrorSeverity.CRITICAL: {"count": 5, "time_window": 1800}     # 5 errors per 30 minutes
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing ErrorMonitor...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            
            await self._setup_error_monitor_tables()
            await self._load_active_errors()
            await self._start_monitoring()
            
            self.logger.info("ErrorMonitor initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ErrorMonitor: {str(e)}")
            return False

    async def _setup_error_monitor_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS error_events (
                    id VARCHAR(255) PRIMARY KEY,
                    error_type VARCHAR(255) NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    source_file VARCHAR(500) NOT NULL,
                    line_number INTEGER NOT NULL,
                    function_name VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    request_id VARCHAR(255),
                    metadata JSONB,
                    fingerprint VARCHAR(255) NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    first_occurrence TIMESTAMP NOT NULL,
                    last_occurrence TIMESTAMP NOT NULL,
                    resolution_notes TEXT,
                    assigned_to VARCHAR(255),
                    tags JSONB NOT NULL
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS error_correlations (
                    id SERIAL PRIMARY KEY,
                    error_id VARCHAR(255) NOT NULL,
                    correlated_errors JSONB NOT NULL,
                    correlation_score DECIMAL(5,4) NOT NULL,
                    common_patterns JSONB NOT NULL,
                    correlation_type VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (error_id) REFERENCES error_events(id) ON DELETE CASCADE
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS error_alerts (
                    id SERIAL PRIMARY KEY,
                    error_id VARCHAR(255) NOT NULL,
                    alert_type VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by VARCHAR(255),
                    acknowledged_at TIMESTAMP,
                    FOREIGN KEY (error_id) REFERENCES error_events(id) ON DELETE CASCADE
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_events_fingerprint ON error_events(fingerprint);
                CREATE INDEX IF NOT EXISTS idx_error_events_timestamp ON error_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_error_events_severity ON error_events(severity);
                CREATE INDEX IF NOT EXISTS idx_error_events_status ON error_events(status);
            """)
            
            await session.commit()

    async def _start_monitoring(self):
        # Start background monitoring tasks
        asyncio.create_task(self._monitor_error_thresholds())
        asyncio.create_task(self._correlate_errors())
        asyncio.create_task(self._cleanup_old_errors())

    async def capture_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorEvent:
        try:
            # Extract error information
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = ''.join(traceback.format_exc())
            
            # Parse stack trace to extract source information
            source_info = self._parse_stack_trace(stack_trace)
            
            # Determine error category and severity
            category, severity, tags = self._classify_error(error_type, error_message, stack_trace)
            
            # Generate fingerprint for deduplication
            fingerprint = self._generate_error_fingerprint(error_type, error_message, source_info)
            
            # Check if this is a duplicate error
            existing_error = await self._find_existing_error(fingerprint)
            if existing_error:
                # Update existing error
                existing_error.occurrence_count += 1
                existing_error.last_occurrence = datetime.utcnow()
                await self._update_error_occurrence(existing_error)
                return existing_error
            
            # Create new error event
            error_event = ErrorEvent(
                id=str(uuid.uuid4()),
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                severity=severity,
                category=category,
                status=ErrorStatus.NEW,
                source_file=source_info.get("file", "unknown"),
                line_number=source_info.get("line", 0),
                function_name=source_info.get("function", "unknown"),
                timestamp=datetime.utcnow(),
                user_id=context.get("user_id") if context else None,
                session_id=context.get("session_id") if context else None,
                request_id=context.get("request_id") if context else None,
                metadata=context or {},
                fingerprint=fingerprint,
                tags=tags
            )
            
            # Save to database
            await self._save_error_to_database(error_event)
            
            # Add to active errors
            self.active_errors[error_event.id] = error_event
            
            # Check if alert should be triggered
            await self._check_alert_thresholds(error_event)
            
            # Publish error event to Kafka
            await self._publish_error_event(error_event)
            
            self.logger.info(f"Error captured: {error_event.id} - {error_type}")
            return error_event
            
        except Exception as e:
            self.logger.error(f"Failed to capture error: {str(e)}")
            raise

    def _parse_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        try:
            lines = stack_trace.split('\n')
            for line in lines:
                if 'File "' in line and '.py"' in line:
                    # Extract file path and line number
                    file_match = re.search(r'File "([^"]+)"', line)
                    line_match = re.search(r'line (\d+)', line)
                    if file_match and line_match:
                        return {
                            "file": file_match.group(1),
                            "line": int(line_match.group(1))
                        }
                
                # Look for function name
                if ' in ' in line and line.strip().endswith(':'):
                    function_match = re.search(r' in ([^:]+):', line)
                    if function_match:
                        return {
                            "function": function_match.group(1).strip()
                        }
            
            return {}
        except Exception:
            return {}

    def _classify_error(self, error_type: str, error_message: str, stack_trace: str) -> Tuple[ErrorCategory, ErrorSeverity, List[str]]:
        # Check against known patterns
        for pattern_name, pattern_info in self.error_patterns.items():
            for pattern in pattern_info["patterns"]:
                if re.search(pattern, error_message.lower()) or re.search(pattern, stack_trace.lower()):
                    return pattern_info["category"], pattern_info["severity"], pattern_info["tags"]
        
        # Default classification based on error type
        if "Database" in error_type or "Connection" in error_type:
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH, ["database", "connection"]
        elif "Authentication" in error_type or "Auth" in error_type:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM, ["auth", "security"]
        elif "Validation" in error_type:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW, ["validation", "input"]
        elif "API" in error_type or "HTTP" in error_type:
            return ErrorCategory.EXTERNAL_API, ErrorSeverity.MEDIUM, ["api", "external"]
        else:
            return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM, ["unknown"]

    def _generate_error_fingerprint(self, error_type: str, error_message: str, source_info: Dict[str, Any]) -> str:
        # Create a unique fingerprint based on error characteristics
        fingerprint_data = f"{error_type}:{source_info.get('file', '')}:{source_info.get('line', '')}:{error_message[:100]}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()

    async def _find_existing_error(self, fingerprint: str) -> Optional[ErrorEvent]:
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, error_type, error_message, stack_trace, severity, category, status,
                       source_file, line_number, function_name, timestamp, user_id, session_id,
                       request_id, metadata, fingerprint, occurrence_count, first_occurrence,
                       last_occurrence, resolution_notes, assigned_to, tags
                FROM error_events WHERE fingerprint = %s AND status != %s
            """, (fingerprint, ErrorStatus.RESOLVED.value))
            
            row = result.fetchone()
            if row:
                return self._create_error_event_from_row(row)
        
        return None

    def _create_error_event_from_row(self, row) -> ErrorEvent:
        return ErrorEvent(
            id=row[0],
            error_type=row[1],
            error_message=row[2],
            stack_trace=row[3],
            severity=ErrorSeverity(row[4]),
            category=ErrorCategory(row[5]),
            status=ErrorStatus(row[6]),
            source_file=row[7],
            line_number=row[8],
            function_name=row[9],
            timestamp=row[10],
            user_id=row[11],
            session_id=row[12],
            request_id=row[13],
            metadata=row[14] if row[14] else {},
            fingerprint=row[15],
            occurrence_count=row[16],
            first_occurrence=row[17],
            last_occurrence=row[18],
            resolution_notes=row[19] or "",
            assigned_to=row[20],
            tags=row[21] if row[21] else []
        )

    async def _save_error_to_database(self, error_event: ErrorEvent):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO error_events (id, error_type, error_message, stack_trace, severity, category,
                                        status, source_file, line_number, function_name, timestamp,
                                        user_id, session_id, request_id, metadata, fingerprint,
                                        occurrence_count, first_occurrence, last_occurrence,
                                        resolution_notes, assigned_to, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                error_event.id, error_event.error_type, error_event.error_message, error_event.stack_trace,
                error_event.severity.value, error_event.category.value, error_event.status.value,
                error_event.source_file, error_event.line_number, error_event.function_name,
                error_event.timestamp, error_event.user_id, error_event.session_id, error_event.request_id,
                json.dumps(error_event.metadata), error_event.fingerprint, error_event.occurrence_count,
                error_event.first_occurrence, error_event.last_occurrence, error_event.resolution_notes,
                error_event.assigned_to, json.dumps(error_event.tags)
            ))
            await session.commit()

    async def _update_error_occurrence(self, error_event: ErrorEvent):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute("""
                UPDATE error_events 
                SET occurrence_count = %s, last_occurrence = %s
                WHERE id = %s
            """, (error_event.occurrence_count, error_event.last_occurrence, error_event.id))
            await session.commit()

    async def _check_alert_thresholds(self, error_event: ErrorEvent):
        threshold = self.alert_thresholds.get(error_event.severity)
        if not threshold:
            return
        
        # Check if threshold is exceeded
        recent_errors = await self._get_recent_errors_by_severity(
            error_event.severity, 
            threshold["time_window"]
        )
        
        if len(recent_errors) >= threshold["count"]:
            await self._create_alert(error_event, "threshold_exceeded", 
                                   f"Error threshold exceeded: {len(recent_errors)} {error_event.severity.value} errors in {threshold['time_window']} seconds")

    async def _get_recent_errors_by_severity(self, severity: ErrorSeverity, time_window: int) -> List[ErrorEvent]:
        if not self.database:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id, error_type, error_message, stack_trace, severity, category, status,
                       source_file, line_number, function_name, timestamp, user_id, session_id,
                       request_id, metadata, fingerprint, occurrence_count, first_occurrence,
                       last_occurrence, resolution_notes, assigned_to, tags
                FROM error_events 
                WHERE severity = %s AND timestamp >= %s
                ORDER BY timestamp DESC
            """, (severity.value, cutoff_time))
            
            errors = []
            for row in result.fetchall():
                errors.append(self._create_error_event_from_row(row))
            
            return errors

    async def _create_alert(self, error_event: ErrorEvent, alert_type: str, message: str):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO error_alerts (error_id, alert_type, message, severity)
                    VALUES (%s, %s, %s, %s)
                """, (error_event.id, alert_type, message, error_event.severity.value))
                await session.commit()
            
            self.logger.warning(f"Error alert created: {alert_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to create error alert: {str(e)}")

    async def _publish_error_event(self, error_event: ErrorEvent):
        if not self.kafka:
            return
        
        try:
            event_data = {
                "error_id": error_event.id,
                "error_type": error_event.error_type,
                "severity": error_event.severity.value,
                "category": error_event.category.value,
                "timestamp": error_event.timestamp.isoformat(),
                "source_file": error_event.source_file,
                "line_number": error_event.line_number
            }
            
            await self.kafka.publish_event("error_events", event_data)
            
        except Exception as e:
            self.logger.error(f"Failed to publish error event: {str(e)}")

    async def get_error_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        if not self.database:
            return {}
        
        # Calculate time range
        if time_range == "1h":
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == "6h":
            cutoff_time = datetime.utcnow() - timedelta(hours=6)
        elif time_range == "24h":
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
        elif time_range == "7d":
            cutoff_time = datetime.utcnow() - timedelta(days=7)
        else:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        async with self.database.get_session() as session:
            # Total errors
            result = await session.execute("""
                SELECT COUNT(*) FROM error_events WHERE timestamp >= %s
            """, (cutoff_time,))
            total_errors = result.scalar()
            
            # Errors by severity
            result = await session.execute("""
                SELECT severity, COUNT(*) FROM error_events 
                WHERE timestamp >= %s GROUP BY severity
            """, (cutoff_time,))
            errors_by_severity = dict(result.fetchall())
            
            # Errors by category
            result = await session.execute("""
                SELECT category, COUNT(*) FROM error_events 
                WHERE timestamp >= %s GROUP BY category
            """, (cutoff_time,))
            errors_by_category = dict(result.fetchall())
            
            # Top error types
            result = await session.execute("""
                SELECT error_type, COUNT(*) FROM error_events 
                WHERE timestamp >= %s GROUP BY error_type 
                ORDER BY COUNT(*) DESC LIMIT 10
            """, (cutoff_time,))
            top_error_types = dict(result.fetchall())
            
            # Error trend (hourly)
            result = await session.execute("""
                SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) 
                FROM error_events 
                WHERE timestamp >= %s 
                GROUP BY hour 
                ORDER BY hour
            """, (cutoff_time,))
            error_trend = [{"hour": row[0].isoformat(), "count": row[1]} for row in result.fetchall()]
        
        return {
            "time_range": time_range,
            "total_errors": total_errors,
            "errors_by_severity": errors_by_severity,
            "errors_by_category": errors_by_category,
            "top_error_types": top_error_types,
            "error_trend": error_trend,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _monitor_error_thresholds(self):
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for severity, threshold in self.alert_thresholds.items():
                    recent_errors = await self._get_recent_errors_by_severity(
                        severity, threshold["time_window"]
                    )
                    
                    if len(recent_errors) >= threshold["count"]:
                        # Check if alert already exists
                        if not await self._alert_exists(severity, "threshold_exceeded"):
                            await self._create_alert(
                                recent_errors[0], 
                                "threshold_exceeded",
                                f"Error threshold exceeded: {len(recent_errors)} {severity.value} errors in {threshold['time_window']} seconds"
                            )
                
            except Exception as e:
                self.logger.error(f"Error in threshold monitoring: {str(e)}")

    async def _alert_exists(self, severity: ErrorSeverity, alert_type: str) -> bool:
        if not self.database:
            return False
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT COUNT(*) FROM error_alerts 
                WHERE severity = %s AND alert_type = %s AND is_acknowledged = FALSE
            """, (severity.value, alert_type))
            
            return result.scalar() > 0

    async def _correlate_errors(self):
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Find errors that might be correlated
                recent_errors = await self._get_recent_errors_by_severity(
                    ErrorSeverity.MEDIUM, 3600  # Last hour
                )
                
                for error in recent_errors:
                    if error.status == ErrorStatus.NEW:
                        correlations = await self._find_error_correlations(error)
                        if correlations:
                            await self._create_error_correlation(error, correlations)
                
            except Exception as e:
                self.logger.error(f"Error in error correlation: {str(e)}")

    async def _find_error_correlations(self, error: ErrorEvent) -> List[str]:
        if not self.database:
            return []
        
        # Find errors with similar patterns
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT id FROM error_events 
                WHERE id != %s AND error_type = %s AND category = %s
                AND timestamp >= %s AND status != %s
            """, (
                error.id, error.error_type, error.category.value,
                error.timestamp - timedelta(hours=1), ErrorStatus.RESOLVED.value
            ))
            
            return [row[0] for row in result.fetchall()]

    async def _create_error_correlation(self, error: ErrorEvent, correlated_errors: List[str]):
        if not self.database:
            return
        
        try:
            correlation_score = min(0.9, len(correlated_errors) * 0.3)  # Simple scoring
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO error_correlations (error_id, correlated_errors, correlation_score,
                                                  common_patterns, correlation_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    error.id, json.dumps(correlated_errors), correlation_score,
                    json.dumps([error.error_type, error.category.value]), "pattern_similarity"
                ))
                await session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to create error correlation: {str(e)}")

    async def _cleanup_old_errors(self):
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                # Remove resolved errors older than 30 days
                cutoff_time = datetime.utcnow() - timedelta(days=30)
                
                if self.database:
                    async with self.database.get_session() as session:
                        await session.execute("""
                            DELETE FROM error_events 
                            WHERE status = %s AND last_occurrence < %s
                        """, (ErrorStatus.RESOLVED.value, cutoff_time))
                        await session.commit()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")

    async def close(self):
        self.logger.info("Closing ErrorMonitor...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_error_monitor: Optional[ErrorMonitor] = None

async def init_error_monitor() -> ErrorMonitor:
    global _error_monitor
    if not _error_monitor:
        _error_monitor = ErrorMonitor()
        await _error_monitor.initialize()
    return _error_monitor

async def get_error_monitor() -> ErrorMonitor:
    global _error_monitor
    if not _error_monitor:
        _error_monitor = await init_error_monitor()
    return _error_monitor
