import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.database import get_database
from core.cache import get_redis
from core.logs import get_logger
from core.config import get_config
from core.security import get_credential_encryption, credential_encryption


class ModerationAction(Enum):
    WARNING = "warning"
    SUSPENSION = "suspension"
    BAN = "ban"
    CONTENT_REMOVAL = "content_removal"
    FEATURE_RESTRICTION = "feature_restriction"
    ACCOUNT_VERIFICATION = "account_verification"


class ViolationType(Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    VIOLENCE = "violence"
    FRAUD = "fraud"
    COPYRIGHT = "copyright"
    TERMS_VIOLATION = "terms_violation"
    SECURITY_THREAT = "security_threat"


class ModerationStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


@dataclass
class ModerationReport:
    id: str
    reporter_id: str
    reported_user_id: str
    violation_type: ViolationType
    description: str
    evidence: List[str]
    severity: int
    status: ModerationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: str = ""


class ContentType(Enum):
    POST = "post"
    COMMENT = "comment"
    MESSAGE = "message"


@dataclass
class ModerationRule:
    id: str
    name: str
    description: str
    content_type: ContentType
    conditions: Dict[str, Any]
    action: Any
    severity: int = 1
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModerationCase:
    id: str
    user_id: str
    content_id: str
    content_type: ContentType
    content: str
    rule_id: str
    action: Any
    status: ModerationStatus
    moderator_id: Optional[str]
    reason: str
    evidence: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserModerationHistory:
    user_id: str
    total_violations: int
    total_warnings: int
    total_suspensions: int
    total_bans: int
    current_status: str
    last_violation: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class ModerationActionRecord:
    id: str
    user_id: str
    action_type: ModerationAction
    reason: str
    duration: Optional[int] = None  # days
    admin_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    notes: str = ""


@dataclass
class ContentFilter:
    id: str
    filter_type: str
    pattern: str
    action: str
    severity: int
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class UserModeration:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        # credential encryption is async to initialize — resolve during initialize()
        self.credential_encryption = None
        self.content_filters: List[ContentFilter] = []
        self.active_moderations: Dict[str, ModerationAction] = {}

        # Initialize moderation rules
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default moderation rules"""
        default_rules = [
            ModerationRule(
                id="spam_detection",
                name="Spam Detection",
                description="Detect and flag spam content",
                content_type=ContentType.POST,
                conditions={"keywords": ["buy now", "click here", "limited time"], "frequency": 5},
                action=ModerationAction.FLAG,
                severity=2
            ),
            ModerationRule(
                id="inappropriate_content",
                name="Inappropriate Content",
                description="Detect inappropriate or offensive content",
                content_type=ContentType.POST,
                conditions={"keywords": ["hate", "violence", "explicit"], "ai_detection": True},
                action=ModerationAction.SUSPENSION,
                severity=4
            ),
            ModerationRule(
                id="harassment",
                name="Harassment Detection",
                description="Detect harassment and bullying",
                content_type=ContentType.MESSAGE,
                conditions={"sentiment": "negative", "frequency": 3, "targeted": True},
                action=ModerationAction.BAN,
                severity=5
            )
        ]
        
        for rule in default_rules:
            self.create_moderation_rule(rule)

    async def initialize(self):
        """Initialize the user moderation system"""
        try:
            # Initialize credential encryption (async)
            try:
                self.credential_encryption = await get_credential_encryption()
            except Exception:
                # If encryption system isn't available yet, log and continue — features may be limited
                self.logger.warning("Credential encryption not available during UserModeration.initialize()")

            await self._setup_moderation_tables()
            await self._load_content_filters()
            await self._load_active_moderations()
            self.logger.info("UserModeration initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize UserModeration: {e}")
            raise

    async def _setup_moderation_tables(self):
        """Create moderation system tables"""
        async with self.db.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS moderation_reports (
                    id VARCHAR(100) PRIMARY KEY,
                    reporter_id VARCHAR(100) NOT NULL,
                    reported_user_id VARCHAR(100) NOT NULL,
                    violation_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    evidence JSONB DEFAULT '[]',
                    severity INTEGER NOT NULL,
                    status VARCHAR(30) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(100),
                    resolution_notes TEXT DEFAULT '',
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS moderation_actions (
                    id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    reason TEXT NOT NULL,
                    duration INTEGER,
                    admin_id VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT DEFAULT '',
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS content_filters (
                    id VARCHAR(100) PRIMARY KEY,
                    filter_type VARCHAR(50) NOT NULL,
                    pattern TEXT NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    severity INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_violations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    violation_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    points INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    created_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.commit()

    async def _load_content_filters(self):
        """Load content filters from database"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM content_filters WHERE is_active = TRUE
                """)
                
                rows = result.fetchall()
                for row in rows:
                    filter_obj = ContentFilter(
                        id=row.id,
                        filter_type=row.filter_type,
                        pattern=row.pattern,
                        action=row.action,
                        severity=row.severity,
                        is_active=row.is_active,
                        created_at=row.created_at,
                        updated_at=row.updated_at
                    )
                    self.content_filters.append(filter_obj)
                
                self.logger.info(f"Loaded {len(self.content_filters)} content filters")
                
        except Exception as e:
            self.logger.error(f"Error loading content filters: {e}")

    async def _load_active_moderations(self):
        """Load active moderation actions from database"""
        try:
            async with self.db.get_session() as session:
                result = await session.execute("""
                    SELECT * FROM moderation_actions 
                    WHERE is_active = TRUE AND (expires_at IS NULL OR expires_at > NOW())
                """)
                
                rows = result.fetchall()
                for row in rows:
                    action = ModerationActionRecord(
                        id=row.id,
                        user_id=row.user_id,
                        action_type=ModerationAction(row.action_type),
                        reason=row.reason,
                        duration=row.duration,
                        admin_id=row.admin_id,
                        created_at=row.created_at,
                        expires_at=row.expires_at,
                        is_active=row.is_active,
                        notes=row.notes
                    )
                    self.active_moderations[action.id] = action
                
                self.logger.info(f"Loaded {len(self.active_moderations)} active moderations")
                
        except Exception as e:
            self.logger.error(f"Error loading active moderations: {e}")

    async def create_moderation_report(self, reporter_id: str, reported_user_id: str,
                                     violation_type: ViolationType, description: str,
                                     evidence: Optional[List[str]] = None,
                                     severity: int = 1) -> ModerationReport:
        """Create a new moderation report"""
        try:
            report_id = f"report_{uuid.uuid4().hex[:8]}"
            
            # Validate severity
            severity = max(1, min(5, severity))
            
            report = ModerationReport(
                id=report_id,
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                violation_type=violation_type,
                description=description,
                evidence=evidence or [],
                severity=severity,
                status=ModerationStatus.PENDING
            )
            
            # Save to database
            await self._save_report_to_database(report)
            
            # Auto-escalate high severity reports
            if severity >= 4:
                report.status = ModerationStatus.ESCALATED
                await self._update_report_status(report.id, ModerationStatus.ESCALATED)
            
            # Check for pattern of violations
            await self._check_violation_pattern(reported_user_id, violation_type)
            
            self.logger.info(f"Created moderation report {report_id} for user {reported_user_id}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error creating moderation report: {e}")
            raise

    async def _save_report_to_database(self, report: ModerationReport):
        """Save report to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO moderation_reports (
                        id, reporter_id, reported_user_id, violation_type, description,
                        evidence, severity, status, created_at
                    ) VALUES (
                        :id, :reporter_id, :reported_user_id, :violation_type, :description,
                        :evidence, :severity, :status, :created_at
                    )
                """, {
                    "id": report.id,
                    "reporter_id": report.reporter_id,
                    "reported_user_id": report.reported_user_id,
                    "violation_type": report.violation_type.value,
                    "description": report.description,
                    "evidence": report.evidence,
                    "severity": report.severity,
                    "status": report.status.value,
                    "created_at": report.created_at
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving report to database: {e}")
            raise

    async def _check_violation_pattern(self, user_id: str, violation_type: ViolationType):
        """Check if user has a pattern of violations"""
        try:
            async with self.db.get_session() as session:
                # Get recent violations
                result = await session.execute("""
                    SELECT COUNT(*) as violation_count, SUM(points) as total_points
                    FROM user_violations
                    WHERE user_id = :user_id 
                    AND created_at >= :cutoff_date
                """, {
                    "user_id": user_id,
                    "cutoff_date": datetime.utcnow() - timedelta(days=90)
                })
                
                row = result.fetchone()
                violation_count = row.violation_count or 0
                total_points = row.total_points or 0
                
                # Auto-moderate based on pattern
                if violation_count >= 5 or total_points >= 20:
                    await self._auto_moderate_user(user_id, violation_type, violation_count, total_points)
                    
        except Exception as e:
            self.logger.warning(f"Could not check violation pattern: {e}")

    async def _auto_moderate_user(self, user_id: str, violation_type: ViolationType,
                                violation_count: int, total_points: int):
        """Automatically moderate user based on violation pattern"""
        try:
            if total_points >= 30:
                action_type = ModerationAction.BAN
                duration = None  # Permanent
                reason = f"Automatic ban due to {violation_count} violations and {total_points} points"
            elif total_points >= 20:
                action_type = ModerationAction.SUSPENSION
                duration = 30  # 30 days
                reason = f"Automatic suspension due to {violation_count} violations and {total_points} points"
            elif violation_count >= 5:
                action_type = ModerationAction.WARNING
                duration = None
                reason = f"Automatic warning due to {violation_count} violations"
            else:
                return
            
            await self.take_moderation_action(
                user_id=user_id,
                action_type=action_type,
                reason=reason,
                duration=duration,
                admin_id="system",
                notes="Auto-generated based on violation pattern"
            )
            
        except Exception as e:
            self.logger.warning(f"Could not auto-moderate user: {e}")

    async def take_moderation_action(self, user_id: str, action_type: ModerationAction,
                                   reason: str, duration: Optional[int] = None,
                                   admin_id: str = "system", notes: str = "") -> ModerationActionRecord:
        """Take a moderation action against a user"""
        try:
            action_id = f"action_{uuid.uuid4().hex[:8]}"
            
            # Calculate expiration
            expires_at = None
            if duration:
                expires_at = datetime.utcnow() + timedelta(days=duration)
            
            action = ModerationActionRecord(
                id=action_id,
                user_id=user_id,
                action_type=action_type,
                reason=reason,
                duration=duration,
                admin_id=admin_id,
                expires_at=expires_at,
                notes=notes
            )
            
            # Save to database
            await self._save_action_to_database(action)
            
            # Add to active moderations
            self.active_moderations[action.id] = action
            
            # Apply the action
            await self._apply_moderation_action(action)
            
            # Log violation
            await self._log_violation(user_id, action_type, reason, self._get_violation_points(action_type))
            
            self.logger.info(f"Took moderation action {action_type.value} against user {user_id}")
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error taking moderation action: {e}")
            raise

    def _get_violation_points(self, action_type: ModerationAction) -> int:
        """Get violation points for a moderation action"""
        points_map = {
            ModerationAction.WARNING: 2,
            ModerationAction.SUSPENSION: 5,
            ModerationAction.BAN: 10,
            ModerationAction.CONTENT_REMOVAL: 3,
            ModerationAction.FEATURE_RESTRICTION: 4,
            ModerationAction.ACCOUNT_VERIFICATION: 1
        }
        return points_map.get(action_type, 1)

    async def _save_action_to_database(self, action: ModerationActionRecord):
        """Save moderation action to database"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO moderation_actions (
                        id, user_id, action_type, reason, duration, admin_id,
                        created_at, expires_at, notes
                    ) VALUES (
                        :id, :user_id, :action_type, :reason, :duration, :admin_id,
                        :created_at, :expires_at, :notes
                    )
                """, {
                    "id": action.id,
                    "user_id": action.user_id,
                    "action_type": action.action_type.value,
                    "reason": action.reason,
                    "duration": action.duration,
                    "admin_id": action.admin_id,
                    "created_at": action.created_at,
                    "expires_at": action.expires_at,
                    "notes": action.notes
                })
                await session.commit()
        except Exception as e:
            self.logger.error(f"Error saving action to database: {e}")
            raise

    async def _apply_moderation_action(self, action: ModerationActionRecord):
        """Apply the moderation action to the user"""
        try:
            if action.action_type == ModerationAction.BAN:
                await self._ban_user(action.user_id)
            elif action.action_type == ModerationAction.SUSPENSION:
                await self._suspend_user(action.user_id, action.duration)
            elif action.action_type == ModerationAction.WARNING:
                await self._warn_user(action.user_id)
            elif action.action_type == ModerationAction.FEATURE_RESTRICTION:
                await self._restrict_user_features(action.user_id)
            
        except Exception as e:
            self.logger.error(f"Error applying moderation action: {e}")

    async def _ban_user(self, user_id: str):
        """Ban a user from the platform"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE users SET status = 'banned', updated_at = :updated_at
                    WHERE id = :user_id
                """, {
                    "user_id": user_id,
                    "updated_at": datetime.utcnow()
                })
                await session.commit()
                
                # Store in Redis for quick access
                await self.redis.set(f"user:banned:{user_id}", "true", expire=86400)
                
        except Exception as e:
            self.logger.error(f"Error banning user {user_id}: {e}")

    async def _suspend_user(self, user_id: str, duration: int):
        """Suspend a user for a specified duration"""
        try:
            expires_at = datetime.utcnow() + timedelta(days=duration)
            
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE users SET status = 'suspended', updated_at = :updated_at
                    WHERE id = :user_id
                """, {
                    "user_id": user_id,
                    "updated_at": datetime.utcnow()
                })
                await session.commit()
                
                # Store suspension info in Redis
                suspension_data = {
                    "status": "suspended",
                    "expires_at": expires_at.isoformat(),
                    "duration_days": duration
                }
                await self.redis.set(f"user:suspended:{user_id}", suspension_data, expire=duration * 86400)
                
        except Exception as e:
            self.logger.error(f"Error suspending user {user_id}: {e}")

    async def _warn_user(self, user_id: str):
        """Send a warning to a user"""
        try:
            # Store warning in Redis
            warning_data = {
                "type": "warning",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "You have received a warning for violating platform policies."
            }
            await self.redis.set(f"user:warning:{user_id}", warning_data, expire=604800)  # 7 days
            
        except Exception as e:
            self.logger.error(f"Error warning user {user_id}: {e}")

    async def _restrict_user_features(self, user_id: str):
        """Restrict user features"""
        try:
            # Store feature restrictions in Redis
            restrictions = {
                "type": "feature_restriction",
                "timestamp": datetime.utcnow().isoformat(),
                "restricted_features": ["api_access", "agent_usage", "file_upload"]
            }
            await self.redis.set(f"user:restricted:{user_id}", restrictions, expire=86400)
            
        except Exception as e:
            self.logger.error(f"Error restricting user features {user_id}: {e}")

    async def _log_violation(self, user_id: str, action_type: ModerationAction,
                           description: str, points: int):
        """Log a user violation"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    INSERT INTO user_violations (
                        user_id, violation_type, description, severity, points, created_at
                    ) VALUES (
                        :user_id, :violation_type, :description, :severity, :points, :created_at
                    )
                """, {
                    "user_id": user_id,
                    "violation_type": action_type.value,
                    "description": description,
                    "severity": 1,  # Default severity
                    "points": points,
                    "created_at": datetime.utcnow()
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging violation: {e}")

    async def check_content(self, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Check content against filters and return moderation result"""
        try:
            violations = []
            total_severity = 0
            
            for content_filter in self.content_filters:
                if content_filter.filter_type == content_type:
                    if content_filter.pattern.lower() in content.lower():
                        violations.append({
                            "filter_id": content_filter.id,
                            "pattern": content_filter.pattern,
                            "action": content_filter.action,
                            "severity": content_filter.severity
                        })
                        total_severity += content_filter.severity
            
            # Determine action based on violations
            action = "allow"
            if violations:
                if total_severity >= 8:
                    action = "block"
                elif total_severity >= 5:
                    action = "flag"
                elif total_severity >= 3:
                    action = "review"
            
            return {
                "action": action,
                "violations": violations,
                "total_severity": total_severity,
                "requires_moderation": action != "allow"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking content: {e}")
            return {"action": "allow", "violations": [], "total_severity": 0, "requires_moderation": False}

    async def is_user_moderated(self, user_id: str) -> Dict[str, Any]:
        """Check if a user is currently under moderation"""
        try:
            # Check Redis first
            banned = await self.redis.get(f"user:banned:{user_id}")
            if banned:
                return {"moderated": True, "action": "banned", "expires_at": None}
            
            suspended = await self.redis.get(f"user:suspended:{user_id}")
            if suspended:
                return {"moderated": True, "action": "suspended", "expires_at": suspended.get("expires_at")}
            
            warning = await self.redis.get(f"user:warning:{user_id}")
            if warning:
                return {"moderated": True, "action": "warning", "expires_at": None}
            
            restricted = await self.redis.get(f"user:restricted:{user_id}")
            if restricted:
                return {"moderated": True, "action": "feature_restriction", "expires_at": None}
            
            return {"moderated": False, "action": None, "expires_at": None}
            
        except Exception as e:
            self.logger.error(f"Error checking user moderation status: {e}")
            return {"moderated": False, "action": None, "expires_at": None}

    async def get_user_violation_history(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get user's violation history"""
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                result = await session.execute("""
                    SELECT * FROM user_violations
                    WHERE user_id = :user_id AND created_at >= :cutoff_date
                    ORDER BY created_at DESC
                """, {
                    "user_id": user_id,
                    "cutoff_date": cutoff_date
                })
                
                rows = result.fetchall()
                violations = []
                for row in rows:
                    violations.append({
                        "id": row.id,
                        "violation_type": row.violation_type,
                        "description": row.description,
                        "severity": row.severity,
                        "points": row.points,
                        "created_at": row.created_at,
                        "expires_at": row.expires_at
                    })
                
                return violations
                
        except Exception as e:
            self.logger.error(f"Error getting user violation history: {e}")
            return []

    async def resolve_moderation_report(self, report_id: str, resolution: str,
                                     admin_id: str, action_taken: Optional[ModerationActionRecord] = None):
        """Resolve a moderation report"""
        try:
            async with self.db.get_session() as session:
                await session.execute("""
                    UPDATE moderation_reports
                    SET status = 'resolved', resolved_at = :resolved_at, 
                        resolved_by = :resolved_by, resolution_notes = :resolution_notes
                    WHERE id = :report_id
                """, {
                    "report_id": report_id,
                    "resolved_at": datetime.utcnow(),
                    "resolved_by": admin_id,
                    "resolution_notes": resolution
                })
                await session.commit()
            
            self.logger.info(f"Resolved moderation report {report_id} by admin {admin_id}")
            
        except Exception as e:
            self.logger.error(f"Error resolving moderation report: {e}")

    async def close(self):
        """Clean up resources"""
        self.logger.info("UserModeration closed")

    async def create_moderation_rule(self, rule: ModerationRule) -> ModerationRule:
        """Create a new moderation rule"""
        try:
            rule_dict = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "content_type": rule.content_type.value,
                "conditions": rule.conditions,
                "action": rule.action.value,
                "severity": rule.severity,
                "active": rule.active,
                "created_at": rule.created_at
            }
            
            await self.db.execute(
                """
                INSERT INTO moderation_rules 
                (id, name, description, content_type, conditions, action, severity, active, created_at)
                VALUES (:id, :name, :description, :content_type, :conditions, :action, :severity, :active, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                name = :name, description = :description, content_type = :content_type,
                conditions = :conditions, action = :action, severity = :severity,
                active = :active
                """,
                rule_dict
            )
            
            self.logger.info(f"Created moderation rule: {rule.name}")
            return rule
            
        except Exception as e:
            self.logger.error(f"Failed to create moderation rule: {e}")
            raise
    
    async def get_moderation_rules(self, content_type: Optional[ContentType] = None) -> List[ModerationRule]:
        """Get moderation rules, optionally filtered by content type"""
        try:
            query = "SELECT * FROM moderation_rules WHERE active = true"
            params = {}
            
            if content_type:
                query += " AND content_type = :content_type"
                params["content_type"] = content_type.value
            
            query += " ORDER BY severity DESC"
            
            rows = await self.db.fetch_all(query, params)
            
            rules = []
            for row in rows:
                rule = ModerationRule(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    content_type=ContentType(row["content_type"]),
                    conditions=row["conditions"],
                    action=ModerationAction(row["action"]),
                    severity=row["severity"],
                    active=row["active"],
                    created_at=row["created_at"]
                )
                rules.append(rule)
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Failed to get moderation rules: {e}")
            raise
    
    async def moderate_content(self, user_id: str, content_id: str, content_type: ContentType, content: str) -> List[ModerationCase]:
        """Moderate content against all active rules"""
        try:
            rules = await self.get_moderation_rules(content_type)
            cases = []
            
            for rule in rules:
                if await self._check_rule_conditions(rule, content, user_id):
                    case = await self._create_moderation_case(user_id, content_id, content_type, content, rule)
                    cases.append(case)
            
            if cases:
                await self._apply_moderation_actions(user_id, cases)
            
            return cases
            
        except Exception as e:
            self.logger.error(f"Failed to moderate content: {e}")
            raise
    
    async def _check_rule_conditions(self, rule: ModerationRule, content: str, user_id: str) -> bool:
        """Check if content matches rule conditions"""
        try:
            conditions = rule.conditions
            
            # Check keywords
            if "keywords" in conditions:
                keywords = conditions["keywords"]
                content_lower = content.lower()
                if any(keyword.lower() in content_lower for keyword in keywords):
                    return True
            
            # Check frequency
            if "frequency" in conditions:
                user_content_count = await self._get_user_content_count(user_id, rule.content_type)
                if user_content_count >= conditions["frequency"]:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check rule conditions: {e}")
            return False
    
    async def _create_moderation_case(self, user_id: str, content_id: str, content_type: ContentType, content: str, rule: ModerationRule) -> ModerationCase:
        """Create a moderation case"""
        try:
            case_id = f"case_{datetime.utcnow().timestamp()}_{user_id}"
            
            case = ModerationCase(
                id=case_id,
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                content=content,
                rule_id=rule.id,
                action=rule.action,
                status=ModerationStatus.PENDING,
                moderator_id=None,
                reason=f"Triggered rule: {rule.name}",
                evidence={"rule_id": rule.id, "severity": rule.severity}
            )
            
            # Store case in database
            await self.db.execute(
                """
                INSERT INTO moderation_cases 
                (id, user_id, content_id, content_type, content, rule_id, action, status, moderator_id, reason, evidence, created_at)
                VALUES (:id, :user_id, :content_id, :content_type, :content, :rule_id, :action, :status, :moderator_id, :reason, :evidence, :created_at)
                """,
                {
                    "id": case.id,
                    "user_id": case.user_id,
                    "content_id": case.content_id,
                    "content_type": case.content_type.value,
                    "content": case.content,
                    "rule_id": case.rule_id,
                    "action": case.action.value,
                    "status": case.status.value,
                    "moderator_id": case.moderator_id,
                    "reason": case.reason,
                    "evidence": case.evidence,
                    "created_at": case.created_at
                }
            )
            
            return case
            
        except Exception as e:
            self.logger.error(f"Failed to create moderation case: {e}")
            raise
    
    async def _apply_moderation_actions(self, user_id: str, cases: List[ModerationCase]):
        """Apply moderation actions to user"""
        try:
            for case in cases:
                if case.action == ModerationAction.WARN:
                    await self._warn_user(user_id, case)
                elif case.action == ModerationAction.SUSPENSION:
                    await self._suspend_user(user_id, case)
                elif case.action == ModerationAction.BAN:
                    await self._ban_user(user_id, case)
                elif case.action == ModerationAction.DELETE_CONTENT:
                    await self._delete_content(case.content_id, case.content_type)
                elif case.action == ModerationAction.FLAG:
                    await self._flag_content(case.content_id, case.content_type)
            
        except Exception as e:
            self.logger.error(f"Failed to apply moderation actions: {e}")
            raise
    
    async def _warn_user(self, user_id: str, case: ModerationCase):
        """Send warning to user"""
        try:
            notification_data = {
                "type": "moderation_warning",
                "title": "Content Warning",
                "message": f"Your content has been flagged: {case.reason}",
                "severity": "warning"
            }
            
            await self.redis.publish(f"user:{user_id}:notifications", notification_data)
            
            await self.db.execute(
                "UPDATE moderation_cases SET status = :status WHERE id = :id",
                {"status": ModerationStatus.APPROVED.value, "id": case.id}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to warn user: {e}")
    
    async def _suspend_user(self, user_id: str, case: ModerationCase):
        """Suspend user account"""
        try:
            duration = timedelta(hours=case.evidence.get("severity", 1) * 24)
            expires_at = datetime.utcnow() + duration
            
            await self.db.execute(
                "UPDATE users SET status = 'suspended', suspended_until = :expires_at WHERE id = :user_id",
                {"expires_at": expires_at, "user_id": user_id}
            )
            
            await self.db.execute(
                "UPDATE moderation_cases SET status = :status WHERE id = :id",
                {"status": ModerationStatus.APPROVED.value, "id": case.id}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to suspend user: {e}")
    
    async def _ban_user(self, user_id: str, case: ModerationCase):
        """Ban user account"""
        try:
            await self.db.execute(
                "UPDATE users SET status = 'banned', banned_at = :banned_at WHERE id = :user_id",
                {"banned_at": datetime.utcnow(), "user_id": user_id}
            )
            
            await self.db.execute(
                "UPDATE moderation_cases SET status = :status WHERE id = :id",
                {"status": ModerationStatus.APPROVED.value, "id": case.id}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to ban user: {e}")
    
    async def _delete_content(self, content_id: str, content_type: ContentType):
        """Delete flagged content"""
        try:
            table_map = {
                ContentType.POST: "posts",
                ContentType.COMMENT: "comments",
                ContentType.MESSAGE: "messages"
            }
            
            if content_type in table_map:
                table = table_map[content_type]
                await self.db.execute(f"DELETE FROM {table} WHERE id = :content_id", {"content_id": content_id})
                
        except Exception as e:
            self.logger.error(f"Failed to delete content: {e}")
    
    async def _flag_content(self, content_id: str, content_type: ContentType):
        """Flag content for review"""
        try:
            table_map = {
                ContentType.POST: "posts",
                ContentType.COMMENT: "comments",
                ContentType.MESSAGE: "messages"
            }
            
            if content_type in table_map:
                table = table_map[content_type]
                await self.db.execute(
                    f"UPDATE {table} SET flagged = true, flagged_at = :flagged_at WHERE id = :content_id",
                    {"flagged_at": datetime.utcnow(), "content_id": content_id}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to flag content: {e}")
    
    async def _update_user_moderation_history(self, user_id: str, cases: List[ModerationCase]):
        """Update user moderation history"""
        try:
            # Get current history
            history = await self.db.fetch_one(
                "SELECT * FROM user_moderation_history WHERE user_id = :user_id",
                {"user_id": user_id}
            )
            
            if not history:
                # Create new history
                await self.db.execute(
                    """
                    INSERT INTO user_moderation_history 
                    (user_id, total_violations, total_warnings, total_suspensions, total_bans, current_status, last_violation)
                    VALUES (:user_id, 0, 0, 0, 0, 'active', NULL)
                    """,
                    {"user_id": user_id}
                )
                history = {"total_violations": 0, "total_warnings": 0, "total_suspensions": 0, "total_bans": 0}
            
            # Update counts
            for case in cases:
                if case.action == ModerationAction.WARN:
                    history["total_warnings"] += 1
                elif case.action == ModerationAction.SUSPENSION:
                    history["total_suspensions"] += 1
                elif case.action == ModerationAction.BAN:
                    history["total_bans"] += 1
                
                history["total_violations"] += 1
            
            # Update database
            await self.db.execute(
                """
                UPDATE user_moderation_history SET
                total_violations = :total_violations,
                total_warnings = :total_warnings,
                total_suspensions = :total_suspensions,
                total_bans = :total_bans,
                last_violation = :last_violation,
                updated_at = :updated_at
                WHERE user_id = :user_id
                """,
                {
                    "total_violations": history["total_violations"],
                    "total_warnings": history["total_warnings"],
                    "total_suspensions": history["total_suspensions"],
                    "total_bans": history["total_bans"],
                    "last_violation": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update user moderation history: {e}")
    
    async def _get_user_content_count(self, user_id: str, content_type: ContentType) -> int:
        """Get user content count for frequency checking"""
        try:
            table_map = {
                ContentType.POST: "posts",
                ContentType.COMMENT: "comments",
                ContentType.MESSAGE: "messages"
            }
            
            if content_type in table_map:
                table = table_map[content_type]
                result = await self.db.fetch_one(
                    f"SELECT COUNT(*) as count FROM {table} WHERE user_id = :user_id AND created_at >= :since",
                    {
                        "user_id": user_id,
                        "since": datetime.utcnow() - timedelta(hours=1)
                    }
                )
                return result["count"] if result else 0
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to get user content count: {e}")
            return 0
    
    async def _analyze_sentiment(self, content: str) -> str:
        """Analyze content sentiment using keyword-based analysis"""
        try:
            if not content or len(content.strip()) == 0:
                return "neutral"
            
            content_lower = content.lower()
            
            # Positive sentiment keywords
            positive_keywords = [
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
                'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'thank', 'thanks',
                'helpful', 'useful', 'perfect', 'best', 'outstanding', 'brilliant', 'superb',
                'appreciate', 'grateful', 'delighted', 'impressed', 'recommend', 'favorite'
            ]
            
            # Negative sentiment keywords
            negative_keywords = [
                'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'angry',
                'frustrated', 'disappointed', 'annoyed', 'upset', 'unhappy', 'dissatisfied',
                'useless', 'broken', 'error', 'bug', 'problem', 'issue', 'fail', 'failed',
                'poor', 'slow', 'crash', 'stupid', 'ridiculous', 'pathetic', 'garbage'
            ]
            
            # Count positive and negative keywords
            positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
            negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
            
            # Determine sentiment
            if positive_count > negative_count and positive_count > 0:
                return "positive"
            elif negative_count > positive_count and negative_count > 0:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            self.logger.warning(f"Error analyzing sentiment: {e}")
            return "neutral"
    
    async def get_user_moderation_history(self, user_id: str) -> Optional[UserModerationHistory]:
        """Get user moderation history"""
        try:
            row = await self.db.fetch_one(
                "SELECT * FROM user_moderation_history WHERE user_id = :user_id",
                {"user_id": user_id}
            )
            
            if row:
                return UserModerationHistory(
                    user_id=row["user_id"],
                    total_violations=row["total_violations"],
                    total_warnings=row["total_warnings"],
                    total_suspensions=row["total_suspensions"],
                    total_bans=row["total_bans"],
                    current_status=row["current_status"],
                    last_violation=row["last_violation"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user moderation history: {e}")
            return None
    
    async def get_pending_moderation_cases(self, limit: int = 50) -> List[ModerationCase]:
        """Get pending moderation cases for review"""
        try:
            rows = await self.db.fetch_all(
                """
                SELECT * FROM moderation_cases 
                WHERE status = 'pending' 
                ORDER BY created_at DESC 
                LIMIT :limit
                """,
                {"limit": limit}
            )
            
            cases = []
            for row in rows:
                case = ModerationCase(
                    id=row["id"],
                    user_id=row["user_id"],
                    content_id=row["content_id"],
                    content_type=ContentType(row["content_type"]),
                    content=row["content"],
                    rule_id=row["rule_id"],
                    action=ModerationAction(row["action"]),
                    status=ModerationStatus(row["status"]),
                    moderator_id=row["moderator_id"],
                    reason=row["reason"],
                    evidence=row["evidence"],
                    created_at=row["created_at"]
                )
                cases.append(case)
            
            return cases
            
        except Exception as e:
            self.logger.error(f"Failed to get pending moderation cases: {e}")
            return []

# Singleton instance
_user_moderation = None

def get_user_moderation() -> UserModeration:
    global _user_moderation
    if _user_moderation is None:
        _user_moderation = UserModeration()
    return _user_moderation

def init_user_moderation():
    """Initialize user moderation system"""
    global _user_moderation
    _user_moderation = UserModeration()
    return _user_moderation
