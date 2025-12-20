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

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class AlertSource(Enum):
    SYSTEM = "system"
    DATABASE = "database"
    SERVER = "server"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class Alert:
    alert_id: str
    source: AlertSource
    severity: AlertSeverity
    title: str
    message: str
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    metadata: Dict[str, Any]

class AlertManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.active_alerts = {}
        self.alert_rules = {}
        self.escalation_rules = {}
        self.notification_channels = {}

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AlertManager...")
            self.database = get_database()
            await self._setup_alert_tables()
            await self._load_alert_rules()
            await self._load_escalation_rules()
            await self._setup_notification_channels()
            self.logger.info("AlertManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AlertManager: {str(e)}")
            return False

    async def _setup_alert_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(255) UNIQUE NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP,
                    assigned_to VARCHAR(255),
                    metadata JSONB,
                    escalation_level INTEGER DEFAULT 0,
                    last_escalation TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id SERIAL PRIMARY KEY,
                    rule_name VARCHAR(255) UNIQUE NOT NULL,
                    source VARCHAR(50) NOT NULL,
                    condition_type VARCHAR(50) NOT NULL,
                    condition_value TEXT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS escalation_rules (
                    id SERIAL PRIMARY KEY,
                    alert_source VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    escalation_level INTEGER NOT NULL,
                    timeout_minutes INTEGER NOT NULL,
                    notification_channels JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS alert_notifications (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(255) NOT NULL,
                    channel_type VARCHAR(50) NOT NULL,
                    recipient VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'sent',
                    error_message TEXT
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_status 
                ON alerts(status)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_severity 
                ON alerts(severity)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_created_at 
                ON alerts(created_at)
            """))
            
            await session.commit()

    async def _load_alert_rules(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT rule_name, source, condition_type, condition_value, severity, enabled
                    FROM alert_rules WHERE enabled = TRUE
                """))
                
                for row in result.fetchall():
                    self.alert_rules[row[0]] = {
                        "source": row[1],
                        "condition_type": row[2],
                        "condition_value": row[3],
                        "severity": row[4],
                        "enabled": row[5]
                    }
        except Exception as e:
            self.logger.error(f"Failed to load alert rules: {str(e)}")

    async def _load_escalation_rules(self):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT alert_source, severity, escalation_level, timeout_minutes, notification_channels
                    FROM escalation_rules ORDER BY escalation_level ASC
                """))
                
                for row in result.fetchall():
                    key = f"{row[0]}_{row[1]}"
                    self.escalation_rules[key] = {
                        "escalation_level": row[2],
                        "timeout_minutes": row[3],
                        "notification_channels": row[4] or []
                    }
        except Exception as e:
            self.logger.error(f"Failed to load escalation rules: {str(e)}")

    async def _setup_notification_channels(self):
        self.notification_channels = {
            "email": {
                "enabled": True,
                "recipients": ["admin@agent47.com", "support@agent47.com"],
                "template": "alert_email_template.html"
            },
            "slack": {
                "enabled": True,
                "webhook_url": self.settings.slack.webhook_url,
                "channel": "#alerts"
            },
            "sms": {
                "enabled": False,
                "recipients": ["+1234567890"],
                "provider": "twilio"
            },
            "webhook": {
                "enabled": True,
                "url": self.settings.webhooks.alert_url,
                "method": "POST"
            }
        }

    async def create_alert(self, source: AlertSource, severity: AlertSeverity, 
                          title: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        alert_id = f"alert_{source.value}_{int(datetime.utcnow().timestamp())}"
        
        try:
            alert = Alert(
                alert_id=alert_id,
                source=source,
                severity=severity,
                title=title,
                message=message,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                acknowledged_at=None,
                resolved_at=None,
                assigned_to=None,
                metadata=metadata or {}
            )
            
            await self._save_alert(alert)
            await self._send_notifications(alert)
            await self._schedule_escalation(alert)
            
            self.active_alerts[alert_id] = alert
            
            # Broadcast alert to all admins via WebSocket
            try:
                from core.realtime.websocket_router import broadcast_alert
                await broadcast_alert({
                    "id": alert_id,
                    "source": source.value,
                    "severity": severity.value,
                    "title": title,
                    "message": message,
                    "status": AlertStatus.ACTIVE.value,
                    "created_at": alert.created_at.isoformat(),
                    "metadata": metadata or {}
                })
            except Exception as e:
                self.logger.warning(f"Failed to broadcast alert: {e}")
            
            return {
                "success": True,
                "alert_id": alert_id,
                "message": "Alert created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {str(e)}")
            return {"error": str(e)}

    async def _save_alert(self, alert: Alert):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO alerts (
                        alert_id, source, severity, title, message, status, 
                        created_at, acknowledged_at, resolved_at, assigned_to, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    alert.alert_id,
                    alert.source.value,
                    alert.severity.value,
                    alert.title,
                    alert.message,
                    alert.status.value,
                    alert.created_at,
                    alert.acknowledged_at,
                    alert.resolved_at,
                    alert.assigned_to,
                    alert.metadata
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save alert: {str(e)}")

    async def _send_notifications(self, alert: Alert):
        try:
            for channel_type, config in self.notification_channels.items():
                if not config.get("enabled", False):
                    continue
                
                if channel_type == "email":
                    await self._send_email_notification(alert, config)
                elif channel_type == "slack":
                    await self._send_slack_notification(alert, config)
                elif channel_type == "sms":
                    await self._send_sms_notification(alert, config)
                elif channel_type == "webhook":
                    await self._send_webhook_notification(alert, config)
                    
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {str(e)}")

    async def _send_email_notification(self, alert: Alert, config: Dict[str, Any]):
        try:
            for recipient in config.get("recipients", []):
                message = f"""
                Alert: {alert.title}
                Severity: {alert.severity.value.upper()}
                Source: {alert.source.value}
                Message: {alert.message}
                Time: {alert.created_at.isoformat()}
                """
                
                await self._log_notification(alert.alert_id, "email", recipient, message)
                
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")

    async def _send_slack_notification(self, alert: Alert, config: Dict[str, Any]):
        try:
            message = {
                "text": f"🚨 *{alert.severity.value.upper()} Alert*",
                "attachments": [{
                    "color": self._get_severity_color(alert.severity),
                    "fields": [
                        {"title": "Title", "value": alert.title, "short": True},
                        {"title": "Source", "value": alert.source.value, "short": True},
                        {"title": "Message", "value": alert.message, "short": False}
                    ],
                    "ts": int(alert.created_at.timestamp())
                }]
            }
            
            await self._log_notification(alert.alert_id, "slack", config.get("channel", "#alerts"), str(message))
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")

    async def _send_sms_notification(self, alert: Alert, config: Dict[str, Any]):
        try:
            message = f"ALERT: {alert.title} - {alert.message[:100]}"
            
            for recipient in config.get("recipients", []):
                await self._log_notification(alert.alert_id, "sms", recipient, message)
                
        except Exception as e:
            self.logger.error(f"Failed to send SMS notification: {str(e)}")

    async def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]):
        try:
            payload = {
                "alert_id": alert.alert_id,
                "source": alert.source.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
            
            await self._log_notification(alert.alert_id, "webhook", config.get("url", ""), str(payload))
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffa500",
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.EMERGENCY: "#8b0000"
        }
        return colors.get(severity, "#808080")

    async def _log_notification(self, alert_id: str, channel_type: str, recipient: str, message: str):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO alert_notifications (alert_id, channel_type, recipient, message)
                    VALUES (%s, %s, %s, %s)
                """), (alert_id, channel_type, recipient, message))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log notification: {str(e)}")

    async def _schedule_escalation(self, alert: Alert):
        escalation_key = f"{alert.source.value}_{alert.severity.value}"
        escalation_rule = self.escalation_rules.get(escalation_key)
        
        if escalation_rule:
            timeout_minutes = escalation_rule["timeout_minutes"]
            asyncio.create_task(self._escalate_alert(alert.alert_id, timeout_minutes))

    async def _escalate_alert(self, alert_id: str, timeout_minutes: int):
        await asyncio.sleep(timeout_minutes * 60)
        
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            if alert.status == AlertStatus.ACTIVE:
                await self._perform_escalation(alert)

    async def _perform_escalation(self, alert: Alert):
        try:
            alert.status = AlertStatus.ESCALATED
            
            if self.database:
                async with self.database.get_session() as session:
                    await session.execute(text("""
                        UPDATE alerts 
                        SET status = %s, escalation_level = escalation_level + 1, last_escalation = CURRENT_TIMESTAMP
                        WHERE alert_id = %s
                    """), (AlertStatus.ESCALATED.value, alert.alert_id))
                    await session.commit()
            
            await self._send_escalation_notifications(alert)
            
        except Exception as e:
            self.logger.error(f"Failed to perform escalation: {str(e)}")

    async def _send_escalation_notifications(self, alert: Alert):
        escalation_message = f"ALERT ESCALATED: {alert.title} - This alert has been escalated due to no response."
        
        for channel_type, config in self.notification_channels.items():
            if config.get("enabled", False) and channel_type in ["email", "slack"]:
                await self._log_notification(alert.alert_id, f"{channel_type}_escalation", 
                                           "admin", escalation_message)

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        if alert_id not in self.active_alerts:
            return False
        
        try:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.assigned_to = user
            
            if self.database:
                async with self.database.get_session() as session:
                    await session.execute(text("""
                        UPDATE alerts 
                        SET status = %s, acknowledged_at = CURRENT_TIMESTAMP, assigned_to = %s
                        WHERE alert_id = %s
                    """), (AlertStatus.ACKNOWLEDGED.value, user, alert_id))
                    await session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {str(e)}")
            return False

    async def resolve_alert(self, alert_id: str, user: str, resolution_notes: str = None) -> bool:
        if alert_id not in self.active_alerts:
            return False
        
        try:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            if resolution_notes:
                alert.metadata["resolution_notes"] = resolution_notes
            
            if self.database:
                async with self.database.get_session() as session:
                    await session.execute(text("""
                        UPDATE alerts 
                        SET status = %s, resolved_at = CURRENT_TIMESTAMP, metadata = metadata || %s
                        WHERE alert_id = %s
                    """), (AlertStatus.RESOLVED.value, 
                          {"resolution_notes": resolution_notes} if resolution_notes else {}, 
                          alert_id))
                    await session.commit()
            
            del self.active_alerts[alert_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {str(e)}")
            return False

    async def get_active_alerts(self, source: AlertSource = None, severity: AlertSeverity = None) -> List[Dict[str, Any]]:
        alerts = []
        
        for alert in self.active_alerts.values():
            if source and alert.source != source:
                continue
            if severity and alert.severity != severity:
                continue
            
            alerts.append({
                "alert_id": alert.alert_id,
                "source": alert.source.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "assigned_to": alert.assigned_to,
                "metadata": alert.metadata
            })
        
        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

    async def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT alert_id, source, severity, title, message, status, 
                           created_at, acknowledged_at, resolved_at, assigned_to, metadata
                    FROM alerts 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """), (limit,))
                
                alerts = []
                for row in result.fetchall():
                    alerts.append({
                        "alert_id": row[0],
                        "source": row[1],
                        "severity": row[2],
                        "title": row[3],
                        "message": row[4],
                        "status": row[5],
                        "created_at": row[6].isoformat(),
                        "acknowledged_at": row[7].isoformat() if row[7] else None,
                        "resolved_at": row[8].isoformat() if row[8] else None,
                        "assigned_to": row[9],
                        "metadata": row[10]
                    })
                
                return alerts
        except Exception as e:
            self.logger.error(f"Failed to get alert history: {str(e)}")
            return []

    async def get_alert_statistics(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(*) FILTER (WHERE status = 'active') as active_alerts,
                        COUNT(*) FILTER (WHERE status = 'acknowledged') as acknowledged_alerts,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
                        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
                        COUNT(*) FILTER (WHERE severity = 'emergency') as emergency_alerts,
                        AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))) as avg_resolution_time
                    FROM alerts 
                    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_alerts": row[0],
                        "active_alerts": row[1],
                        "acknowledged_alerts": row[2],
                        "resolved_alerts": row[3],
                        "critical_alerts": row[4],
                        "emergency_alerts": row[5],
                        "avg_resolution_time_seconds": row[6] or 0
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {str(e)}")
            return {}

    async def add_alert_rule(self, rule_name: str, source: AlertSource, condition_type: str,
                           condition_value: str, severity: AlertSeverity) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO alert_rules (rule_name, source, condition_type, condition_value, severity)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (rule_name) DO UPDATE SET
                        source = EXCLUDED.source,
                        condition_type = EXCLUDED.condition_type,
                        condition_value = EXCLUDED.condition_value,
                        severity = EXCLUDED.severity
                """), (rule_name, source.value, condition_type, condition_value, severity.value))
                await session.commit()
            
            await self._load_alert_rules()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add alert rule: {str(e)}")
            return False

    async def shutdown(self):
        self.logger.info("Shutting down AlertManager...")
        self.logger.info("AlertManager shutdown complete")
