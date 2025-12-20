import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class EscalationLevel(Enum):
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"
    LEVEL_5 = "level_5"

class EscalationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class EscalationTrigger(Enum):
    TIME_BASED = "time_based"
    SEVERITY_BASED = "severity_based"
    MANUAL = "manual"
    CONDITION_BASED = "condition_based"
    THRESHOLD_BASED = "threshold_based"

@dataclass
class EscalationRule:
    rule_id: str
    name: str
    description: str
    trigger: EscalationTrigger
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

@dataclass
class EscalationEvent:
    event_id: str
    rule_id: str
    alert_id: str
    level: EscalationLevel
    status: EscalationStatus
    triggered_at: datetime
    completed_at: Optional[datetime]
    assigned_to: Optional[str]
    actions_taken: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class EscalationAction:
    action_id: str
    name: str
    type: str
    parameters: Dict[str, Any]
    timeout_seconds: int
    retry_count: int
    is_active: bool

class EscalationManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.rules: Dict[str, EscalationRule] = {}
        self.actions: Dict[str, EscalationAction] = {}
        self.active_escalations: Dict[str, EscalationEvent] = {}
        self.escalation_timeouts: Dict[str, datetime] = {}
        self.max_concurrent_escalations = 50
        self.default_timeout_minutes = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing EscalationManager...")
            self.database = get_database()
            await self._setup_escalation_tables()
            await self._load_rules()
            await self._load_actions()
            await self._start_escalation_monitor()
            self.logger.info("EscalationManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize EscalationManager: {str(e)}")
            return False

    async def _setup_escalation_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS escalation_rules (
                    id SERIAL PRIMARY KEY,
                    rule_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    trigger VARCHAR(50) NOT NULL,
                    conditions JSONB NOT NULL,
                    actions JSONB NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS escalation_actions (
                    id SERIAL PRIMARY KEY,
                    action_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    parameters JSONB NOT NULL,
                    timeout_seconds INTEGER DEFAULT 300,
                    retry_count INTEGER DEFAULT 3,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS escalation_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    rule_id VARCHAR(255) NOT NULL,
                    alert_id VARCHAR(255) NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    assigned_to VARCHAR(255),
                    actions_taken JSONB,
                    metadata JSONB,
                    FOREIGN KEY (rule_id) REFERENCES escalation_rules(rule_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalation_events_alert_id 
                ON escalation_events(alert_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalation_events_status 
                ON escalation_events(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalation_events_triggered_at 
                ON escalation_events(triggered_at);
            """)
            
            await session.commit()

    async def _load_rules(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT rule_id, name, description, trigger, conditions, actions, 
                       is_active, priority, created_at, updated_at
                FROM escalation_rules
                WHERE is_active = TRUE
                ORDER BY priority DESC
            """)
            
            for row in result:
                rule = EscalationRule(
                    rule_id=row.rule_id,
                    name=row.name,
                    description=row.description,
                    trigger=EscalationTrigger(row.trigger),
                    conditions=row.conditions,
                    actions=row.actions,
                    is_active=row.is_active,
                    priority=row.priority,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.rules[rule.rule_id] = rule

    async def _load_actions(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT action_id, name, type, parameters, timeout_seconds, 
                       retry_count, is_active, created_at, updated_at
                FROM escalation_actions
                WHERE is_active = TRUE
            """)
            
            for row in result:
                action = EscalationAction(
                    action_id=row.action_id,
                    name=row.name,
                    type=row.type,
                    parameters=row.parameters,
                    timeout_seconds=row.timeout_seconds,
                    retry_count=row.retry_count,
                    is_active=row.is_active
                )
                self.actions[action.action_id] = action

    async def _start_escalation_monitor(self):
        asyncio.create_task(self._monitor_escalations())

    async def _monitor_escalations(self):
        while True:
            try:
                await self._check_timeout_escalations()
                await self._process_pending_escalations()
                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _check_timeout_escalations(self):
        now = datetime.utcnow()
        timeout_escalations = []
        
        for event_id, timeout in self.escalation_timeouts.items():
            if now > timeout:
                timeout_escalations.append(event_id)
        
        for event_id in timeout_escalations:
            await self._handle_escalation_timeout(event_id)
            del self.escalation_timeouts[event_id]

    async def _process_pending_escalations(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT event_id, rule_id, alert_id, level, actions_taken
                FROM escalation_events
                WHERE status = 'pending'
                ORDER BY triggered_at ASC
                LIMIT 10
            """)
            
            for row in result:
                if len(self.active_escalations) >= self.max_concurrent_escalations:
                    break
                
                await self._execute_escalation(
                    row.event_id, row.rule_id, row.alert_id, 
                    EscalationLevel(row.level), row.actions_taken
                )

    async def create_escalation_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        trigger: EscalationTrigger,
        conditions: Dict[str, Any],
        actions: List[Dict[str, Any]],
        priority: int = 0
    ) -> bool:
        try:
            if not self.database:
                return False
            
            rule = EscalationRule(
                rule_id=rule_id,
                name=name,
                description=description,
                trigger=trigger,
                conditions=conditions,
                actions=actions,
                is_active=True,
                priority=priority,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO escalation_rules (
                        rule_id, name, description, trigger, conditions, actions, 
                        is_active, priority
                    ) VALUES (
                        :rule_id, :name, :description, :trigger, :conditions, :actions, 
                        :is_active, :priority
                    )
                """, {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "trigger": rule.trigger.value,
                    "conditions": rule.conditions,
                    "actions": rule.actions,
                    "is_active": rule.is_active,
                    "priority": rule.priority
                })
                await session.commit()
            
            self.rules[rule_id] = rule
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create escalation rule: {str(e)}")
            return False

    async def create_escalation_action(
        self,
        action_id: str,
        name: str,
        action_type: str,
        parameters: Dict[str, Any],
        timeout_seconds: int = 300,
        retry_count: int = 3
    ) -> bool:
        try:
            if not self.database:
                return False
            
            action = EscalationAction(
                action_id=action_id,
                name=name,
                type=action_type,
                parameters=parameters,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
                is_active=True
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO escalation_actions (
                        action_id, name, type, parameters, timeout_seconds, retry_count, is_active
                    ) VALUES (
                        :action_id, :name, :type, :parameters, :timeout_seconds, :retry_count, :is_active
                    )
                """, {
                    "action_id": action.action_id,
                    "name": action.name,
                    "type": action.type,
                    "parameters": action.parameters,
                    "timeout_seconds": action.timeout_seconds,
                    "retry_count": action.retry_count,
                    "is_active": action.is_active
                })
                await session.commit()
            
            self.actions[action_id] = action
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create escalation action: {str(e)}")
            return False

    async def trigger_escalation(
        self,
        alert_id: str,
        rule_id: Optional[str] = None,
        level: EscalationLevel = EscalationLevel.LEVEL_1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            if not self.database:
                return None
            
            if rule_id and rule_id not in self.rules:
                self.logger.warning(f"Escalation rule not found: {rule_id}")
                return None
            
            if not rule_id:
                rule_id = await self._find_matching_rule(alert_id, metadata or {})
                if not rule_id:
                    self.logger.warning(f"No matching escalation rule found for alert: {alert_id}")
                    return None
            
            event_id = f"escalation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(alert_id) % 10000}"
            
            event = EscalationEvent(
                event_id=event_id,
                rule_id=rule_id,
                alert_id=alert_id,
                level=level,
                status=EscalationStatus.PENDING,
                triggered_at=datetime.utcnow(),
                completed_at=None,
                assigned_to=None,
                actions_taken=[],
                metadata=metadata or {}
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO escalation_events (
                        event_id, rule_id, alert_id, level, status, metadata
                    ) VALUES (
                        :event_id, :rule_id, :alert_id, :level, :status, :metadata
                    )
                """, {
                    "event_id": event.event_id,
                    "rule_id": event.rule_id,
                    "alert_id": event.alert_id,
                    "level": event.level.value,
                    "status": event.status.value,
                    "metadata": event.metadata
                })
                await session.commit()
            
            self.active_escalations[event_id] = event
            self.escalation_timeouts[event_id] = datetime.utcnow() + timedelta(minutes=self.default_timeout_minutes)
            
            self.logger.info(f"Escalation triggered: {event_id} for alert: {alert_id}")
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to trigger escalation: {str(e)}")
            return None

    async def _find_matching_rule(self, alert_id: str, metadata: Dict[str, Any]) -> Optional[str]:
        for rule_id, rule in self.rules.items():
            if await self._evaluate_rule_conditions(rule, alert_id, metadata):
                return rule_id
        return None

    async def _evaluate_rule_conditions(
        self, 
        rule: EscalationRule, 
        alert_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            conditions = rule.conditions
            
            if rule.trigger == EscalationTrigger.TIME_BASED:
                return await self._evaluate_time_conditions(conditions, alert_id)
            elif rule.trigger == EscalationTrigger.SEVERITY_BASED:
                return await self._evaluate_severity_conditions(conditions, alert_id)
            elif rule.trigger == EscalationTrigger.CONDITION_BASED:
                return await self._evaluate_custom_conditions(conditions, metadata)
            elif rule.trigger == EscalationTrigger.THRESHOLD_BASED:
                return await self._evaluate_threshold_conditions(conditions, alert_id)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate rule conditions: {str(e)}")
            return False

    async def _evaluate_time_conditions(self, conditions: Dict[str, Any], alert_id: str) -> bool:
        if not self.database:
            return False
        
        time_threshold = conditions.get("time_threshold_minutes", 30)
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT created_at FROM alerts 
                WHERE alert_id = :alert_id
            """, {"alert_id": alert_id})
            
            row = result.fetchone()
            if not row:
                return False
            
            alert_age = datetime.utcnow() - row.created_at
            return alert_age.total_seconds() / 60 >= time_threshold

    async def _evaluate_severity_conditions(self, conditions: Dict[str, Any], alert_id: str) -> bool:
        if not self.database:
            return False
        
        required_severity = conditions.get("severity", "critical")
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT severity FROM alerts 
                WHERE alert_id = :alert_id
            """, {"alert_id": alert_id})
            
            row = result.fetchone()
            if not row:
                return False
            
            severity_levels = {"info": 1, "warning": 2, "critical": 3, "emergency": 4}
            alert_severity_level = severity_levels.get(row.severity, 0)
            required_severity_level = severity_levels.get(required_severity, 0)
            
            return alert_severity_level >= required_severity_level

    async def _evaluate_custom_conditions(self, conditions: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        field = conditions.get("field")
        operator = conditions.get("operator", "equals")
        value = conditions.get("value")
        
        if not field or field not in metadata:
            return False
        
        field_value = metadata[field]
        
        if operator == "equals":
            return str(field_value) == str(value)
        elif operator == "not_equals":
            return str(field_value) != str(value)
        elif operator == "greater_than":
            return float(field_value) > float(value)
        elif operator == "less_than":
            return float(field_value) < float(value)
        elif operator == "contains":
            return str(value) in str(field_value)
        elif operator == "not_contains":
            return str(value) not in str(field_value)
        
        return False

    async def _evaluate_threshold_conditions(self, conditions: Dict[str, Any], alert_id: str) -> bool:
        if not self.database:
            return False
        
        threshold_type = conditions.get("threshold_type")
        threshold_value = conditions.get("threshold_value")
        time_window_minutes = conditions.get("time_window_minutes", 60)
        
        if threshold_type == "alert_count":
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as count FROM alerts 
                    WHERE created_at >= :start_time
                """, {
                    "start_time": datetime.utcnow() - timedelta(minutes=time_window_minutes)
                })
                
                row = result.fetchone()
                return row.count >= threshold_value
        
        return False

    async def _execute_escalation(
        self,
        event_id: str,
        rule_id: str,
        alert_id: str,
        level: EscalationLevel,
        actions_taken: List[Dict[str, Any]]
    ):
        try:
            if rule_id not in self.rules:
                self.logger.error(f"Escalation rule not found: {rule_id}")
                return
            
            rule = self.rules[rule_id]
            
            await self._update_escalation_status(event_id, EscalationStatus.IN_PROGRESS)
            
            for action_config in rule.actions:
                action_id = action_config.get("action_id")
                if action_id and action_id in self.actions:
                    action = self.actions[action_id]
                    success = await self._execute_action(action, alert_id, level, action_config)
                    
                    action_result = {
                        "action_id": action_id,
                        "action_name": action.name,
                        "success": success,
                        "timestamp": datetime.utcnow().isoformat(),
                        "parameters": action_config
                    }
                    actions_taken.append(action_result)
            
            await self._update_escalation_status(event_id, EscalationStatus.COMPLETED, actions_taken)
            
            if event_id in self.active_escalations:
                del self.active_escalations[event_id]
            if event_id in self.escalation_timeouts:
                del self.escalation_timeouts[event_id]
            
        except Exception as e:
            self.logger.error(f"Failed to execute escalation: {str(e)}")
            await self._update_escalation_status(event_id, EscalationStatus.FAILED)

    async def _execute_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            if action.type == "notification":
                return await self._execute_notification_action(action, alert_id, level, action_config)
            elif action.type == "webhook":
                return await self._execute_webhook_action(action, alert_id, level, action_config)
            elif action.type == "email":
                return await self._execute_email_action(action, alert_id, level, action_config)
            elif action.type == "sms":
                return await self._execute_sms_action(action, alert_id, level, action_config)
            elif action.type == "slack":
                return await self._execute_slack_action(action, alert_id, level, action_config)
            elif action.type == "escalate_level":
                return await self._execute_level_escalation_action(action, alert_id, level, action_config)
            elif action.type == "assign_user":
                return await self._execute_assign_user_action(action, alert_id, level, action_config)
            else:
                self.logger.warning(f"Unknown action type: {action.type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to execute action {action.action_id}: {str(e)}")
            return False

    async def _execute_notification_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            from .notification_manager import get_notification_manager
            notification_manager = await get_notification_manager()
            
            recipients = action_config.get("recipients", [])
            message = action_config.get("message", f"Alert {alert_id} escalated to {level.value}")
            subject = action_config.get("subject", f"Escalation: Alert {alert_id}")
            
            for recipient in recipients:
                await notification_manager.create_notification(
                    notification_type=action.parameters.get("type", "email"),
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    priority=action.parameters.get("priority", "high"),
                    metadata={"alert_id": alert_id, "escalation_level": level.value}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute notification action: {str(e)}")
            return False

    async def _execute_webhook_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            import requests
            
            webhook_url = action.parameters.get("url")
            if not webhook_url:
                return False
            
            payload = {
                "alert_id": alert_id,
                "escalation_level": level.value,
                "timestamp": datetime.utcnow().isoformat(),
                "action_config": action_config
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute webhook action: {str(e)}")
            return False

    async def _execute_email_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            from .notification_manager import get_notification_manager
            notification_manager = await get_notification_manager()
            
            recipients = action_config.get("recipients", [])
            subject = action_config.get("subject", f"Escalation: Alert {alert_id}")
            message = action_config.get("message", f"Alert {alert_id} has been escalated to {level.value}")
            
            for recipient in recipients:
                await notification_manager.create_notification(
                    notification_type="email",
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    priority="high",
                    metadata={"alert_id": alert_id, "escalation_level": level.value}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute email action: {str(e)}")
            return False

    async def _execute_sms_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            from .notification_manager import get_notification_manager
            notification_manager = await get_notification_manager()
            
            recipients = action_config.get("recipients", [])
            message = action_config.get("message", f"Alert {alert_id} escalated to {level.value}")
            
            for recipient in recipients:
                await notification_manager.create_notification(
                    notification_type="sms",
                    recipient=recipient,
                    subject="Alert Escalation",
                    message=message,
                    priority="urgent",
                    metadata={"alert_id": alert_id, "escalation_level": level.value}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute SMS action: {str(e)}")
            return False

    async def _execute_slack_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            from .notification_manager import get_notification_manager
            notification_manager = await get_notification_manager()
            
            message = action_config.get("message", f"Alert {alert_id} has been escalated to {level.value}")
            
            await notification_manager.create_notification(
                notification_type="slack",
                recipient="admin",
                subject="Alert Escalation",
                message=message,
                priority="high",
                metadata={"alert_id": alert_id, "escalation_level": level.value}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute Slack action: {str(e)}")
            return False

    async def _execute_level_escalation_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            next_level = action_config.get("next_level")
            if not next_level:
                return False
            
            next_level_enum = EscalationLevel(next_level)
            await self.trigger_escalation(alert_id, level=next_level_enum)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute level escalation action: {str(e)}")
            return False

    async def _execute_assign_user_action(
        self,
        action: EscalationAction,
        alert_id: str,
        level: EscalationLevel,
        action_config: Dict[str, Any]
    ) -> bool:
        try:
            assigned_user = action_config.get("assigned_user")
            if not assigned_user:
                return False
            
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE alerts 
                    SET assigned_to = :assigned_user, updated_at = CURRENT_TIMESTAMP
                    WHERE alert_id = :alert_id
                """, {
                    "assigned_user": assigned_user,
                    "alert_id": alert_id
                })
                await session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute assign user action: {str(e)}")
            return False

    async def _update_escalation_status(
        self,
        event_id: str,
        status: EscalationStatus,
        actions_taken: Optional[List[Dict[str, Any]]] = None
    ):
        if not self.database:
            return
        
        update_fields = ["status = :status"]
        params = {"event_id": event_id, "status": status.value}
        
        if status == EscalationStatus.COMPLETED:
            update_fields.append("completed_at = :completed_at")
            params["completed_at"] = datetime.utcnow()
        
        if actions_taken is not None:
            update_fields.append("actions_taken = :actions_taken")
            params["actions_taken"] = actions_taken
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE escalation_events 
                SET {', '.join(update_fields)}
                WHERE event_id = :event_id
            """, params)
            await session.commit()

    async def _handle_escalation_timeout(self, event_id: str):
        try:
            await self._update_escalation_status(event_id, EscalationStatus.FAILED)
            
            if event_id in self.active_escalations:
                del self.active_escalations[event_id]
            
            self.logger.warning(f"Escalation timeout: {event_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle escalation timeout: {str(e)}")

    async def get_escalation_events(
        self,
        alert_id: Optional[str] = None,
        status: Optional[EscalationStatus] = None,
        level: Optional[EscalationLevel] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EscalationEvent]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if alert_id:
            conditions.append("alert_id = :alert_id")
            params["alert_id"] = alert_id
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if level:
            conditions.append("level = :level")
            params["level"] = level.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT event_id, rule_id, alert_id, level, status, triggered_at, 
                       completed_at, assigned_to, actions_taken, metadata
                FROM escalation_events
                {where_clause}
                ORDER BY triggered_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            events = []
            for row in result:
                event = EscalationEvent(
                    event_id=row.event_id,
                    rule_id=row.rule_id,
                    alert_id=row.alert_id,
                    level=EscalationLevel(row.level),
                    status=EscalationStatus(row.status),
                    triggered_at=row.triggered_at,
                    completed_at=row.completed_at,
                    assigned_to=row.assigned_to,
                    actions_taken=row.actions_taken or [],
                    metadata=row.metadata or {}
                )
                events.append(event)
            
            return events

    async def get_escalation_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN level = 'level_1' THEN 1 END) as level_1,
                    COUNT(CASE WHEN level = 'level_2' THEN 1 END) as level_2,
                    COUNT(CASE WHEN level = 'level_3' THEN 1 END) as level_3,
                    COUNT(CASE WHEN level = 'level_4' THEN 1 END) as level_4,
                    COUNT(CASE WHEN level = 'level_5' THEN 1 END) as level_5
                FROM escalation_events
                WHERE triggered_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total": row.total,
                "completed": row.completed,
                "failed": row.failed,
                "in_progress": row.in_progress,
                "level_1": row.level_1,
                "level_2": row.level_2,
                "level_3": row.level_3,
                "level_4": row.level_4,
                "level_5": row.level_5,
                "success_rate": (row.completed / row.total * 100) if row.total > 0 else 0
            }

    async def cancel_escalation(self, event_id: str) -> bool:
        try:
            await self._update_escalation_status(event_id, EscalationStatus.CANCELLED)
            
            if event_id in self.active_escalations:
                del self.active_escalations[event_id]
            if event_id in self.escalation_timeouts:
                del self.escalation_timeouts[event_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel escalation: {str(e)}")
            return False

_escalation_manager: Optional[EscalationManager] = None

async def get_escalation_manager() -> EscalationManager:
    global _escalation_manager
    if _escalation_manager is None:
        _escalation_manager = EscalationManager()
        await _escalation_manager.initialize()
    return _escalation_manager

async def init_escalation_manager() -> EscalationManager:
    return await get_escalation_manager()
