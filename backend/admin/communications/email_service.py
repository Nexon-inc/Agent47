import asyncio
import smtplib
import ssl
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class EmailStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"

class EmailPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailType(Enum):
    TEXT = "text"
    HTML = "html"
    MULTIPART = "multipart"

@dataclass
class EmailMessage:
    message_id: str
    sender: str
    recipients: List[str]
    subject: str
    body: str
    email_type: EmailType
    priority: EmailPriority
    status: EmailStatus
    template_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class EmailTemplate:
    template_id: str
    name: str
    subject_template: str
    body_template: str
    email_type: EmailType
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class EmailService(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.use_tls = True
        self.use_ssl = False
        self.templates: Dict[str, EmailTemplate] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_emails_per_hour = 1000
        self.retry_attempts = 3
        self.retry_delay_seconds = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing EmailService...")
            self.database = get_database()
            await self._setup_email_tables()
            await self._load_smtp_config()
            await self._load_templates()
            self.logger.info("EmailService initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize EmailService: {str(e)}")
            return False

    async def _setup_email_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS email_messages (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) UNIQUE NOT NULL,
                    sender VARCHAR(255) NOT NULL,
                    recipients JSONB NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    email_type VARCHAR(20) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    template_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    metadata JSONB,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS email_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    subject_template TEXT NOT NULL,
                    body_template TEXT NOT NULL,
                    email_type VARCHAR(20) NOT NULL,
                    variables JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS email_attachments (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_data BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES email_messages(message_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_email_messages_sender 
                ON email_messages(sender);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_email_messages_status 
                ON email_messages(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_email_messages_created_at 
                ON email_messages(created_at);
            """)
            
            await session.commit()

    async def _load_smtp_config(self):
        self.smtp_server = self.settings.email.smtp_server
        self.smtp_port = self.settings.email.smtp_port
        self.smtp_username = self.settings.email.smtp_username
        self.smtp_password = self.settings.email.smtp_password
        self.use_tls = self.settings.email.use_tls
        self.use_ssl = self.settings.email.use_ssl
        self.max_emails_per_hour = self.settings.email.max_emails_per_hour

    async def _load_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, subject_template, body_template, 
                       email_type, variables, is_active, created_at, updated_at
                FROM email_templates
                WHERE is_active = TRUE
            """)
            
            for row in result:
                template = EmailTemplate(
                    template_id=row.template_id,
                    name=row.name,
                    subject_template=row.subject_template,
                    body_template=row.body_template,
                    email_type=EmailType(row.email_type),
                    variables=row.variables or [],
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.templates[template.template_id] = template

    async def send_email(
        self,
        sender: str,
        recipients: List[str],
        subject: str,
        body: str,
        email_type: EmailType = EmailType.HTML,
        priority: EmailPriority = EmailPriority.NORMAL,
        template_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        message_id = f"email_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(recipients)) % 10000}"
        
        email_message = EmailMessage(
            message_id=message_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            email_type=email_type,
            priority=priority,
            status=EmailStatus.PENDING,
            template_id=template_id,
            created_at=datetime.utcnow(),
            sent_at=None,
            delivered_at=None,
            metadata=metadata or {}
        )
        
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO email_messages (
                    message_id, sender, recipients, subject, body, email_type, 
                    priority, status, template_id, metadata
                ) VALUES (
                    :message_id, :sender, :recipients, :subject, :body, :email_type, 
                    :priority, :status, :template_id, :metadata
                )
            """, {
                "message_id": email_message.message_id,
                "sender": email_message.sender,
                "recipients": email_message.recipients,
                "subject": email_message.subject,
                "body": email_message.body,
                "email_type": email_message.email_type.value,
                "priority": email_message.priority.value,
                "status": email_message.status.value,
                "template_id": email_message.template_id,
                "metadata": email_message.metadata
            })
            
            if attachments:
                for attachment in attachments:
                    await session.execute("""
                        INSERT INTO email_attachments (
                            message_id, filename, content_type, file_size, file_data
                        ) VALUES (
                            :message_id, :filename, :content_type, :file_size, :file_data
                        )
                    """, {
                        "message_id": message_id,
                        "filename": attachment.get("filename", ""),
                        "content_type": attachment.get("content_type", "application/octet-stream"),
                        "file_size": len(attachment.get("data", b"")),
                        "file_data": attachment.get("data", b"")
                    })
            
            await session.commit()
        
        await self._send_email_message(email_message, attachments)
        return message_id

    async def _send_email_message(self, email_message: EmailMessage, attachments: Optional[List[Dict[str, Any]]] = None):
        try:
            if not self._check_rate_limit(email_message.sender):
                self.logger.warning(f"Rate limit exceeded for sender: {email_message.sender}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = email_message.sender
            msg['To'] = ', '.join(email_message.recipients)
            msg['Subject'] = email_message.subject
            
            if email_message.email_type == EmailType.HTML:
                msg.attach(MIMEText(email_message.body, 'html'))
            else:
                msg.attach(MIMEText(email_message.body, 'plain'))
            
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.get("data", b""))
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.get("filename", "attachment")}'
                    )
                    msg.attach(part)
            
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls and not self.use_ssl:
                server.starttls()
            
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            await self._update_email_status(email_message.message_id, EmailStatus.SENT)
            self.logger.info(f"Email sent successfully: {email_message.message_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email {email_message.message_id}: {str(e)}")
            await self._handle_email_failure(email_message.message_id, str(e))

    def _check_rate_limit(self, sender: str) -> bool:
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        if sender not in self.rate_limits:
            self.rate_limits[sender] = []
        
        self.rate_limits[sender] = [
            timestamp for timestamp in self.rate_limits[sender]
            if timestamp > hour_ago
        ]
        
        if len(self.rate_limits[sender]) >= self.max_emails_per_hour:
            return False
        
        self.rate_limits[sender].append(now)
        return True

    async def _update_email_status(
        self, 
        message_id: str, 
        status: EmailStatus,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        if not self.database:
            return
        
        update_fields = ["status = :status"]
        params = {"message_id": message_id, "status": status.value}
        
        if status == EmailStatus.SENT:
            update_fields.append("sent_at = :sent_at")
            params["sent_at"] = datetime.utcnow()
        elif status == EmailStatus.DELIVERED:
            update_fields.append("delivered_at = :delivered_at")
            params["delivered_at"] = datetime.utcnow()
        
        if additional_data:
            for key, value in additional_data.items():
                update_fields.append(f"{key} = :{key}")
                params[key] = value
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE email_messages 
                SET {', '.join(update_fields)}
                WHERE message_id = :message_id
            """, params)
            await session.commit()

    async def _handle_email_failure(self, message_id: str, error_message: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT retry_count FROM email_messages 
                WHERE message_id = :message_id
            """, {"message_id": message_id})
            
            row = result.fetchone()
            if not row:
                return
            
            retry_count = row.retry_count or 0
            
            if retry_count < self.retry_attempts:
                await session.execute("""
                    UPDATE email_messages 
                    SET retry_count = :retry_count, error_message = :error_message
                    WHERE message_id = :message_id
                """, {
                    "message_id": message_id,
                    "retry_count": retry_count + 1,
                    "error_message": error_message
                })
                
                await asyncio.sleep(self.retry_delay_seconds)
                await self._retry_email(message_id)
            else:
                await session.execute("""
                    UPDATE email_messages 
                    SET status = :status, error_message = :error_message
                    WHERE message_id = :message_id
                """, {
                    "message_id": message_id,
                    "status": EmailStatus.FAILED.value,
                    "error_message": error_message
                })
            
            await session.commit()

    async def _retry_email(self, message_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT message_id, sender, recipients, subject, body, email_type, 
                       priority, template_id, metadata
                FROM email_messages 
                WHERE message_id = :message_id
            """, {"message_id": message_id})
            
            row = result.fetchone()
            if not row:
                return
            
            email_message = EmailMessage(
                message_id=row.message_id,
                sender=row.sender,
                recipients=row.recipients,
                subject=row.subject,
                body=row.body,
                email_type=EmailType(row.email_type),
                priority=EmailPriority(row.priority),
                status=EmailStatus.PENDING,
                template_id=row.template_id,
                created_at=datetime.utcnow(),
                sent_at=None,
                delivered_at=None,
                metadata=row.metadata or {}
            )
            
            await self._send_email_message(email_message)

    async def create_template(
        self,
        template_id: str,
        name: str,
        subject_template: str,
        body_template: str,
        email_type: EmailType = EmailType.HTML,
        variables: Optional[List[str]] = None
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO email_templates (
                        template_id, name, subject_template, body_template, 
                        email_type, variables, is_active
                    ) VALUES (
                        :template_id, :name, :subject_template, :body_template, 
                        :email_type, :variables, TRUE
                    )
                """, {
                    "template_id": template_id,
                    "name": name,
                    "subject_template": subject_template,
                    "body_template": body_template,
                    "email_type": email_type.value,
                    "variables": variables or []
                })
                await session.commit()
            
            await self._load_templates()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create email template: {str(e)}")
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
            self.logger.error(f"Failed to render email template: {str(e)}")
            return None

    async def send_template_email(
        self,
        template_id: str,
        sender: str,
        recipients: List[str],
        variables: Dict[str, Any],
        priority: EmailPriority = EmailPriority.NORMAL,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        rendered = await self.render_template(template_id, variables)
        if not rendered:
            return None
        
        return await self.send_email(
            sender=sender,
            recipients=recipients,
            subject=rendered["subject"],
            body=rendered["body"],
            email_type=self.templates[template_id].email_type,
            priority=priority,
            template_id=template_id,
            attachments=attachments,
            metadata={"template_variables": variables}
        )

    async def get_email_messages(
        self,
        sender: Optional[str] = None,
        status: Optional[EmailStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EmailMessage]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if sender:
            conditions.append("sender = :sender")
            params["sender"] = sender
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT message_id, sender, recipients, subject, body, email_type, 
                       priority, status, template_id, created_at, sent_at, delivered_at, metadata
                FROM email_messages
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            messages = []
            for row in result:
                message = EmailMessage(
                    message_id=row.message_id,
                    sender=row.sender,
                    recipients=row.recipients,
                    subject=row.subject,
                    body=row.body,
                    email_type=EmailType(row.email_type),
                    priority=EmailPriority(row.priority),
                    status=EmailStatus(row.status),
                    template_id=row.template_id,
                    created_at=row.created_at,
                    sent_at=row.sent_at,
                    delivered_at=row.delivered_at,
                    metadata=row.metadata or {}
                )
                messages.append(message)
            
            return messages

    async def get_email_stats(
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
                    COUNT(CASE WHEN status = 'bounced' THEN 1 END) as bounced,
                    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN email_type = 'html' THEN 1 END) as html,
                    COUNT(CASE WHEN email_type = 'text' THEN 1 END) as text
                FROM email_messages
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
                "bounced": row.bounced,
                "urgent": row.urgent,
                "high": row.high,
                "html": row.html,
                "text": row.text,
                "delivery_rate": (row.delivered / row.total * 100) if row.total > 0 else 0,
                "failure_rate": (row.failed / row.total * 100) if row.total > 0 else 0
            }

    async def mark_email_delivered(self, message_id: str) -> bool:
        try:
            await self._update_email_status(message_id, EmailStatus.DELIVERED)
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark email as delivered: {str(e)}")
            return False

    async def mark_email_opened(self, message_id: str) -> bool:
        try:
            await self._update_email_status(message_id, EmailStatus.OPENED)
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark email as opened: {str(e)}")
            return False

    async def mark_email_clicked(self, message_id: str) -> bool:
        try:
            await self._update_email_status(message_id, EmailStatus.CLICKED)
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark email as clicked: {str(e)}")
            return False

_email_service: Optional[EmailService] = None

async def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
        await _email_service.initialize()
    return _email_service

async def init_email_service() -> EmailService:
    return await get_email_service()
