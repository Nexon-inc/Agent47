import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL = "general"

@dataclass
class Ticket:
    ticket_id: str
    user_id: str
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    metadata: Dict[str, Any]

class SupportManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.ticket_manager = None
        self.knowledge_base = None
        self.customer_service = None
        self.support_queue = asyncio.Queue()
        self.processing_active = False

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing SupportManager...")
            self.database = get_database()
            await self._setup_support_tables()
            await self._initialize_services()
            await self._load_knowledge_base()
            self.logger.info("SupportManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize SupportManager: {str(e)}")
            return False

    async def _setup_support_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id SERIAL PRIMARY KEY,
                    ticket_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    status VARCHAR(30) DEFAULT 'open',
                    assigned_to VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    metadata JSONB,
                    response_time_hours FLOAT,
                    resolution_time_hours FLOAT
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS ticket_responses (
                    id SERIAL PRIMARY KEY,
                    ticket_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    is_internal BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_base_articles (
                    id SERIAL PRIMARY KEY,
                    article_id VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    tags JSONB,
                    views INTEGER DEFAULT 0,
                    helpful_votes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published BOOLEAN DEFAULT TRUE
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS support_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_date DATE NOT NULL,
                    total_tickets INTEGER DEFAULT 0,
                    resolved_tickets INTEGER DEFAULT 0,
                    avg_response_time_hours FLOAT DEFAULT 0,
                    avg_resolution_time_hours FLOAT DEFAULT 0,
                    customer_satisfaction_score FLOAT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tickets_status 
                ON support_tickets(status)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tickets_priority 
                ON support_tickets(priority)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tickets_user_id 
                ON support_tickets(user_id)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to 
                ON support_tickets(assigned_to)
            """))
            
            await session.commit()

    async def _initialize_services(self):
        from .ticket_manager import TicketManager
        from .knowledge_base import KnowledgeBase
        from .customer_service import CustomerService
        
        self.ticket_manager = TicketManager()
        self.knowledge_base = KnowledgeBase()
        self.customer_service = CustomerService()

    async def _load_knowledge_base(self):
        await self.knowledge_base.load_articles()

    async def create_ticket(self, user_id: str, subject: str, description: str,
                          category: TicketCategory, priority: TicketPriority = TicketPriority.MEDIUM) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        ticket_id = f"ticket_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            ticket = Ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                status=TicketStatus.OPEN,
                assigned_to=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                resolved_at=None,
                metadata={}
            )
            
            await self._save_ticket(ticket)
            await self._auto_assign_ticket(ticket)
            await self._send_ticket_notifications(ticket)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "message": "Support ticket created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {str(e)}")
            return {"error": str(e)}

    async def _save_ticket(self, ticket: Ticket):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO support_tickets (
                        ticket_id, user_id, subject, description, category, priority, status,
                        assigned_to, created_at, updated_at, resolved_at, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    ticket.ticket_id,
                    ticket.user_id,
                    ticket.subject,
                    ticket.description,
                    ticket.category.value,
                    ticket.priority.value,
                    ticket.status.value,
                    ticket.assigned_to,
                    ticket.created_at,
                    ticket.updated_at,
                    ticket.resolved_at,
                    ticket.metadata
                ))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save ticket: {str(e)}")

    async def _auto_assign_ticket(self, ticket: Ticket):
        try:
            if ticket.priority == TicketPriority.URGENT:
                ticket.assigned_to = "senior_support"
            elif ticket.category == TicketCategory.BILLING:
                ticket.assigned_to = "billing_support"
            elif ticket.category == TicketCategory.TECHNICAL:
                ticket.assigned_to = "technical_support"
            else:
                ticket.assigned_to = "general_support"
            
            await self._update_ticket(ticket)
            
        except Exception as e:
            self.logger.error(f"Failed to auto-assign ticket: {str(e)}")

    async def _send_ticket_notifications(self, ticket: Ticket):
        try:
            notification_data = {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "assigned_to": ticket.assigned_to
            }
            
            if ticket.assigned_to:
                await self._send_assignment_notification(ticket.assigned_to, notification_data)
            
            await self._send_user_confirmation(ticket.user_id, notification_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send ticket notifications: {str(e)}")

    async def _send_assignment_notification(self, assigned_to: str, notification_data: Dict[str, Any]):
        try:
            message = f"New ticket assigned: {notification_data['subject']} (Priority: {notification_data['priority']})"
            
            if self.settings.slack.webhook_url:
                slack_payload = {
                    "text": f"🎫 *New Support Ticket Assigned*",
                    "attachments": [{
                        "color": "#ff6b35",
                        "fields": [
                            {"title": "Ticket ID", "value": notification_data['ticket_id'], "short": True},
                            {"title": "Subject", "value": notification_data['subject'], "short": True},
                            {"title": "Priority", "value": notification_data['priority'], "short": True},
                            {"title": "Category", "value": notification_data['category'], "short": True}
                        ]
                    }]
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send assignment notification: {str(e)}")

    async def _send_user_confirmation(self, user_id: str, notification_data: Dict[str, Any]):
        try:
            message = f"Your support ticket has been created. Ticket ID: {notification_data['ticket_id']}"
            
        except Exception as e:
            self.logger.error(f"Failed to send user confirmation: {str(e)}")

    async def update_ticket_status(self, ticket_id: str, status: TicketStatus, 
                                 user_id: str, notes: str = None) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT * FROM support_tickets WHERE ticket_id = %s
                """), (ticket_id,))
                
                row = result.fetchone()
                if not row:
                    return False
                
                ticket = Ticket(
                    ticket_id=row[1],
                    user_id=row[2],
                    subject=row[3],
                    description=row[4],
                    category=TicketCategory(row[5]),
                    priority=TicketPriority(row[6]),
                    status=status,
                    assigned_to=row[8],
                    created_at=row[9],
                    updated_at=datetime.utcnow(),
                    resolved_at=datetime.utcnow() if status == TicketStatus.RESOLVED else None,
                    metadata=row[12] or {}
                )
                
                await session.execute(text("""
                    UPDATE support_tickets 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP, resolved_at = %s
                    WHERE ticket_id = %s
                """), (status.value, ticket.resolved_at, ticket_id))
                
                if notes:
                    await session.execute(text("""
                        INSERT INTO ticket_responses (ticket_id, user_id, message, is_internal)
                        VALUES (%s, %s, %s, TRUE)
                    """), (ticket_id, user_id, notes))
                
                await session.commit()
                
                await self._send_status_update_notification(ticket, status, notes)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update ticket status: {str(e)}")
            return False

    async def _send_status_update_notification(self, ticket: Ticket, status: TicketStatus, notes: str = None):
        try:
            status_message = f"Ticket {ticket.ticket_id} status updated to: {status.value}"
            if notes:
                status_message += f"\nNotes: {notes}"
            
        except Exception as e:
            self.logger.error(f"Failed to send status update notification: {str(e)}")

    async def add_ticket_response(self, ticket_id: str, user_id: str, message: str, 
                                is_internal: bool = False) -> bool:
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO ticket_responses (ticket_id, user_id, message, is_internal)
                    VALUES (%s, %s, %s, %s)
                """), (ticket_id, user_id, message, is_internal))
                
                await session.execute(text("""
                    UPDATE support_tickets 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE ticket_id = %s
                """), (ticket_id,))
                
                await session.commit()
                
                if not is_internal:
                    await self._send_response_notification(ticket_id, user_id, message)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add ticket response: {str(e)}")
            return False

    async def _send_response_notification(self, ticket_id: str, user_id: str, message: str):
        try:
            notification_message = f"New response added to ticket {ticket_id}"
            
        except Exception as e:
            self.logger.error(f"Failed to send response notification: {str(e)}")

    async def get_ticket_details(self, ticket_id: str) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT ticket_id, user_id, subject, description, category, priority, status,
                           assigned_to, created_at, updated_at, resolved_at, metadata
                    FROM support_tickets 
                    WHERE ticket_id = %s
                """), (ticket_id,))
                
                row = result.fetchone()
                if not row:
                    return {"error": "Ticket not found"}
                
                responses_result = await session.execute(text("""
                    SELECT user_id, message, is_internal, created_at
                    FROM ticket_responses 
                    WHERE ticket_id = %s
                    ORDER BY created_at ASC
                """), (ticket_id,))
                
                responses = []
                for resp_row in responses_result.fetchall():
                    responses.append({
                        "user_id": resp_row[0],
                        "message": resp_row[1],
                        "is_internal": resp_row[2],
                        "created_at": resp_row[3].isoformat()
                    })
                
                return {
                    "ticket_id": row[0],
                    "user_id": row[1],
                    "subject": row[2],
                    "description": row[3],
                    "category": row[4],
                    "priority": row[5],
                    "status": row[6],
                    "assigned_to": row[7],
                    "created_at": row[8].isoformat(),
                    "updated_at": row[9].isoformat(),
                    "resolved_at": row[10].isoformat() if row[10] else None,
                    "metadata": row[11],
                    "responses": responses
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get ticket details: {str(e)}")
            return {"error": str(e)}

    async def get_user_tickets(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT ticket_id, subject, category, priority, status, assigned_to, 
                           created_at, updated_at, resolved_at
                    FROM support_tickets 
                    WHERE user_id = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                """), (user_id, limit))
                
                tickets = []
                for row in result.fetchall():
                    tickets.append({
                        "ticket_id": row[0],
                        "subject": row[1],
                        "category": row[2],
                        "priority": row[3],
                        "status": row[4],
                        "assigned_to": row[5],
                        "created_at": row[6].isoformat(),
                        "updated_at": row[7].isoformat(),
                        "resolved_at": row[8].isoformat() if row[8] else None
                    })
                
                return tickets
        except Exception as e:
            self.logger.error(f"Failed to get user tickets: {str(e)}")
            return []

    async def get_support_queue(self, assigned_to: str = None, status: TicketStatus = None) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT ticket_id, user_id, subject, category, priority, status, assigned_to, 
                           created_at, updated_at
                    FROM support_tickets 
                """
                params = []
                
                conditions = []
                if assigned_to:
                    conditions.append("assigned_to = %s")
                    params.append(assigned_to)
                
                if status:
                    conditions.append("status = %s")
                    params.append(status.value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY priority DESC, created_at ASC"
                
                result = await session.execute(text(query), params)
                
                tickets = []
                for row in result.fetchall():
                    tickets.append({
                        "ticket_id": row[0],
                        "user_id": row[1],
                        "subject": row[2],
                        "category": row[3],
                        "priority": row[4],
                        "status": row[5],
                        "assigned_to": row[6],
                        "created_at": row[7].isoformat(),
                        "updated_at": row[8].isoformat()
                    })
                
                return tickets
        except Exception as e:
            self.logger.error(f"Failed to get support queue: {str(e)}")
            return []

    async def get_support_statistics(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_tickets,
                        COUNT(*) FILTER (WHERE status = 'open') as open_tickets,
                        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tickets,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
                        COUNT(*) FILTER (WHERE priority = 'urgent') as urgent_tickets,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_response_time_hours,
                        AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_time_hours
                    FROM support_tickets 
                    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_tickets": row[0],
                        "open_tickets": row[1],
                        "in_progress_tickets": row[2],
                        "resolved_tickets": row[3],
                        "urgent_tickets": row[4],
                        "avg_response_time_hours": row[5] or 0,
                        "avg_resolution_time_hours": row[6] or 0,
                        "resolution_rate": (row[3] / max(row[0], 1)) * 100
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get support statistics: {str(e)}")
            return {}

    async def search_knowledge_base(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        return await self.knowledge_base.search_articles(query, category)

    async def create_knowledge_article(self, title: str, content: str, category: str,
                                     tags: List[str] = None) -> Dict[str, Any]:
        return await self.knowledge_base.create_article(title, content, category, tags)

    async def _update_ticket(self, ticket: Ticket):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE support_tickets 
                    SET assigned_to = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE ticket_id = %s
                """), (ticket.assigned_to, ticket.ticket_id))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update ticket: {str(e)}")

    async def cleanup_old_tickets(self, days: int = 90):
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(text("""
                    UPDATE support_tickets 
                    SET status = 'closed'
                    WHERE status = 'resolved' AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                """), (days,))
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to cleanup old tickets: {str(e)}")

    async def shutdown(self):
        self.logger.info("Shutting down SupportManager...")
        self.logger.info("SupportManager shutdown complete")
