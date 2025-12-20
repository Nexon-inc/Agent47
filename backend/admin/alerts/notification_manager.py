import asyncio
import smtplib
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class Notification:
    notification_id: str
    type: NotificationType
    recipient: str
    subject: str
    message: str
    priority: NotificationPriority
    status: NotificationStatus
    template_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class NotificationTemplate:
    template_id: str
    name: str
    type: NotificationType
    subject_template: str
    body_template: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class NotificationManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.templates: Dict[str, NotificationTemplate] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_notifications_per_minute = 100
        self.retry_attempts = 3
        self.retry_delay_seconds = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing NotificationManager...")
            self.database = get_database()
            await self._setup_notification_tables()
            await self._load_templates()
            self.logger.info("NotificationManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize NotificationManager: {str(e)}")
            return False

    async def _setup_notification_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    notification_id VARCHAR(255) UNIQUE NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    recipient VARCHAR(255) NOT NULL,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    template_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    read_at TIMESTAMP,
                    metadata JSONB,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS notification_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    subject_template TEXT NOT NULL,
                    body_template TEXT NOT NULL,
                    variables JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_recipient 
                ON notifications(recipient);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_status 
                ON notifications(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
                ON notifications(created_at);
            """)
            
            await session.commit()

    async def _load_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, type, subject_template, body_template, 
                       variables, is_active, created_at, updated_at
                FROM notification_templates
                WHERE is_active = TRUE
            """)
            
            for row in result:
                template = NotificationTemplate(
                    template_id=row.template_id,
                    name=row.name,
                    type=NotificationType(row.type),
                    subject_template=row.subject_template,
                    body_template=row.body_template,
                    variables=row.variables or [],
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.templates[template.template_id] = template

    async def create_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(recipient) % 10000}"
        
        notification = Notification(
            notification_id=notification_id,
            type=notification_type,
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority,
            status=NotificationStatus.PENDING,
            template_id=template_id,
            created_at=datetime.utcnow(),
            sent_at=None,
            delivered_at=None,
            read_at=None,
            metadata=metadata or {}
        )
        
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO notifications (
                    notification_id, type, recipient, subject, message, priority, 
                    status, template_id, metadata
                ) VALUES (
                    :notification_id, :type, :recipient, :subject, :message, 
                    :priority, :status, :template_id, :metadata
                )
            """, {
                "notification_id": notification.notification_id,
                "type": notification.type.value,
                "recipient": notification.recipient,
                "subject": notification.subject,
                "message": notification.message,
                "priority": notification.priority.value,
                "status": notification.status.value,
                "template_id": notification.template_id,
                "metadata": notification.metadata
            })
            await session.commit()
        
        await self._send_notification(notification)
        return notification_id

    async def _send_notification(self, notification: Notification):
        try:
            if not self._check_rate_limit(notification.recipient):
                self.logger.warning(f"Rate limit exceeded for recipient: {notification.recipient}")
                return
            
            if notification.type == NotificationType.EMAIL:
                await self._send_email(notification)
            elif notification.type == NotificationType.SMS:
                await self._send_sms(notification)
            elif notification.type == NotificationType.PUSH:
                await self._send_push(notification)
            elif notification.type == NotificationType.WEBHOOK:
                await self._send_webhook(notification)
            elif notification.type == NotificationType.SLACK:
                await self._send_slack(notification)
            elif notification.type == NotificationType.DISCORD:
                await self._send_discord(notification)
            elif notification.type == NotificationType.TEAMS:
                await self._send_teams(notification)
            
            await self._update_notification_status(notification.notification_id, NotificationStatus.SENT)
            
        except Exception as e:
            self.logger.error(f"Failed to send notification {notification.notification_id}: {str(e)}")
            await self._handle_notification_failure(notification.notification_id, str(e))

    async def _send_email(self, notification: Notification):
        try:
            smtp_server = self.settings.notifications.smtp_server
            smtp_port = self.settings.notifications.smtp_port
            smtp_username = self.settings.notifications.smtp_username
            smtp_password = self.settings.notifications.smtp_password
            
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = notification.recipient
            msg['Subject'] = notification.subject
            
            msg.attach(MIMEText(notification.message, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {notification.recipient}")
            
        except Exception as e:
            raise Exception(f"Email sending failed: {str(e)}")

    async def _send_sms(self, notification: Notification):
        try:
            api_key = self.settings.notifications.sms_api_key
            api_url = self.settings.notifications.sms_api_url
            
            payload = {
                "to": notification.recipient,
                "message": notification.message,
                "from": self.settings.notifications.sms_sender_id
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"SMS sent successfully to {notification.recipient}")
            
        except Exception as e:
            raise Exception(f"SMS sending failed: {str(e)}")

    async def _send_push(self, notification: Notification):
        try:
            fcm_server_key = self.settings.notifications.fcm_server_key
            
            payload = {
                "to": notification.recipient,
                "notification": {
                    "title": notification.subject,
                    "body": notification.message
                },
                "data": notification.metadata
            }
            
            headers = {
                "Authorization": f"key={fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            self.logger.info(f"Push notification sent successfully to {notification.recipient}")
            
        except Exception as e:
            raise Exception(f"Push notification sending failed: {str(e)}")

    async def _send_webhook(self, notification: Notification):
        try:
            webhook_url = notification.metadata.get("webhook_url")
            if not webhook_url:
                raise ValueError("Webhook URL not provided in metadata")
            
            payload = {
                "subject": notification.subject,
                "message": notification.message,
                "priority": notification.priority.value,
                "timestamp": notification.created_at.isoformat(),
                "metadata": notification.metadata
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Webhook notification sent successfully to {webhook_url}")
            
        except Exception as e:
            raise Exception(f"Webhook notification sending failed: {str(e)}")

    async def _send_slack(self, notification: Notification):
        try:
            webhook_url = self.settings.notifications.slack_webhook_url
            
            payload = {
                "text": f"*{notification.subject}*",
                "attachments": [
                    {
                        "color": self._get_priority_color(notification.priority),
                        "text": notification.message,
                        "footer": "Agent47 Admin",
                        "ts": int(notification.created_at.timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Slack notification sent successfully")
            
        except Exception as e:
            raise Exception(f"Slack notification sending failed: {str(e)}")

    async def _send_discord(self, notification: Notification):
        try:
            webhook_url = self.settings.notifications.discord_webhook_url
            
            payload = {
                "embeds": [
                    {
                        "title": notification.subject,
                        "description": notification.message,
                        "color": self._get_priority_color(notification.priority),
                        "timestamp": notification.created_at.isoformat(),
                        "footer": {
                            "text": "Agent47 Admin"
                        }
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Discord notification sent successfully")
            
        except Exception as e:
            raise Exception(f"Discord notification sending failed: {str(e)}")

    async def _send_teams(self, notification: Notification):
        try:
            webhook_url = self.settings.notifications.teams_webhook_url
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_priority_color(notification.priority),
                "summary": notification.subject,
                "sections": [
                    {
                        "activityTitle": notification.subject,
                        "activitySubtitle": "Agent47 Admin",
                        "activityImage": "",
                        "text": notification.message,
                        "facts": [
                            {
                                "name": "Priority",
                                "value": notification.priority.value.title()
                            },
                            {
                                "name": "Time",
                                "value": notification.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.logger.info(f"Teams notification sent successfully")
            
        except Exception as e:
            raise Exception(f"Teams notification sending failed: {str(e)}")

    def _get_priority_color(self, priority: NotificationPriority) -> int:
        color_map = {
            NotificationPriority.LOW: 0x00ff00,
            NotificationPriority.MEDIUM: 0xffff00,
            NotificationPriority.HIGH: 0xff8800,
            NotificationPriority.URGENT: 0xff0000
        }
        return color_map.get(priority, 0x0000ff)

    def _check_rate_limit(self, recipient: str) -> bool:
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        if recipient not in self.rate_limits:
            self.rate_limits[recipient] = []
        
        self.rate_limits[recipient] = [
            timestamp for timestamp in self.rate_limits[recipient]
            if timestamp > minute_ago
        ]
        
        if len(self.rate_limits[recipient]) >= self.max_notifications_per_minute:
            return False
        
        self.rate_limits[recipient].append(now)
        return True

    async def _update_notification_status(
        self, 
        notification_id: str, 
        status: NotificationStatus,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        if not self.database:
            return
        
        update_fields = ["status = :status"]
        params = {"notification_id": notification_id, "status": status.value}
        
        if status == NotificationStatus.SENT:
            update_fields.append("sent_at = :sent_at")
            params["sent_at"] = datetime.utcnow()
        elif status == NotificationStatus.DELIVERED:
            update_fields.append("delivered_at = :delivered_at")
            params["delivered_at"] = datetime.utcnow()
        elif status == NotificationStatus.READ:
            update_fields.append("read_at = :read_at")
            params["read_at"] = datetime.utcnow()
        
        if additional_data:
            for key, value in additional_data.items():
                update_fields.append(f"{key} = :{key}")
                params[key] = value
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE notifications 
                SET {', '.join(update_fields)}
                WHERE notification_id = :notification_id
            """, params)
            await session.commit()

    async def _handle_notification_failure(self, notification_id: str, error_message: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT retry_count FROM notifications 
                WHERE notification_id = :notification_id
            """, {"notification_id": notification_id})
            
            row = result.fetchone()
            if not row:
                return
            
            retry_count = row.retry_count or 0
            
            if retry_count < self.retry_attempts:
                await session.execute("""
                    UPDATE notifications 
                    SET retry_count = :retry_count, error_message = :error_message
                    WHERE notification_id = :notification_id
                """, {
                    "notification_id": notification_id,
                    "retry_count": retry_count + 1,
                    "error_message": error_message
                })
                
                await asyncio.sleep(self.retry_delay_seconds)
                await self._retry_notification(notification_id)
            else:
                await session.execute("""
                    UPDATE notifications 
                    SET status = :status, error_message = :error_message
                    WHERE notification_id = :notification_id
                """, {
                    "notification_id": notification_id,
                    "status": NotificationStatus.FAILED.value,
                    "error_message": error_message
                })
            
            await session.commit()

    async def _retry_notification(self, notification_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT notification_id, type, recipient, subject, message, 
                       priority, template_id, metadata
                FROM notifications 
                WHERE notification_id = :notification_id
            """, {"notification_id": notification_id})
            
            row = result.fetchone()
            if not row:
                return
            
            notification = Notification(
                notification_id=row.notification_id,
                type=NotificationType(row.type),
                recipient=row.recipient,
                subject=row.subject,
                message=row.message,
                priority=NotificationPriority(row.priority),
                status=NotificationStatus.PENDING,
                template_id=row.template_id,
                created_at=datetime.utcnow(),
                sent_at=None,
                delivered_at=None,
                read_at=None,
                metadata=row.metadata or {}
            )
            
            await self._send_notification(notification)

    async def get_notifications(
        self,
        recipient: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Notification]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if recipient:
            conditions.append("recipient = :recipient")
            params["recipient"] = recipient
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if notification_type:
            conditions.append("type = :type")
            params["type"] = notification_type.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT notification_id, type, recipient, subject, message, 
                       priority, status, template_id, created_at, sent_at, 
                       delivered_at, read_at, metadata
                FROM notifications
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            notifications = []
            for row in result:
                notification = Notification(
                    notification_id=row.notification_id,
                    type=NotificationType(row.type),
                    recipient=row.recipient,
                    subject=row.subject,
                    message=row.message,
                    priority=NotificationPriority(row.priority),
                    status=NotificationStatus(row.status),
                    template_id=row.template_id,
                    created_at=row.created_at,
                    sent_at=row.sent_at,
                    delivered_at=row.delivered_at,
                    read_at=row.read_at,
                    metadata=row.metadata or {}
                )
                notifications.append(notification)
            
            return notifications

    async def mark_notification_read(self, notification_id: str) -> bool:
        try:
            await self._update_notification_status(notification_id, NotificationStatus.READ)
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    async def create_template(
        self,
        template_id: str,
        name: str,
        notification_type: NotificationType,
        subject_template: str,
        body_template: str,
        variables: List[str]
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO notification_templates (
                        template_id, name, type, subject_template, body_template, 
                        variables, is_active
                    ) VALUES (
                        :template_id, :name, :type, :subject_template, :body_template, 
                        :variables, TRUE
                    )
                """, {
                    "template_id": template_id,
                    "name": name,
                    "type": notification_type.value,
                    "subject_template": subject_template,
                    "body_template": body_template,
                    "variables": variables
                })
                await session.commit()
            
            await self._load_templates()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {str(e)}")
            return False

    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        
        try:
            subject = template.subject_template
            body = template.body_template
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                subject = subject.replace(placeholder, str(var_value))
                body = body.replace(placeholder, str(var_value))
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            self.logger.error(f"Failed to render template: {str(e)}")
            return None

    async def get_notification_stats(
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
                    COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'read' THEN 1 END) as read,
                    COUNT(CASE WHEN type = 'email' THEN 1 END) as email,
                    COUNT(CASE WHEN type = 'sms' THEN 1 END) as sms,
                    COUNT(CASE WHEN type = 'push' THEN 1 END) as push
                FROM notifications
                WHERE created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total": row.total,
                "sent": row.sent,
                "delivered": row.delivered,
                "failed": row.failed,
                "read": row.read,
                "email": row.email,
                "sms": row.sms,
                "push": row.push,
                "delivery_rate": (row.delivered / row.total * 100) if row.total > 0 else 0,
                "read_rate": (row.read / row.delivered * 100) if row.delivered > 0 else 0
            }

_notification_manager: Optional[NotificationManager] = None

async def get_notification_manager() -> NotificationManager:
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
        await _notification_manager.initialize()
    return _notification_manager

async def init_notification_manager() -> NotificationManager:
    return await get_notification_manager()
