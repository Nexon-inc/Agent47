import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from backend.core.database import get_database
from backend.core.logs import get_logger
from backend.core.config import get_settings
from backend.core.cache import get_redis
from backend.core.security import get_credential_encryption

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    DDoS_ATTACK = "ddos_attack"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    PHISHING = "phishing"

class ThreatStatus(Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

@dataclass
class SecurityThreat:
    id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    status: ThreatStatus
    source_ip: str
    user_id: Optional[str]
    description: str
    evidence: Dict[str, Any]
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    mitigation_actions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class SecurityRule:
    id: str
    name: str
    description: str
    threat_type: ThreatType
    conditions: Dict[str, Any]
    action: str
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

class ThreatDetection:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        # Use credential encryption API if needed; security manager not available in core.security
        self.credential_encryption = None

        # Initialize threat detection rules
        self._init_threat_rules()
    
    def _init_threat_rules(self):
        """Initialize default threat detection rules"""
        default_rules = [
            SecurityRule(
                id="brute_force_detection",
                name="Brute Force Attack Detection",
                description="Detect multiple failed login attempts from same IP",
                threat_type=ThreatType.BRUTE_FORCE,
                conditions={
                    "failed_attempts_threshold": 5,
                    "time_window_minutes": 15,
                    "ip_whitelist": []
                },
                action="block_ip"
            ),
            SecurityRule(
                id="sql_injection_detection",
                name="SQL Injection Detection",
                description="Detect SQL injection attempts in user input",
                threat_type=ThreatType.SQL_INJECTION,
                conditions={
                    "patterns": [
                        "SELECT.*FROM", "INSERT.*INTO", "UPDATE.*SET",
                        "DELETE.*FROM", "DROP.*TABLE", "UNION.*SELECT"
                    ],
                    "case_sensitive": False
                },
                action="block_request"
            ),
            SecurityRule(
                id="xss_detection",
                name="XSS Attack Detection",
                description="Detect cross-site scripting attempts",
                threat_type=ThreatType.XSS_ATTACK,
                conditions={
                    "patterns": [
                        "<script", "javascript:", "onerror=", "onload=",
                        "eval(", "document.cookie"
                    ],
                    "case_sensitive": False
                },
                action="sanitize_input"
            ),
            SecurityRule(
                id="ddos_detection",
                name="DDoS Attack Detection",
                description="Detect distributed denial of service attacks",
                threat_type=ThreatType.DDoS_ATTACK,
                conditions={
                    "requests_per_minute": 100,
                    "concurrent_connections": 50,
                    "time_window_minutes": 5
                },
                action="rate_limit"
            )
        ]
        
        for rule in default_rules:
            self.create_security_rule(rule)
    
    async def create_security_rule(self, rule: SecurityRule) -> SecurityRule:
        """Create a new security rule"""
        try:
            rule_dict = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "threat_type": rule.threat_type.value,
                "conditions": rule.conditions,
                "action": rule.action,
                "enabled": rule.enabled,
                "created_at": rule.created_at
            }
            
            await self.db.execute(
                """
                INSERT INTO security_rules 
                (id, name, description, threat_type, conditions, action, enabled, created_at)
                VALUES (:id, :name, :description, :threat_type, :conditions, :action, :enabled, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                name = :name, description = :description, threat_type = :threat_type,
                conditions = :conditions, action = :action, enabled = :enabled
                """,
                rule_dict
            )
            
            self.logger.info(f"Created security rule: {rule.name}")
            return rule
            
        except Exception as e:
            self.logger.error(f"Failed to create security rule: {e}")
            raise
    
    async def get_security_rules(self, threat_type: Optional[ThreatType] = None) -> List[SecurityRule]:
        """Get security rules, optionally filtered by threat type"""
        try:
            query = "SELECT * FROM security_rules WHERE enabled = true"
            params = {}
            
            if threat_type:
                query += " AND threat_type = :threat_type"
                params["threat_type"] = threat_type.value
            
            rows = await self.db.fetch_all(query, params)
            
            rules = []
            for row in rows:
                rule = SecurityRule(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    threat_type=ThreatType(row["threat_type"]),
                    conditions=row["conditions"],
                    action=row["action"],
                    enabled=row["enabled"],
                    created_at=row["created_at"]
                )
                rules.append(rule)
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Failed to get security rules: {e}")
            raise
    
    async def analyze_request(self, request_data: Dict[str, Any]) -> List[SecurityThreat]:
        """Analyze incoming request for security threats"""
        try:
            threats = []
            rules = await self.get_security_rules()
            
            for rule in rules:
                if await self._check_rule_conditions(rule, request_data):
                    threat = await self._create_threat(rule, request_data)
                    threats.append(threat)
                    
                    # Apply mitigation action
                    await self._apply_mitigation_action(rule.action, threat, request_data)
            
            return threats
            
        except Exception as e:
            self.logger.error(f"Failed to analyze request: {e}")
            return []
    
    async def _check_rule_conditions(self, rule: SecurityRule, request_data: Dict[str, Any]) -> bool:
        """Check if request matches rule conditions"""
        try:
            conditions = rule.conditions
            
            if rule.threat_type == ThreatType.BRUTE_FORCE:
                return await self._check_brute_force_conditions(conditions, request_data)
            elif rule.threat_type == ThreatType.SQL_INJECTION:
                return await self._check_sql_injection_conditions(conditions, request_data)
            elif rule.threat_type == ThreatType.XSS_ATTACK:
                return await self._check_xss_conditions(conditions, request_data)
            elif rule.threat_type == ThreatType.DDoS_ATTACK:
                return await self._check_ddos_conditions(conditions, request_data)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check rule conditions: {e}")
            return False
    
    async def _check_brute_force_conditions(self, conditions: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """Check brute force attack conditions"""
        try:
            source_ip = request_data.get("source_ip")
            if not source_ip:
                return False
            
            threshold = conditions.get("failed_attempts_threshold", 5)
            time_window = conditions.get("time_window_minutes", 15)
            
            # Check failed login attempts for this IP
            failed_attempts = await self.db.fetch_one(
                """
                SELECT COUNT(*) as count FROM login_attempts 
                WHERE source_ip = :source_ip AND success = false 
                AND created_at >= :since
                """,
                {
                    "source_ip": source_ip,
                    "since": datetime.utcnow() - timedelta(minutes=time_window)
                }
            )
            
            return failed_attempts["count"] >= threshold if failed_attempts else False
            
        except Exception as e:
            self.logger.error(f"Failed to check brute force conditions: {e}")
            return False
    
    async def _check_sql_injection_conditions(self, conditions: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """Check SQL injection conditions"""
        try:
            patterns = conditions.get("patterns", [])
            case_sensitive = conditions.get("case_sensitive", False)
            
            # Check all user inputs
            user_inputs = self._extract_user_inputs(request_data)
            
            for user_input in user_inputs:
                input_text = str(user_input)
                if not case_sensitive:
                    input_text = input_text.lower()
                
                for pattern in patterns:
                    pattern_text = pattern if case_sensitive else pattern.lower()
                    if pattern_text in input_text:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check SQL injection conditions: {e}")
            return False
    
    async def _check_xss_conditions(self, conditions: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """Check XSS attack conditions"""
        try:
            patterns = conditions.get("patterns", [])
            case_sensitive = conditions.get("case_sensitive", False)
            
            # Check all user inputs
            user_inputs = self._extract_user_inputs(request_data)
            
            for user_input in user_inputs:
                input_text = str(user_input)
                if not case_sensitive:
                    input_text = input_text.lower()
                
                for pattern in patterns:
                    pattern_text = pattern if case_sensitive else pattern.lower()
                    if pattern_text in input_text:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check XSS conditions: {e}")
            return False
    
    async def _check_ddos_conditions(self, conditions: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """Check DDoS attack conditions"""
        try:
            source_ip = request_data.get("source_ip")
            if not source_ip:
                return False
            
            requests_per_minute = conditions.get("requests_per_minute", 100)
            concurrent_connections = conditions.get("concurrent_connections", 50)
            time_window = conditions.get("time_window_minutes", 5)
            
            # Check request rate
            request_count = await self.db.fetch_one(
                """
                SELECT COUNT(*) as count FROM request_logs 
                WHERE source_ip = :source_ip 
                AND created_at >= :since
                """,
                {
                    "source_ip": source_ip,
                    "since": datetime.utcnow() - timedelta(minutes=time_window)
                }
            )
            
            if request_count and request_count["count"] >= requests_per_minute:
                return True
            
            # Check concurrent connections
            active_connections = await self.redis.get(f"connections:{source_ip}")
            if active_connections and int(active_connections) >= concurrent_connections:
                return True

            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check DDoS conditions: {e}")
            return False
    
    def _extract_user_inputs(self, request_data: Dict[str, Any]) -> List[str]:
        """Extract all user inputs from request data"""
        inputs = []
        
        # Extract from query parameters
        if "query_params" in request_data:
            for value in request_data["query_params"].values():
                inputs.append(str(value))
        
        # Extract from body data
        if "body" in request_data:
            if isinstance(request_data["body"], dict):
                for value in request_data["body"].values():
                    inputs.append(str(value))
            else:
                inputs.append(str(request_data["body"]))
        
        # Extract from headers
        if "headers" in request_data:
            for value in request_data["headers"].values():
                inputs.append(str(value))
        
        return inputs
    
    async def _create_threat(self, rule: SecurityRule, request_data: Dict[str, Any]) -> SecurityThreat:
        """Create a security threat record"""
        try:
            threat_id = f"threat_{datetime.utcnow().timestamp()}"
            
            # Determine threat level based on rule and context
            threat_level = self._determine_threat_level(rule, request_data)
            
            threat = SecurityThreat(
                id=threat_id,
                threat_type=rule.threat_type,
                threat_level=threat_level,
                status=ThreatStatus.DETECTED,
                source_ip=request_data.get("source_ip", "unknown"),
                user_id=request_data.get("user_id"),
                description=f"Detected {rule.threat_type.value} using rule: {rule.name}",
                evidence={
                    "rule_id": rule.id,
                    "request_data": request_data,
                    "conditions_met": rule.conditions
                }
            )
            
            # Store threat in database
            await self.db.execute(
                """
                INSERT INTO security_threats 
                (id, threat_type, threat_level, status, source_ip, user_id, description, evidence, detected_at)
                VALUES (:id, :threat_type, :threat_level, :status, :source_ip, :user_id, :description, :evidence, :detected_at)
                """,
                {
                    "id": threat.id,
                    "threat_type": threat.threat_type.value,
                    "threat_level": threat.threat_level.value,
                    "status": threat.status.value,
                    "source_ip": threat.source_ip,
                    "user_id": threat.user_id,
                    "description": threat.description,
                    "evidence": threat.evidence,
                    "detected_at": threat.detected_at
                }
            )
            
            # Send alert
            await self._send_threat_alert(threat)
            
            self.logger.warning(f"Security threat detected: {threat.threat_type.value} from {threat.source_ip}")
            return threat
            
        except Exception as e:
            self.logger.error(f"Failed to create threat: {e}")
            raise
    
    def _determine_threat_level(self, rule: SecurityRule, request_data: Dict[str, Any]) -> ThreatLevel:
        """Determine threat level based on rule and context"""
        # Base level on threat type
        base_levels = {
            ThreatType.BRUTE_FORCE: ThreatLevel.MEDIUM,
            ThreatType.SQL_INJECTION: ThreatLevel.HIGH,
            ThreatType.XSS_ATTACK: ThreatLevel.HIGH,
            ThreatType.CSRF_ATTACK: ThreatLevel.MEDIUM,
            ThreatType.DDoS_ATTACK: ThreatLevel.CRITICAL,
            ThreatType.SUSPICIOUS_ACTIVITY: ThreatLevel.LOW,
            ThreatType.UNAUTHORIZED_ACCESS: ThreatLevel.HIGH,
            ThreatType.DATA_BREACH: ThreatLevel.CRITICAL,
            ThreatType.MALWARE: ThreatLevel.HIGH,
            ThreatType.PHISHING: ThreatLevel.MEDIUM
        }
        
        base_level = base_levels.get(rule.threat_type, ThreatLevel.MEDIUM)
        
        # Escalate based on context
        if request_data.get("user_id"):  # Authenticated user
            base_level = ThreatLevel.HIGH if base_level == ThreatLevel.MEDIUM else base_level
        
        if rule.threat_type == ThreatType.DDoS_ATTACK:
            base_level = ThreatLevel.CRITICAL
        
        return base_level
    
    async def _apply_mitigation_action(self, action: str, threat: SecurityThreat, request_data: Dict[str, Any]):
        """Apply mitigation action for detected threat"""
        try:
            if action == "block_ip":
                await self._block_ip(threat.source_ip, threat.threat_level)
            elif action == "block_request":
                await self._block_request(request_data)
            elif action == "sanitize_input":
                await self._sanitize_input(request_data)
            elif action == "rate_limit":
                await self._rate_limit_ip(threat.source_ip)
            elif action == "alert_admin":
                await self._alert_admin(threat)
            
            # Update threat with mitigation action
            threat.mitigation_actions.append(action)
            await self.db.execute(
                "UPDATE security_threats SET mitigation_actions = :actions WHERE id = :id",
                {"actions": threat.mitigation_actions, "id": threat.id}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to apply mitigation action: {e}")
    
    async def _block_ip(self, ip_address: str, threat_level: ThreatLevel):
        """Block IP address"""
        try:
            # Calculate block duration based on threat level
            duration_map = {
                ThreatLevel.LOW: 300,      # 5 minutes
                ThreatLevel.MEDIUM: 3600,  # 1 hour
                ThreatLevel.HIGH: 86400,   # 24 hours
                ThreatLevel.CRITICAL: 604800  # 1 week
            }
            
            duration = duration_map.get(threat_level, 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=duration)
            
            await self.redis.setex(f"blocked_ip:{ip_address}", duration, "blocked")
            
            # Store in database
            await self.db.execute(
                """
                INSERT INTO blocked_ips (ip_address, reason, expires_at, created_at)
                VALUES (:ip_address, :reason, :expires_at, :created_at)
                ON CONFLICT (ip_address) DO UPDATE SET
                reason = :reason, expires_at = :expires_at
                """,
                {
                    "ip_address": ip_address,
                    "reason": f"Security threat: {threat_level.value}",
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to block IP: {e}")
    
    async def _block_request(self, request_data: Dict[str, Any]):
        """Block specific request"""
        try:
            # Store blocked request pattern
            request_hash = self.security.hash_data(str(request_data))
            await self.redis.setex(f"blocked_request:{request_hash}", 3600, "blocked")
            
        except Exception as e:
            self.logger.error(f"Failed to block request: {e}")
    
    async def _sanitize_input(self, request_data: Dict[str, Any]):
        """Sanitize user inputs"""
        try:
            # This would integrate with input sanitization service
            # For now, just log the action
            self.logger.info("Input sanitization applied")
            
        except Exception as e:
            self.logger.error(f"Failed to sanitize input: {e}")
    
    async def _rate_limit_ip(self, ip_address: str):
        """Apply rate limiting to IP"""
        try:
            # Set rate limit for this IP
            await self.redis.setex(f"rate_limit:{ip_address}", 300, "limited")
            
        except Exception as e:
            self.logger.error(f"Failed to rate limit IP: {e}")
    
    async def _alert_admin(self, threat: SecurityThreat):
        """Send alert to admin"""
        try:
            alert_data = {
                "type": "security_threat",
                "threat_id": threat.id,
                "threat_type": threat.threat_type.value,
                "threat_level": threat.threat_level.value,
                "source_ip": threat.source_ip,
                "description": threat.description
            }
            
            await self.redis.publish("admin:security_alerts", alert_data)
            
        except Exception as e:
            self.logger.error(f"Failed to alert admin: {e}")
    
    async def _send_threat_alert(self, threat: SecurityThreat):
        """Send threat alert to security team"""
        try:
            alert_data = {
                "type": "threat_detected",
                "threat_id": threat.id,
                "threat_type": threat.threat_type.value,
                "threat_level": threat.threat_level.value,
                "source_ip": threat.source_ip,
                "description": threat.description,
                "timestamp": threat.detected_at.isoformat()
            }
            
            await self.redis.publish("security:threats", alert_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send threat alert: {e}")
    
    async def get_active_threats(self, limit: int = 50) -> List[SecurityThreat]:
        """Get active security threats"""
        try:
            rows = await self.db.fetch_all(
                """
                SELECT * FROM security_threats 
                WHERE status IN ('detected', 'investigating')
                ORDER BY detected_at DESC 
                LIMIT :limit
                """,
                {"limit": limit}
            )
            
            threats = []
            for row in rows:
                threat = SecurityThreat(
                    id=row["id"],
                    threat_type=ThreatType(row["threat_type"]),
                    threat_level=ThreatLevel(row["threat_level"]),
                    status=ThreatStatus(row["status"]),
                    source_ip=row["source_ip"],
                    user_id=row["user_id"],
                    description=row["description"],
                    evidence=row["evidence"],
                    detected_at=row["detected_at"],
                    resolved_at=row["resolved_at"],
                    mitigation_actions=row.get("mitigation_actions", []),
                    tags=row.get("tags", [])
                )
                threats.append(threat)
            
            return threats
            
        except Exception as e:
            self.logger.error(f"Failed to get active threats: {e}")
            return []
    
    async def update_threat_status(self, threat_id: str, status: ThreatStatus, 
                                 notes: Optional[str] = None) -> bool:
        """Update threat status"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow(),
                "threat_id": threat_id
            }
            
            if status == ThreatStatus.RESOLVED:
                update_data["resolved_at"] = datetime.utcnow()
            
            if notes:
                update_data["notes"] = notes
            
            await self.db.execute(
                """
                UPDATE security_threats 
                SET status = :status, updated_at = :updated_at, resolved_at = :resolved_at
                WHERE id = :threat_id
                """,
                update_data
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update threat status: {e}")
            return False

# Singleton instance
_threat_detection = None

def get_threat_detection() -> ThreatDetection:
    global _threat_detection
    if _threat_detection is None:
        _threat_detection = ThreatDetection()
    return _threat_detection

def init_threat_detection():
    """Initialize threat detection system"""
    global _threat_detection
    _threat_detection = ThreatDetection()
    return _threat_detection
