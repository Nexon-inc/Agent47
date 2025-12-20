import asyncio
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class SMSStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"

class SMSPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class SMSProvider(Enum):
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"
    NEXMO = "nexmo"
    CUSTOM = "custom"

@dataclass
class SMSMessage:
    message_id: str
    sender: str
    recipient: str
    message: str
    priority: SMSPriority
    status: SMSStatus
    provider: SMSProvider
    template_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cost: Optional[float]
    metadata: Dict[str, Any]

@dataclass
class SMSTemplate:
    template_id: str
    name: str
    message_template: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class SMSService(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.providers: Dict[SMSProvider, Dict[str, Any]] = {}
        self.templates: Dict[str, SMSTemplate] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_sms_per_hour = 500
        self.retry_attempts = 3
        self.retry_delay_seconds = 30

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SMSService...")
            self.database = get_database()
            await self._setup_sms_tables()
            await self._load_provider_configs()
            await self._load_templates()
            self.logger.info("SMSService initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize SMSService: {str(e)}")
            return False

    async def _setup_sms_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS sms_messages (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) UNIQUE NOT NULL,
                    sender VARCHAR(20) NOT NULL,
                    recipient VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    provider VARCHAR(20) NOT NULL,
                    template_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    cost DECIMAL(10,4),
                    metadata JSONB,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS sms_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    message_template TEXT NOT NULL,
                    variables JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_sms_messages_recipient 
                ON sms_messages(recipient);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_sms_messages_status 
                ON sms_messages(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_sms_messages_created_at 
                ON sms_messages(created_at);
            """)
            
            await session.commit()

    async def _load_provider_configs(self):
        self.providers[SMSProvider.TWILIO] = {
            "account_sid": self.settings.sms.twilio_account_sid,
            "auth_token": self.settings.sms.twilio_auth_token,
            "from_number": self.settings.sms.twilio_from_number,
            "api_url": "https://api.twilio.com/2010-04-01/Accounts"
        }
        
        self.providers[SMSProvider.AWS_SNS] = {
            "access_key": self.settings.sms.aws_access_key,
            "secret_key": self.settings.sms.aws_secret_key,
            "region": self.settings.sms.aws_region,
            "api_url": "https://sns.amazonaws.com"
        }
        
        self.providers[SMSProvider.NEXMO] = {
            "api_key": self.settings.sms.nexmo_api_key,
            "api_secret": self.settings.sms.nexmo_api_secret,
            "from_number": self.settings.sms.nexmo_from_number,
            "api_url": "https://rest.nexmo.com/sms/json"
        }
        
        self.providers[SMSProvider.CUSTOM] = {
            "api_url": self.settings.sms.custom_api_url,
            "api_key": self.settings.sms.custom_api_key,
            "from_number": self.settings.sms.custom_from_number
        }

    async def _load_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, message_template, variables, 
                       is_active, created_at, updated_at
                FROM sms_templates
                WHERE is_active = TRUE
            """)
            
            for row in result:
                template = SMSTemplate(
                    template_id=row.template_id,
                    name=row.name,
                    message_template=row.message_template,
                    variables=row.variables or [],
                    is_active=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                self.templates[template.template_id] = template

    async def send_sms(
        self,
        sender: str,
        recipient: str,
        message: str,
        priority: SMSPriority = SMSPriority.NORMAL,
        provider: SMSProvider = SMSProvider.TWILIO,
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        message_id = f"sms_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(recipient) % 10000}"
        
        sms_message = SMSMessage(
            message_id=message_id,
            sender=sender,
            recipient=recipient,
            message=message,
            priority=priority,
            status=SMSStatus.PENDING,
            provider=provider,
            template_id=template_id,
            created_at=datetime.utcnow(),
            sent_at=None,
            delivered_at=None,
            cost=None,
            metadata=metadata or {}
        )
        
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO sms_messages (
                    message_id, sender, recipient, message, priority, status, 
                    provider, template_id, metadata
                ) VALUES (
                    :message_id, :sender, :recipient, :message, :priority, :status, 
                    :provider, :template_id, :metadata
                )
            """, {
                "message_id": sms_message.message_id,
                "sender": sms_message.sender,
                "recipient": sms_message.recipient,
                "message": sms_message.message,
                "priority": sms_message.priority.value,
                "status": sms_message.status.value,
                "provider": sms_message.provider.value,
                "template_id": sms_message.template_id,
                "metadata": sms_message.metadata
            })
            await session.commit()
        
        await self._send_sms_message(sms_message)
        return message_id

    async def _send_sms_message(self, sms_message: SMSMessage):
        try:
            if not self._check_rate_limit(sms_message.sender):
                self.logger.warning(f"Rate limit exceeded for sender: {sms_message.sender}")
                return
            
            if sms_message.provider == SMSProvider.TWILIO:
                await self._send_via_twilio(sms_message)
            elif sms_message.provider == SMSProvider.AWS_SNS:
                await self._send_via_aws_sns(sms_message)
            elif sms_message.provider == SMSProvider.NEXMO:
                await self._send_via_nexmo(sms_message)
            elif sms_message.provider == SMSProvider.CUSTOM:
                await self._send_via_custom(sms_message)
            
            await self._update_sms_status(sms_message.message_id, SMSStatus.SENT)
            self.logger.info(f"SMS sent successfully: {sms_message.message_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS {sms_message.message_id}: {str(e)}")
            await self._handle_sms_failure(sms_message.message_id, str(e))

    async def _send_via_twilio(self, sms_message: SMSMessage):
        config = self.providers[SMSProvider.TWILIO]
        
        url = f"{config['api_url']}/{config['account_sid']}/Messages.json"
        
        data = {
            "From": config['from_number'],
            "To": sms_message.recipient,
            "Body": sms_message.message
        }
        
        response = requests.post(
            url,
            data=data,
            auth=(config['account_sid'], config['auth_token']),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        cost = float(result.get('price', 0))
        
        await self._update_sms_status(
            sms_message.message_id, 
            SMSStatus.SENT, 
            {"cost": cost, "twilio_sid": result.get('sid')}
        )

    async def _send_via_aws_sns(self, sms_message: SMSMessage):
        import boto3
        
        config = self.providers[SMSProvider.AWS_SNS]
        
        sns_client = boto3.client(
            'sns',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            region_name=config['region']
        )
        
        response = sns_client.publish(
            PhoneNumber=sms_message.recipient,
            Message=sms_message.message,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        
        await self._update_sms_status(
            sms_message.message_id, 
            SMSStatus.SENT, 
            {"aws_message_id": response.get('MessageId')}
        )

    async def _send_via_nexmo(self, sms_message: SMSMessage):
        config = self.providers[SMSProvider.NEXMO]
        
        data = {
            "api_key": config['api_key'],
            "api_secret": config['api_secret'],
            "from": config['from_number'],
            "to": sms_message.recipient,
            "text": sms_message.message
        }
        
        response = requests.post(
            config['api_url'],
            data=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('messages', [{}])[0].get('status') == '0':
            await self._update_sms_status(
                sms_message.message_id, 
                SMSStatus.SENT, 
                {"nexmo_message_id": result.get('messages', [{}])[0].get('message-id')}
            )
        else:
            error_text = result.get('messages', [{}])[0].get('error-text', 'Unknown error')
            raise Exception(f"Nexmo error: {error_text}")

    async def _send_via_custom(self, sms_message: SMSMessage):
        config = self.providers[SMSProvider.CUSTOM]
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": config['from_number'],
            "to": sms_message.recipient,
            "message": sms_message.message
        }
        
        response = requests.post(
            config['api_url'],
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        await self._update_sms_status(
            sms_message.message_id, 
            SMSStatus.SENT, 
            {"custom_response": result}
        )

    def _check_rate_limit(self, sender: str) -> bool:
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        if sender not in self.rate_limits:
            self.rate_limits[sender] = []
        
        self.rate_limits[sender] = [
            timestamp for timestamp in self.rate_limits[sender]
            if timestamp > hour_ago
        ]
        
        if len(self.rate_limits[sender]) >= self.max_sms_per_hour:
            return False
        
        self.rate_limits[sender].append(now)
        return True

    async def _update_sms_status(
        self, 
        message_id: str, 
        status: SMSStatus,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        if not self.database:
            return
        
        update_fields = ["status = :status"]
        params = {"message_id": message_id, "status": status.value}
        
        if status == SMSStatus.SENT:
            update_fields.append("sent_at = :sent_at")
            params["sent_at"] = datetime.utcnow()
        elif status == SMSStatus.DELIVERED:
            update_fields.append("delivered_at = :delivered_at")
            params["delivered_at"] = datetime.utcnow()
        
        if additional_data:
            for key, value in additional_data.items():
                update_fields.append(f"{key} = :{key}")
                params[key] = value
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE sms_messages 
                SET {', '.join(update_fields)}
                WHERE message_id = :message_id
            """, params)
            await session.commit()

    async def _handle_sms_failure(self, message_id: str, error_message: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT retry_count FROM sms_messages 
                WHERE message_id = :message_id
            """, {"message_id": message_id})
            
            row = result.fetchone()
            if not row:
                return
            
            retry_count = row.retry_count or 0
            
            if retry_count < self.retry_attempts:
                await session.execute("""
                    UPDATE sms_messages 
                    SET retry_count = :retry_count, error_message = :error_message
                    WHERE message_id = :message_id
                """, {
                    "message_id": message_id,
                    "retry_count": retry_count + 1,
                    "error_message": error_message
                })
                
                await asyncio.sleep(self.retry_delay_seconds)
                await self._retry_sms(message_id)
            else:
                await session.execute("""
                    UPDATE sms_messages 
                    SET status = :status, error_message = :error_message
                    WHERE message_id = :message_id
                """, {
                    "message_id": message_id,
                    "status": SMSStatus.FAILED.value,
                    "error_message": error_message
                })
            
            await session.commit()

    async def _retry_sms(self, message_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT message_id, sender, recipient, message, priority, 
                       provider, template_id, metadata
                FROM sms_messages 
                WHERE message_id = :message_id
            """, {"message_id": message_id})
            
            row = result.fetchone()
            if not row:
                return
            
            sms_message = SMSMessage(
                message_id=row.message_id,
                sender=row.sender,
                recipient=row.recipient,
                message=row.message,
                priority=SMSPriority(row.priority),
                status=SMSStatus.PENDING,
                provider=SMSProvider(row.provider),
                template_id=row.template_id,
                created_at=datetime.utcnow(),
                sent_at=None,
                delivered_at=None,
                cost=None,
                metadata=row.metadata or {}
            )
            
            await self._send_sms_message(sms_message)

    async def create_template(
        self,
        template_id: str,
        name: str,
        message_template: str,
        variables: Optional[List[str]] = None
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO sms_templates (
                        template_id, name, message_template, variables, is_active
                    ) VALUES (
                        :template_id, :name, :message_template, :variables, TRUE
                    )
                """, {
                    "template_id": template_id,
                    "name": name,
                    "message_template": message_template,
                    "variables": variables or []
                })
                await session.commit()
            
            await self._load_templates()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create SMS template: {str(e)}")
            return False

    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        
        try:
            message = template.message_template
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                message = message.replace(placeholder, str(var_value))
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to render SMS template: {str(e)}")
            return None

    async def send_template_sms(
        self,
        template_id: str,
        sender: str,
        recipient: str,
        variables: Dict[str, Any],
        priority: SMSPriority = SMSPriority.NORMAL,
        provider: SMSProvider = SMSProvider.TWILIO
    ) -> Optional[str]:
        rendered = await self.render_template(template_id, variables)
        if not rendered:
            return None
        
        return await self.send_sms(
            sender=sender,
            recipient=recipient,
            message=rendered,
            priority=priority,
            provider=provider,
            template_id=template_id,
            metadata={"template_variables": variables}
        )

    async def get_sms_messages(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        status: Optional[SMSStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SMSMessage]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if sender:
            conditions.append("sender = :sender")
            params["sender"] = sender
        
        if recipient:
            conditions.append("recipient = :recipient")
            params["recipient"] = recipient
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT message_id, sender, recipient, message, priority, status, 
                       provider, template_id, created_at, sent_at, delivered_at, cost, metadata
                FROM sms_messages
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            messages = []
            for row in result:
                message = SMSMessage(
                    message_id=row.message_id,
                    sender=row.sender,
                    recipient=row.recipient,
                    message=row.message,
                    priority=SMSPriority(row.priority),
                    status=SMSStatus(row.status),
                    provider=SMSProvider(row.provider),
                    template_id=row.template_id,
                    created_at=row.created_at,
                    sent_at=row.sent_at,
                    delivered_at=row.delivered_at,
                    cost=float(row.cost) if row.cost else None,
                    metadata=row.metadata or {}
                )
                messages.append(message)
            
            return messages

    async def get_sms_stats(
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
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN provider = 'twilio' THEN 1 END) as twilio,
                    COUNT(CASE WHEN provider = 'aws_sns' THEN 1 END) as aws_sns,
                    COUNT(CASE WHEN provider = 'nexmo' THEN 1 END) as nexmo,
                    SUM(cost) as total_cost
                FROM sms_messages
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
                "rejected": row.rejected,
                "urgent": row.urgent,
                "high": row.high,
                "twilio": row.twilio,
                "aws_sns": row.aws_sns,
                "nexmo": row.nexmo,
                "total_cost": float(row.total_cost) if row.total_cost else 0.0,
                "delivery_rate": (row.delivered / row.total * 100) if row.total > 0 else 0,
                "failure_rate": (row.failed / row.total * 100) if row.total > 0 else 0
            }

    async def mark_sms_delivered(self, message_id: str) -> bool:
        try:
            await self._update_sms_status(message_id, SMSStatus.DELIVERED)
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark SMS as delivered: {str(e)}")
            return False

    async def handle_webhook(self, provider: SMSProvider, webhook_data: Dict[str, Any]) -> bool:
        try:
            if provider == SMSProvider.TWILIO:
                return await self._handle_twilio_webhook(webhook_data)
            elif provider == SMSProvider.AWS_SNS:
                return await self._handle_aws_sns_webhook(webhook_data)
            elif provider == SMSProvider.NEXMO:
                return await self._handle_nexmo_webhook(webhook_data)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle webhook: {str(e)}")
            return False

    async def _handle_twilio_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        message_sid = webhook_data.get('MessageSid')
        message_status = webhook_data.get('MessageStatus')
        
        if not message_sid:
            return False
        
        if message_status == 'delivered':
            await self._update_sms_status_by_external_id(
                message_sid, SMSStatus.DELIVERED, "twilio_sid"
            )
        elif message_status == 'failed':
            await self._update_sms_status_by_external_id(
                message_sid, SMSStatus.FAILED, "twilio_sid"
            )
        
        return True

    async def _handle_aws_sns_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        message_id = webhook_data.get('MessageId')
        delivery_status = webhook_data.get('deliveryStatus')
        
        if not message_id:
            return False
        
        if delivery_status == 'SUCCESS':
            await self._update_sms_status_by_external_id(
                message_id, SMSStatus.DELIVERED, "aws_message_id"
            )
        elif delivery_status == 'FAILURE':
            await self._update_sms_status_by_external_id(
                message_id, SMSStatus.FAILED, "aws_message_id"
            )
        
        return True

    async def _handle_nexmo_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        message_id = webhook_data.get('messageId')
        status = webhook_data.get('status')
        
        if not message_id:
            return False
        
        if status == 'delivered':
            await self._update_sms_status_by_external_id(
                message_id, SMSStatus.DELIVERED, "nexmo_message_id"
            )
        elif status == 'failed':
            await self._update_sms_status_by_external_id(
                message_id, SMSStatus.FAILED, "nexmo_message_id"
            )
        
        return True

    async def _update_sms_status_by_external_id(
        self, 
        external_id: str, 
        status: SMSStatus, 
        external_id_field: str
    ):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(f"""
                UPDATE sms_messages 
                SET status = :status, delivered_at = :delivered_at
                WHERE metadata->>:external_id_field = :external_id
            """, {
                "status": status.value,
                "delivered_at": datetime.utcnow() if status == SMSStatus.DELIVERED else None,
                "external_id_field": external_id_field,
                "external_id": external_id
            })
            await session.commit()

_sms_service: Optional[SMSService] = None

async def get_sms_service() -> SMSService:
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
        await _sms_service.initialize()
    return _sms_service

async def init_sms_service() -> SMSService:
    return await get_sms_service()
