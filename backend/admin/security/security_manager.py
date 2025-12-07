import asyncio
import uuid
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE = "malware"
    PHISHING = "phishing"

class SecurityEvent(Enum):
    LOGIN_ATTEMPT = "login_attempt"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    INTEGRATION_ACCESS = "integration_access"

@dataclass
class SecurityAlert:
    id: str
    threat_type: ThreatType
    security_level: SecurityLevel
    description: str
    source_ip: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityRule:
    id: str
    name: str
    description: str
    rule_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    is_active: bool = True
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class SecurityManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.settings = get_settings()

        self.security_alerts: Dict[str, SecurityAlert] = {}
        self.security_rules: Dict[str, SecurityRule] = {}
        self.blocked_ips: Dict[str, Dict[str, Any]] = {}
        self.suspicious_activities: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = logger

        self._setup_default_security_rules()

    def _setup_default_security_rules(self):
        self.default_rules = {
            "brute_force_detection": {
                "name": "Brute Force Detection",
                "description": "Detect multiple failed login attempts from the same IP",
                "rule_type": "rate_limit",
                "conditions": {
                    "event_type": "login_attempt",
                    "max_attempts": 5,
                    "time_window_minutes": 15,
                    "threshold": 5
                },
                "actions": ["block_ip", "alert_admin", "log_event"]
            },
            "sql_injection_detection": {
                "name": "SQL Injection Detection",
                "description": "Detect potential SQL injection attempts in user input",
                "rule_type": "pattern_matching",
                "conditions": {
                    "patterns": [
                        r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
                        r"(--|#|/\*|\*/)",
                        r"(\b(exec|execute|script)\b)"
                    ],
                    "severity": "high"
                },
                "actions": ["block_ip", "alert_admin", "log_event", "sanitize_input"]
            },
            "xss_detection": {
                "name": "XSS Attack Detection",
                "description": "Detect potential XSS attacks in user input",
                "rule_type": "pattern_matching",
                "conditions": {
                    "patterns": [
                        r"(<script[^>]*>.*?</script>)",
                        r"(javascript:.*)",
                        r"(on\w+\s*=)",
                        r"(<iframe[^>]*>)"
                    ],
                    "severity": "high"
                },
                "actions": ["block_ip", "alert_admin", "log_event", "sanitize_input"]
            },
            "rate_limit_violation": {
                "name": "Rate Limit Violation",
                "description": "Detect excessive API calls or requests",
                "rule_type": "rate_limit",
                "conditions": {
                    "max_requests": 100,
                    "time_window_minutes": 1,
                    "threshold": 100
                },
                "actions": ["rate_limit", "alert_admin", "log_event"]
            }
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SecurityManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()

            await self._setup_security_tables()
            await self._initialize_default_rules()
            await self._load_security_data()

            self.logger.info("SecurityManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize SecurityManager: {str(e)}")
            return False

    async def _setup_security_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id VARCHAR(255) PRIMARY KEY,
                    threat_type VARCHAR(100) NOT NULL,
                    security_level VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    source_ip INET NOT NULL,
                    user_id VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by VARCHAR(255),
                    resolved_at TIMESTAMP,
                    metadata JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS security_rules (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    rule_type VARCHAR(100) NOT NULL,
                    conditions JSONB NOT NULL,
                    actions JSONB NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id SERIAL PRIMARY KEY,
                    ip_address INET NOT NULL UNIQUE,
                    reason TEXT NOT NULL,
                    blocked_by VARCHAR(255) NOT NULL,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT FALSE,
                    metadata JSONB
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    user_id VARCHAR(255),
                    source_ip INET NOT NULL,
                    user_agent TEXT,
                    event_data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    security_level VARCHAR(50) DEFAULT 'low'
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS ip_reputation (
                    id SERIAL PRIMARY KEY,
                    ip_address INET NOT NULL UNIQUE,
                    reputation_score INTEGER DEFAULT 0,
                    threat_count INTEGER DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)

            await session.commit()

    async def _initialize_default_rules(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                for rule_id, rule_data in self.default_rules.items():
                    # Check if rule already exists
                    result = await session.execute(
                        "SELECT id FROM security_rules WHERE id = %s",
                        (rule_id,)
                    )
                    
                    if not result.fetchone():
                        await session.execute("""
                            INSERT INTO security_rules (id, name, description, rule_type, conditions, actions, priority)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            rule_id, rule_data["name"], rule_data["description"],
                            rule_data["rule_type"], json.dumps(rule_data["conditions"]),
                            json.dumps(rule_data["actions"]), rule_data.get("priority", 1)
                        ))

                await session.commit()
                self.logger.info("Default security rules initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize default security rules: {str(e)}")

    async def _load_security_data(self):
        try:
            await self._load_security_alerts()
            await self._load_blocked_ips()
            await self._load_security_rules()
        except Exception as e:
            self.logger.error(f"Failed to load security data: {str(e)}")

    async def _load_security_alerts(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, threat_type, security_level, description, source_ip, user_id,
                           timestamp, resolved, resolved_by, resolved_at, metadata
                    FROM security_alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                """)

                rows = result.fetchall()
                for row in rows:
                    alert = SecurityAlert(
                        id=row[0],
                        threat_type=ThreatType(row[1]),
                        security_level=SecurityLevel(row[2]),
                        description=row[3],
                        source_ip=row[4],
                        user_id=row[5],
                        timestamp=row[6],
                        resolved=row[7],
                        resolved_by=row[8],
                        resolved_at=row[9],
                        metadata=row[10] if row[10] else {}
                    )
                    self.security_alerts[alert.id] = alert

        except Exception as e:
            self.logger.error(f"Failed to load security alerts: {str(e)}")

    async def _load_blocked_ips(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT ip_address, reason, blocked_by, blocked_at, expires_at, is_permanent, metadata
                    FROM blocked_ips
                    WHERE expires_at > %s OR is_permanent = TRUE
                """, (datetime.utcnow(),))

                rows = result.fetchall()
                for row in rows:
                    self.blocked_ips[row[0]] = {
                        "reason": row[1],
                        "blocked_by": row[2],
                        "blocked_at": row[3],
                        "expires_at": row[4],
                        "is_permanent": row[5],
                        "metadata": row[6] if row[6] else {}
                    }

        except Exception as e:
            self.logger.error(f"Failed to load blocked IPs: {str(e)}")

    async def _load_security_rules(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, name, description, rule_type, conditions, actions, is_active, priority
                    FROM security_rules
                    WHERE is_active = TRUE
                    ORDER BY priority DESC
                """)

                rows = result.fetchall()
                for row in rows:
                    rule = SecurityRule(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        rule_type=row[3],
                        conditions=row[4] if row[4] else {},
                        actions=row[5] if row[5] else [],
                        is_active=row[6],
                        priority=row[7]
                    )
                    self.security_rules[rule.id] = rule

        except Exception as e:
            self.logger.error(f"Failed to load security rules: {str(e)}")

    async def analyze_security_event(self, event_type: SecurityEvent, user_id: Optional[str],
                                   source_ip: str, user_agent: str = None, event_data: Dict[str, Any] = None) -> List[SecurityAlert]:
        try:
            alerts = []
            
            # Log the security event
            await self._log_security_event(event_type, user_id, source_ip, user_agent, event_data)
            
            # Check IP reputation
            ip_reputation = await self._get_ip_reputation(source_ip)
            
            # Apply security rules
            for rule in self.security_rules.values():
                if rule.is_active:
                    rule_alerts = await self._evaluate_security_rule(rule, event_type, user_id, source_ip, event_data, ip_reputation)
                    alerts.extend(rule_alerts)
            
            # Update IP reputation
            await self._update_ip_reputation(source_ip, event_type, event_data)
            
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to analyze security event: {str(e)}")
            return []

    async def _evaluate_security_rule(self, rule: SecurityRule, event_type: SecurityEvent, user_id: Optional[str],
                                    source_ip: str, event_data: Dict[str, Any], ip_reputation: Dict[str, Any]) -> List[SecurityAlert]:
        try:
            alerts = []
            
            if rule.rule_type == "rate_limit":
                rule_alerts = await self._evaluate_rate_limit_rule(rule, event_type, user_id, source_ip, event_data)
                alerts.extend(rule_alerts)
            elif rule.rule_type == "pattern_matching":
                rule_alerts = await self._evaluate_pattern_matching_rule(rule, event_type, user_id, source_ip, event_data)
                alerts.extend(rule_alerts)
            
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to evaluate security rule: {str(e)}")
            return []

    async def _evaluate_rate_limit_rule(self, rule: SecurityRule, event_type: SecurityEvent, user_id: Optional[str],
                                      source_ip: str, event_data: Dict[str, Any]) -> List[SecurityAlert]:
        try:
            alerts = []
            conditions = rule.conditions
            
            if event_type.value != conditions.get("event_type"):
                return alerts
            
            # Check rate limit
            time_window = timedelta(minutes=conditions.get("time_window_minutes", 15))
            max_attempts = conditions.get("max_attempts", 5)
            
            recent_events = await self._get_recent_events(source_ip, event_type, time_window)
            
            if len(recent_events) >= max_attempts:
                # Create security alert
                alert = SecurityAlert(
                    id=str(uuid.uuid4()),
                    threat_type=ThreatType.BRUTE_FORCE if event_type == SecurityEvent.LOGIN_ATTEMPT else ThreatType.RATE_LIMIT_VIOLATION,
                    security_level=SecurityLevel.HIGH,
                    description=f"Rate limit exceeded for {event_type.value} from IP {source_ip}",
                    source_ip=source_ip,
                    user_id=user_id,
                    metadata={
                        "rule_id": rule.id,
                        "event_count": len(recent_events),
                        "max_allowed": max_attempts,
                        "time_window": conditions.get("time_window_minutes")
                    }
                )
                
                alerts.append(alert)
                
                # Execute actions
                await self._execute_security_actions(rule.actions, alert)
            
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to evaluate rate limit rule: {str(e)}")
            return []

    async def _evaluate_pattern_matching_rule(self, rule: SecurityRule, event_type: SecurityEvent, user_id: Optional[str],
                                            source_ip: str, event_data: Dict[str, Any]) -> List[SecurityAlert]:
        try:
            alerts = []
            conditions = rule.conditions
            patterns = conditions.get("patterns", [])
            
            # Check if any patterns match
            for pattern in patterns:
                if self._check_pattern_match(pattern, event_data):
                    # Create security alert
                    alert = SecurityAlert(
                        id=str(uuid.uuid4()),
                        threat_type=ThreatType.SQL_INJECTION if "sql" in rule.id.lower() else ThreatType.XSS_ATTACK,
                        security_level=SecurityLevel(conditions.get("severity", "medium")),
                        description=f"Pattern match detected for rule {rule.name} from IP {source_ip}",
                        source_ip=source_ip,
                        user_id=user_id,
                        metadata={
                            "rule_id": rule.id,
                            "matched_pattern": pattern,
                            "event_data": event_data
                        }
                    )
                    
                    alerts.append(alert)
                    
                    # Execute actions
                    await self._execute_security_actions(rule.actions, alert)
                    
                    break  # Only create one alert per rule
            
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to evaluate pattern matching rule: {str(e)}")
            return []

    def _check_pattern_match(self, pattern: str, event_data: Dict[str, Any]) -> bool:
        try:
            if not event_data:
                return False
            
            # Convert event data to string for pattern matching
            data_string = json.dumps(event_data).lower()
            
            # Check if pattern matches
            return bool(re.search(pattern, data_string, re.IGNORECASE))
            
        except Exception as e:
            self.logger.error(f"Failed to check pattern match: {str(e)}")
            return False

    async def _execute_security_actions(self, actions: List[str], alert: SecurityAlert):
        try:
            for action in actions:
                if action == "block_ip":
                    await self.block_ip_address(alert.source_ip, f"Security alert: {alert.description}", "system")
                elif action == "alert_admin":
                    await self._send_admin_alert(alert)
                elif action == "log_event":
                    await self._log_security_alert(alert)
                elif action == "sanitize_input":
                    # Input sanitization would be handled at the application level
                    pass

        except Exception as e:
            self.logger.error(f"Failed to execute security actions: {str(e)}")

    async def block_ip_address(self, ip_address: str, reason: str, blocked_by: str,
                             duration_hours: int = 24, is_permanent: bool = False) -> bool:
        try:
            expires_at = None
            if not is_permanent and duration_hours:
                expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

            # Add to blocked IPs
            self.blocked_ips[ip_address] = {
                "reason": reason,
                "blocked_by": blocked_by,
                "blocked_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_permanent": is_permanent,
                "metadata": {}
            }

            # Store in database
            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO blocked_ips (ip_address, reason, blocked_by, expires_at, is_permanent)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET
                        reason = EXCLUDED.reason,
                        blocked_by = EXCLUDED.blocked_by,
                        expires_at = EXCLUDED.expires_at,
                        is_permanent = EXCLUDED.is_permanent
                """, (ip_address, reason, blocked_by, expires_at, is_permanent))
                await session.commit()

            self.logger.info(f"IP address {ip_address} blocked by {blocked_by}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to block IP address: {str(e)}")
            return False

    async def unblock_ip_address(self, ip_address: str, unblocked_by: str) -> bool:
        try:
            if ip_address in self.blocked_ips:
                del self.blocked_ips[ip_address]

            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE blocked_ips
                    SET expires_at = %s
                    WHERE ip_address = %s
                """, (datetime.utcnow(), ip_address))
                await session.commit()

            self.logger.info(f"IP address {ip_address} unblocked by {unblocked_by}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unblock IP address: {str(e)}")
            return False

    async def is_ip_blocked(self, ip_address: str) -> bool:
        if ip_address in self.blocked_ips:
            blocked_info = self.blocked_ips[ip_address]
            
            # Check if block has expired
            if not blocked_info["is_permanent"] and blocked_info["expires_at"]:
                if datetime.utcnow() > blocked_info["expires_at"]:
                    # Remove expired block
                    del self.blocked_ips[ip_address]
                    return False
            
            return True
        
        return False

    async def _log_security_event(self, event_type: SecurityEvent, user_id: Optional[str],
                                source_ip: str, user_agent: str = None, event_data: Dict[str, Any] = None):
        try:
            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO security_events (event_type, user_id, source_ip, user_agent, event_data)
                    VALUES (%s, %s, %s, %s, %s)
                """, (event_type.value, user_id, source_ip, user_agent, json.dumps(event_data or {})))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to log security event: {str(e)}")

    async def _log_security_alert(self, alert: SecurityAlert):
        try:
            # Store alert in database
            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO security_alerts (id, threat_type, security_level, description, source_ip, user_id, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    alert.id, alert.threat_type.value, alert.security_level.value,
                    alert.description, alert.source_ip, alert.user_id, json.dumps(alert.metadata)
                ))
                await session.commit()

            # Add to cache
            self.security_alerts[alert.id] = alert

        except Exception as e:
            self.logger.error(f"Failed to log security alert: {str(e)}")

    async def _send_admin_alert(self, alert: SecurityAlert):
        try:
            # This would integrate with notification system
            # For now, just log it
            self.logger.warning(f"ADMIN ALERT: {alert.description} - IP: {alert.source_ip} - Level: {alert.security_level.value}")
            
            # Could also send email, Slack notification, etc.
            
        except Exception as e:
            self.logger.error(f"Failed to send admin alert: {str(e)}")

    async def _get_recent_events(self, source_ip: str, event_type: SecurityEvent, time_window: timedelta) -> List[Dict[str, Any]]:
        try:
            if not self.database:
                return []

            start_time = datetime.utcnow() - time_window

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT event_type, user_id, source_ip, timestamp, event_data
                    FROM security_events
                    WHERE source_ip = %s AND event_type = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                """, (source_ip, event_type.value, start_time))

                rows = result.fetchall()
                events = []
                
                for row in rows:
                    events.append({
                        "event_type": row[0],
                        "user_id": row[1],
                        "source_ip": row[2],
                        "timestamp": row[3],
                        "event_data": row[4] if row[4] else {}
                    })

                return events

        except Exception as e:
            self.logger.error(f"Failed to get recent events: {str(e)}")
            return []

    async def _get_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        try:
            if not self.database:
                return {"reputation_score": 0, "threat_count": 0}

            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT reputation_score, threat_count, last_seen, first_seen, metadata
                    FROM ip_reputation WHERE ip_address = %s
                """, (ip_address,))

                row = result.fetchone()
                if row:
                    return {
                        "reputation_score": row[0],
                        "threat_count": row[1],
                        "last_seen": row[2],
                        "first_seen": row[3],
                        "metadata": row[4] if row[4] else {}
                    }
                else:
                    # Create new IP reputation record
                    await session.execute("""
                        INSERT INTO ip_reputation (ip_address, reputation_score, threat_count)
                        VALUES (%s, %s, %s)
                    """, (ip_address, 0, 0))
                    await session.commit()
                    
                    return {"reputation_score": 0, "threat_count": 0}

        except Exception as e:
            self.logger.error(f"Failed to get IP reputation: {str(e)}")
            return {"reputation_score": 0, "threat_count": 0}

    async def _update_ip_reputation(self, ip_address: str, event_type: SecurityEvent, event_data: Dict[str, Any]):
        try:
            if not self.database:
                return

            # Update last seen
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE ip_reputation
                    SET last_seen = %s
                    WHERE ip_address = %s
                """, (datetime.utcnow(), ip_address))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to update IP reputation: {str(e)}")

    async def get_security_alerts(self, resolved: bool = None, threat_type: ThreatType = None,
                                security_level: SecurityLevel = None) -> List[SecurityAlert]:
        alerts = list(self.security_alerts.values())
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
            
        if threat_type:
            alerts = [a for a in alerts if a.threat_type == threat_type]
            
        if security_level:
            alerts = [a for a in alerts if a.security_level == security_level]
            
        return alerts

    async def resolve_security_alert(self, alert_id: str, resolved_by: str, resolution_notes: str = "") -> bool:
        try:
            if alert_id not in self.security_alerts:
                return False

            alert = self.security_alerts[alert_id]
            alert.resolved = True
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.utcnow()

            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE security_alerts
                    SET resolved = TRUE, resolved_by = %s, resolved_at = %s
                    WHERE id = %s
                """, (resolved_by, alert.resolved_at, alert_id))
                await session.commit()

            self.logger.info(f"Security alert {alert_id} resolved by {resolved_by}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve security alert: {str(e)}")
            return False

    async def get_security_statistics(self, days: int = 30) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.database.get_session() as session:
                # Total alerts
                result = await session.execute("""
                    SELECT COUNT(*) FROM security_alerts WHERE timestamp >= %s
                """, (start_date,))
                total_alerts = result.scalar()

                # Resolved alerts
                result = await session.execute("""
                    SELECT COUNT(*) FROM security_alerts WHERE timestamp >= %s AND resolved = TRUE
                """, (start_date,))
                resolved_alerts = result.scalar()

                # Alerts by threat type
                result = await session.execute("""
                    SELECT threat_type, COUNT(*) FROM security_alerts
                    WHERE timestamp >= %s GROUP BY threat_type
                """, (start_date,))
                alerts_by_type = {row[0]: row[1] for row in result.fetchall()}

                # Blocked IPs
                result = await session.execute("""
                    SELECT COUNT(*) FROM blocked_ips WHERE blocked_at >= %s
                """, (start_date,))
                blocked_ips = result.scalar()

                return {
                    "total_alerts": total_alerts,
                    "resolved_alerts": resolved_alerts,
                    "pending_alerts": total_alerts - resolved_alerts,
                    "alerts_by_type": alerts_by_type,
                    "blocked_ips": blocked_ips,
                    "period_days": days
                }

        except Exception as e:
            self.logger.error(f"Failed to get security statistics: {str(e)}")
            return {}

    async def close(self):
        self.logger.info("Closing SecurityManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_security_manager: Optional[SecurityManager] = None

async def init_security_manager() -> SecurityManager:
    global _security_manager
    if not _security_manager:
        _security_manager = SecurityManager()
        await _security_manager.initialize()
    return _security_manager

async def get_security_manager() -> SecurityManager:
    global _security_manager
    if not _security_manager:
        _security_manager = await init_security_manager()
    return _security_manager
