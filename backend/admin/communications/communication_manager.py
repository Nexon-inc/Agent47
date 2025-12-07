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

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class CommunicationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"

class CommunicationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"

@dataclass
class Communication:
    communication_id: str
    type: CommunicationType
    recipient: str
    subject: str
    message: str
    template_id: Optional[str]
    status: CommunicationStatus
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    metadata: Dict[str, Any]

class CommunicationManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.email_service = None
        self.sms_service = None
        self.notification_service = None
        self.template_manager = None
        self.communication_queue = asyncio.Queue()
        self.processing_active = False

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CommunicationManager...")
            self.database = get_database()
            await self._setup_communication_tables()
            await self._initialize_services()
            await self._load_templates()
            await self._setup_automated_triggers()
            self.logger.info("CommunicationManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CommunicationManager: {str(e)}")
            return False

    async def _setup_communication_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS communications (
                    id SERIAL PRIMARY KEY,
                    communication_id VARCHAR(255) UNIQUE NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    recipient VARCHAR(255) NOT NULL,
                    subject VARCHAR(255),
                    message TEXT NOT NULL,
                    template_id VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    metadata JSONB,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS communication_templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    subject VARCHAR(255),
                    body TEXT NOT NULL,
                    variables JSONB,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS communication_triggers (
                    id SERIAL PRIMARY KEY,
                    trigger_name VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    template_id VARCHAR(255) NOT NULL,
                    conditions JSONB,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS communication_logs (
                    id SERIAL PRIMARY KEY,
                    communication_id VARCHAR(255) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_communications_status 
                ON communications(status)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_communications_type 
                ON communications(type)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_communications_created_at 
                ON communications(created_at)
            """))
            
            await session.commit()

    async def _initialize_services(self):
        from .email_service import EmailService
        from .sms_service import SMSService
        from .notification_service import NotificationService
        from .template_manager import TemplateManager
        
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.notification_service = NotificationService()
        self.template_manager = TemplateManager()

    async def _load_templates(self):
        await self.template_manager.load_templates()

    async def _setup_automated_triggers(self):
        triggers = [
            {
                "trigger_name": "user_signup",
                "event_type": "user_registered",
                "template_id": "welcome_email",
                "conditions": {"user_type": "new"}
            },
            {
                "trigger_name": "payment_success",
                "event_type": "payment_completed",
                "template_id": "payment_confirmation",
                "conditions": {"status": "successful"}
            },
            {
                "trigger_name": "password_reset",
                "event_type": "password_reset_requested",
                "template_id": "password_reset",
                "conditions": {}
            },
            {
                "trigger_name": "subscription_upgrade",
                "event_type": "subscription_changed",
                "template_id": "subscription_upgrade",
                "conditions": {"change_type": "upgrade"}
            },
            {
                "trigger_name": "system_update",
                "event_type": "system_maintenance",
                "template_id": "system_notification",
                "conditions": {"maintenance_type": "scheduled"}
            }
        ]
        
        for trigger in triggers:
            await self._add_trigger(trigger)

    async def _add_trigger(self, trigger_data: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO communication_triggers (trigger_name, event_type, template_id, conditions)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (trigger_name) DO UPDATE SET
                        event_type = EXCLUDED.event_type,
                        template_id = EXCLUDED.template_id,
                        conditions = EXCLUDED.conditions
                """), (
                    trigger_data["trigger_name"],
                    trigger_data["event_type"],
                    trigger_data["template_id"],
                    trigger_data["conditions"]
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to add trigger: {str(e)}")

    async def send_communication(self, comm_type: CommunicationType, recipient: str, 
                               subject: str, message: str, template_id: str = None,
                               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        communication_id = f"comm_{comm_type.value}_{int(datetime.utcnow().timestamp())}"
        
        try:
            communication = Communication(
                communication_id=communication_id,
                type=comm_type,
                recipient=recipient,
                subject=subject,
                message=message,
                template_id=template_id,
                status=CommunicationStatus.PENDING,
                created_at=datetime.utcnow(),
                sent_at=None,
                delivered_at=None,
                metadata=metadata or {}
            )
            
            await self._save_communication(communication)
            await self.communication_queue.put(communication)
            
            return {
                "success": True,
                "communication_id": communication_id,
                "message": "Communication queued successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send communication: {str(e)}")
            return {"error": str(e)}

    async def _save_communication(self, communication: Communication):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO communications (
                        communication_id, type, recipient, subject, message, template_id, status, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    communication.communication_id,
                    communication.type.value,
                    communication.recipient,
                    communication.subject,
                    communication.message,
                    communication.template_id,
                    communication.status.value,
                    communication.metadata
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save communication: {str(e)}")

    async def start_processing(self):
        if self.processing_active:
            return
        
        self.processing_active = True
        asyncio.create_task(self._process_communication_queue())

    async def stop_processing(self):
        self.processing_active = False

    async def _process_communication_queue(self):
        while self.processing_active:
            try:
                communication = await asyncio.wait_for(self.communication_queue.get(), timeout=1.0)
                await self._process_communication(communication)
                self.communication_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing communication queue: {str(e)}")

    async def _process_communication(self, communication: Communication):
        try:
            if communication.type == CommunicationType.EMAIL:
                success = await self.email_service.send_email(
                    communication.recipient,
                    communication.subject,
                    communication.message
                )
            elif communication.type == CommunicationType.SMS:
                success = await self.sms_service.send_sms(
                    communication.recipient,
                    communication.message
                )
            elif communication.type == CommunicationType.PUSH:
                success = await self.notification_service.send_push_notification(
                    communication.recipient,
                    communication.subject,
                    communication.message
                )
            elif communication.type == CommunicationType.SLACK:
                success = await self.notification_service.send_slack_message(
                    communication.recipient,
                    communication.message
                )
            else:
                success = False
                self.logger.error(f"Unsupported communication type: {communication.type}")
            
            if success:
                communication.status = CommunicationStatus.SENT
                communication.sent_at = datetime.utcnow()
            else:
                communication.status = CommunicationStatus.FAILED
            
            await self._update_communication_status(communication)
            await self._log_communication_action(communication.communication_id, 
                                               "processed", {"success": success})
            
        except Exception as e:
            self.logger.error(f"Failed to process communication {communication.communication_id}: {str(e)}")
            communication.status = CommunicationStatus.FAILED
            await self._update_communication_status(communication)

    async def _update_communication_status(self, communication: Communication):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE communications 
                    SET status = %s, sent_at = %s, delivered_at = %s
                    WHERE communication_id = %s
                """), (
                    communication.status.value,
                    communication.sent_at,
                    communication.delivered_at,
                    communication.communication_id
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update communication status: {str(e)}")

    async def _log_communication_action(self, communication_id: str, action: str, details: Dict[str, Any]):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO communication_logs (communication_id, action, details)
                    VALUES (%s, %s, %s)
                """), (communication_id, action, details))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log communication action: {str(e)}")

    async def send_bulk_communication(self, comm_type: CommunicationType, recipients: List[str],
                                    subject: str, message: str, template_id: str = None) -> Dict[str, Any]:
        results = []
        
        for recipient in recipients:
            result = await self.send_communication(comm_type, recipient, subject, message, template_id)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        return {
            "total_recipients": len(recipients),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def trigger_automated_communication(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT trigger_name, template_id, conditions
                    FROM communication_triggers 
                    WHERE event_type = %s AND enabled = TRUE
                """), (event_type,))
                
                triggers = []
                for row in result.fetchall():
                    trigger = {
                        "trigger_name": row[0],
                        "template_id": row[1],
                        "conditions": row[2]
                    }
                    
                    if await self._check_trigger_conditions(trigger["conditions"], event_data):
                        triggers.append(trigger)
                
                results = []
                for trigger in triggers:
                    template = await self.template_manager.get_template(trigger["template_id"])
                    if template:
                        rendered_message = await self.template_manager.render_template(
                            template, event_data
                        )
                        
                        if "user_email" in event_data:
                            result = await self.send_communication(
                                CommunicationType.EMAIL,
                                event_data["user_email"],
                                template.get("subject", "Notification"),
                                rendered_message,
                                trigger["template_id"]
                            )
                            results.append(result)
                
                return {
                    "triggers_found": len(triggers),
                    "communications_sent": len(results),
                    "results": results
                }
                
        except Exception as e:
            self.logger.error(f"Failed to trigger automated communication: {str(e)}")
            return {"error": str(e)}

    async def _check_trigger_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        if not conditions:
            return True
        
        for key, value in conditions.items():
            if key not in event_data or event_data[key] != value:
                return False
        
        return True

    async def get_communication_status(self, communication_id: str) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT communication_id, type, recipient, subject, status, 
                           created_at, sent_at, delivered_at, metadata
                    FROM communications 
                    WHERE communication_id = %s
                """), (communication_id,))
                
                row = result.fetchone()
                if row:
                    return {
                        "communication_id": row[0],
                        "type": row[1],
                        "recipient": row[2],
                        "subject": row[3],
                        "status": row[4],
                        "created_at": row[5].isoformat(),
                        "sent_at": row[6].isoformat() if row[6] else None,
                        "delivered_at": row[7].isoformat() if row[7] else None,
                        "metadata": row[8]
                    }
                return {"error": "Communication not found"}
                
        except Exception as e:
            self.logger.error(f"Failed to get communication status: {str(e)}")
            return {"error": str(e)}

    async def get_communication_statistics(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_communications,
                        COUNT(*) FILTER (WHERE status = 'sent') as sent_communications,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_communications,
                        COUNT(*) FILTER (WHERE type = 'email') as email_count,
                        COUNT(*) FILTER (WHERE type = 'sms') as sms_count,
                        COUNT(*) FILTER (WHERE type = 'push') as push_count,
                        AVG(EXTRACT(EPOCH FROM (sent_at - created_at))) as avg_send_time
                    FROM communications 
                    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_communications": row[0],
                        "sent_communications": row[1],
                        "failed_communications": row[2],
                        "email_count": row[3],
                        "sms_count": row[4],
                        "push_count": row[5],
                        "avg_send_time_seconds": row[6] or 0,
                        "success_rate": (row[1] / max(row[0], 1)) * 100
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get communication statistics: {str(e)}")
            return {}

    async def retry_failed_communications(self) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT communication_id, type, recipient, subject, message, template_id, metadata
                    FROM communications 
                    WHERE status = 'failed' AND retry_count < max_retries
                """))
                
                retried_count = 0
                for row in result.fetchall():
                    communication = Communication(
                        communication_id=row[0],
                        type=CommunicationType(row[1]),
                        recipient=row[2],
                        subject=row[3],
                        message=row[4],
                        template_id=row[5],
                        status=CommunicationStatus.PENDING,
                        created_at=datetime.utcnow(),
                        sent_at=None,
                        delivered_at=None,
                        metadata=row[6] or {}
                    )
                    
                    await self.communication_queue.put(communication)
                    retried_count += 1
                
                return {
                    "retried_count": retried_count,
                    "message": f"Retried {retried_count} failed communications"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to retry failed communications: {str(e)}")
            return {"error": str(e)}

    async def cleanup_old_communications(self, days: int = 30):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    DELETE FROM communications 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                
                await session.execute(text("""
                    DELETE FROM communication_logs 
                    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to cleanup old communications: {str(e)}")

    async def shutdown(self):
        self.logger.info("Shutting down CommunicationManager...")
        await self.stop_processing()
        await self.communication_queue.join()
        self.logger.info("CommunicationManager shutdown complete")
