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

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_VENDOR = "pending_vendor"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class TicketPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL = "general"
    SECURITY = "security"

class TicketSource(Enum):
    EMAIL = "email"
    PHONE = "phone"
    WEB = "web"
    API = "api"
    CHAT = "chat"
    SOCIAL = "social"
    INTERNAL = "internal"

@dataclass
class Ticket:
    ticket_id: str
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    source: TicketSource
    customer_id: str
    customer_email: str
    customer_name: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    due_date: Optional[datetime]
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class TicketComment:
    comment_id: str
    ticket_id: str
    author_id: str
    author_name: str
    author_type: str
    content: str
    is_internal: bool
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class TicketAttachment:
    attachment_id: str
    ticket_id: str
    filename: str
    file_size: int
    file_type: str
    file_path: str
    uploaded_by: str
    uploaded_at: datetime
    metadata: Dict[str, Any]

class TicketManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.ticket_cache: Dict[str, Ticket] = {}
        self.auto_assignment_rules: List[Dict[str, Any]] = []
        self.sla_rules: Dict[str, Dict[str, Any]] = {}
        self.escalation_rules: List[Dict[str, Any]] = []
        self.notification_templates: Dict[str, str] = {}

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing TicketManager...")
            self.database = get_database()
            await self._setup_ticket_tables()
            await self._load_configuration()
            await self._start_background_tasks()
            self.logger.info("TicketManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TicketManager: {str(e)}")
            return False

    async def _setup_ticket_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id SERIAL PRIMARY KEY,
                    ticket_id VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    category VARCHAR(30) NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    customer_id VARCHAR(255) NOT NULL,
                    customer_email VARCHAR(255) NOT NULL,
                    customer_name VARCHAR(255) NOT NULL,
                    assigned_to VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    due_date TIMESTAMP,
                    tags JSONB DEFAULT '[]'::jsonb,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS ticket_comments (
                    id SERIAL PRIMARY KEY,
                    comment_id VARCHAR(255) UNIQUE NOT NULL,
                    ticket_id VARCHAR(255) NOT NULL,
                    author_id VARCHAR(255) NOT NULL,
                    author_name VARCHAR(255) NOT NULL,
                    author_type VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    is_internal BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS ticket_attachments (
                    id SERIAL PRIMARY KEY,
                    attachment_id VARCHAR(255) UNIQUE NOT NULL,
                    ticket_id VARCHAR(255) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    uploaded_by VARCHAR(255) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS ticket_escalations (
                    id SERIAL PRIMARY KEY,
                    escalation_id VARCHAR(255) UNIQUE NOT NULL,
                    ticket_id VARCHAR(255) NOT NULL,
                    escalated_from VARCHAR(255) NOT NULL,
                    escalated_to VARCHAR(255) NOT NULL,
                    reason TEXT NOT NULL,
                    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_status 
                ON support_tickets(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_priority 
                ON support_tickets(priority);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_category 
                ON support_tickets(category);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_id 
                ON support_tickets(customer_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_to 
                ON support_tickets(assigned_to);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at 
                ON support_tickets(created_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket_id 
                ON ticket_comments(ticket_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticket_comments_created_at 
                ON ticket_comments(created_at);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticket_attachments_ticket_id 
                ON ticket_attachments(ticket_id);
            """)
            
            await session.commit()

    async def _load_configuration(self):
        self.auto_assignment_rules = [
            {
                "category": TicketCategory.TECHNICAL,
                "priority": TicketPriority.CRITICAL,
                "assign_to": "senior_engineer",
                "sla_hours": 2
            },
            {
                "category": TicketCategory.BILLING,
                "priority": TicketPriority.HIGH,
                "assign_to": "billing_specialist",
                "sla_hours": 4
            },
            {
                "category": TicketCategory.SECURITY,
                "priority": TicketPriority.URGENT,
                "assign_to": "security_team",
                "sla_hours": 1
            }
        ]
        
        self.sla_rules = {
            TicketPriority.CRITICAL.value: {"response_hours": 1, "resolution_hours": 4},
            TicketPriority.URGENT.value: {"response_hours": 2, "resolution_hours": 8},
            TicketPriority.HIGH.value: {"response_hours": 4, "resolution_hours": 24},
            TicketPriority.NORMAL.value: {"response_hours": 8, "resolution_hours": 72},
            TicketPriority.LOW.value: {"response_hours": 24, "resolution_hours": 168}
        }
        
        self.escalation_rules = [
            {
                "condition": "overdue",
                "action": "escalate_to_manager",
                "threshold_hours": 24
            },
            {
                "condition": "no_response",
                "action": "escalate_to_senior",
                "threshold_hours": 48
            }
        ]

    async def _start_background_tasks(self):
        asyncio.create_task(self._escalation_monitor())
        asyncio.create_task(self._sla_monitor())

    async def _escalation_monitor(self):
        while True:
            try:
                await self._check_escalations()
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {str(e)}")
                await asyncio.sleep(3600)

    async def _sla_monitor(self):
        while True:
            try:
                await self._check_sla_violations()
                await asyncio.sleep(1800)
            except Exception as e:
                self.logger.error(f"Error in SLA monitor: {str(e)}")
                await asyncio.sleep(1800)

    async def create_ticket(
        self,
        title: str,
        description: str,
        customer_id: str,
        customer_email: str,
        customer_name: str,
        category: TicketCategory,
        priority: TicketPriority = TicketPriority.NORMAL,
        source: TicketSource = TicketSource.WEB,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            ticket_id = f"TICKET_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(customer_id) % 10000}"
            
            ticket = Ticket(
                ticket_id=ticket_id,
                title=title,
                description=description,
                status=TicketStatus.OPEN,
                priority=priority,
                category=category,
                source=source,
                customer_id=customer_id,
                customer_email=customer_email,
                customer_name=customer_name,
                assigned_to=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                resolved_at=None,
                closed_at=None,
                due_date=None,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO support_tickets (
                        ticket_id, title, description, status, priority, category, source,
                        customer_id, customer_email, customer_name, tags, metadata
                    ) VALUES (
                        :ticket_id, :title, :description, :status, :priority, :category, :source,
                        :customer_id, :customer_email, :customer_name, :tags, :metadata
                    )
                """, {
                    "ticket_id": ticket.ticket_id,
                    "title": ticket.title,
                    "description": ticket.description,
                    "status": ticket.status.value,
                    "priority": ticket.priority.value,
                    "category": ticket.category.value,
                    "source": ticket.source.value,
                    "customer_id": ticket.customer_id,
                    "customer_email": ticket.customer_email,
                    "customer_name": ticket.customer_name,
                    "tags": ticket.tags,
                    "metadata": ticket.metadata
                })
                await session.commit()
            
            await self._auto_assign_ticket(ticket)
            await self._set_ticket_due_date(ticket)
            await self._send_ticket_notification(ticket, "created")
            
            self.ticket_cache[ticket_id] = ticket
            self.logger.info(f"Ticket created: {ticket_id}")
            return ticket_id
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {str(e)}")
            return None

    async def _auto_assign_ticket(self, ticket: Ticket):
        try:
            for rule in self.auto_assignment_rules:
                if (rule["category"] == ticket.category and 
                    rule["priority"] == ticket.priority):
                    ticket.assigned_to = rule["assign_to"]
                    ticket.status = TicketStatus.IN_PROGRESS
                    
                    if not self.database:
                        return
                    
                    async with self.database.get_session() as session:
                        await session.execute("""
                            UPDATE support_tickets 
                            SET assigned_to = :assigned_to, status = :status, updated_at = :updated_at
                            WHERE ticket_id = :ticket_id
                        """, {
                            "ticket_id": ticket.ticket_id,
                            "assigned_to": ticket.assigned_to,
                            "status": ticket.status.value,
                            "updated_at": datetime.utcnow()
                        })
                        await session.commit()
                    
                    break
                    
        except Exception as e:
            self.logger.error(f"Failed to auto-assign ticket: {str(e)}")

    async def _set_ticket_due_date(self, ticket: Ticket):
        try:
            sla_rule = self.sla_rules.get(ticket.priority.value)
            if sla_rule:
                resolution_hours = sla_rule["resolution_hours"]
                ticket.due_date = datetime.utcnow() + timedelta(hours=resolution_hours)
                
                if not self.database:
                    return
                
                async with self.database.get_session() as session:
                    await session.execute("""
                        UPDATE support_tickets 
                        SET due_date = :due_date
                        WHERE ticket_id = :ticket_id
                    """, {
                        "ticket_id": ticket.ticket_id,
                        "due_date": ticket.due_date
                    })
                    await session.commit()
                    
        except Exception as e:
            self.logger.error(f"Failed to set ticket due date: {str(e)}")

    async def _send_ticket_notification(self, ticket: Ticket, event_type: str):
        try:
            if event_type == "created":
                message = f"New ticket {ticket.ticket_id} has been created: {ticket.title}"
            elif event_type == "assigned":
                message = f"Ticket {ticket.ticket_id} has been assigned to {ticket.assigned_to}"
            elif event_type == "resolved":
                message = f"Ticket {ticket.ticket_id} has been resolved"
            else:
                message = f"Ticket {ticket.ticket_id} has been updated"
            
            self.logger.info(f"Ticket notification: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to send ticket notification: {str(e)}")

    async def update_ticket(
        self,
        ticket_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        try:
            if ticket_id not in self.ticket_cache:
                ticket = await self.get_ticket(ticket_id)
                if not ticket:
                    return False
            else:
                ticket = self.ticket_cache[ticket_id]
            
            if not self.database:
                return False
            
            update_fields = ["updated_at = :updated_at"]
            params = {"ticket_id": ticket_id, "updated_at": datetime.utcnow()}
            
            if title is not None:
                update_fields.append("title = :title")
                params["title"] = title
                ticket.title = title
            
            if description is not None:
                update_fields.append("description = :description")
                params["description"] = description
                ticket.description = description
            
            if status is not None:
                update_fields.append("status = :status")
                params["status"] = status.value
                ticket.status = status
                
                if status == TicketStatus.RESOLVED:
                    update_fields.append("resolved_at = :resolved_at")
                    params["resolved_at"] = datetime.utcnow()
                    ticket.resolved_at = datetime.utcnow()
                elif status == TicketStatus.CLOSED:
                    update_fields.append("closed_at = :closed_at")
                    params["closed_at"] = datetime.utcnow()
                    ticket.closed_at = datetime.utcnow()
            
            if priority is not None:
                update_fields.append("priority = :priority")
                params["priority"] = priority.value
                ticket.priority = priority
            
            if category is not None:
                update_fields.append("category = :category")
                params["category"] = category.value
                ticket.category = category
            
            if assigned_to is not None:
                update_fields.append("assigned_to = :assigned_to")
                params["assigned_to"] = assigned_to
                ticket.assigned_to = assigned_to
            
            if tags is not None:
                update_fields.append("tags = :tags")
                params["tags"] = tags
                ticket.tags = tags
            
            if metadata is not None:
                update_fields.append("metadata = :metadata")
                params["metadata"] = metadata
                ticket.metadata = metadata
            
            async with self.database.get_session() as session:
                await session.execute(f"""
                    UPDATE support_tickets 
                    SET {', '.join(update_fields)}
                    WHERE ticket_id = :ticket_id
                """, params)
                await session.commit()
            
            self.ticket_cache[ticket_id] = ticket
            await self._send_ticket_notification(ticket, "updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update ticket: {str(e)}")
            return False

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        try:
            if ticket_id in self.ticket_cache:
                return self.ticket_cache[ticket_id]
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT ticket_id, title, description, status, priority, category, source,
                           customer_id, customer_email, customer_name, assigned_to, created_at,
                           updated_at, resolved_at, closed_at, due_date, tags, metadata
                    FROM support_tickets
                    WHERE ticket_id = :ticket_id
                """, {"ticket_id": ticket_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                ticket = Ticket(
                    ticket_id=row.ticket_id,
                    title=row.title,
                    description=row.description,
                    status=TicketStatus(row.status),
                    priority=TicketPriority(row.priority),
                    category=TicketCategory(row.category),
                    source=TicketSource(row.source),
                    customer_id=row.customer_id,
                    customer_email=row.customer_email,
                    customer_name=row.customer_name,
                    assigned_to=row.assigned_to,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    resolved_at=row.resolved_at,
                    closed_at=row.closed_at,
                    due_date=row.due_date,
                    tags=row.tags or [],
                    metadata=row.metadata or {}
                )
                
                self.ticket_cache[ticket_id] = ticket
                return ticket
                
        except Exception as e:
            self.logger.error(f"Failed to get ticket: {str(e)}")
            return None

    async def get_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        assigned_to: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Ticket]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        if priority:
            conditions.append("priority = :priority")
            params["priority"] = priority.value
        
        if category:
            conditions.append("category = :category")
            params["category"] = category.value
        
        if assigned_to:
            conditions.append("assigned_to = :assigned_to")
            params["assigned_to"] = assigned_to
        
        if customer_id:
            conditions.append("customer_id = :customer_id")
            params["customer_id"] = customer_id
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT ticket_id, title, description, status, priority, category, source,
                       customer_id, customer_email, customer_name, assigned_to, created_at,
                       updated_at, resolved_at, closed_at, due_date, tags, metadata
                FROM support_tickets
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            tickets = []
            for row in result:
                ticket = Ticket(
                    ticket_id=row.ticket_id,
                    title=row.title,
                    description=row.description,
                    status=TicketStatus(row.status),
                    priority=TicketPriority(row.priority),
                    category=TicketCategory(row.category),
                    source=TicketSource(row.source),
                    customer_id=row.customer_id,
                    customer_email=row.customer_email,
                    customer_name=row.customer_name,
                    assigned_to=row.assigned_to,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    resolved_at=row.resolved_at,
                    closed_at=row.closed_at,
                    due_date=row.due_date,
                    tags=row.tags or [],
                    metadata=row.metadata or {}
                )
                tickets.append(ticket)
            
            return tickets

    async def add_comment(
        self,
        ticket_id: str,
        author_id: str,
        author_name: str,
        author_type: str,
        content: str,
        is_internal: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        try:
            comment_id = f"COMMENT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(ticket_id) % 10000}"
            
            if not self.database:
                return None
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO ticket_comments (
                        comment_id, ticket_id, author_id, author_name, author_type,
                        content, is_internal, metadata
                    ) VALUES (
                        :comment_id, :ticket_id, :author_id, :author_name, :author_type,
                        :content, :is_internal, :metadata
                    )
                """, {
                    "comment_id": comment_id,
                    "ticket_id": ticket_id,
                    "author_id": author_id,
                    "author_name": author_name,
                    "author_type": author_type,
                    "content": content,
                    "is_internal": is_internal,
                    "metadata": metadata or {}
                })
                await session.commit()
            
            await self.update_ticket(ticket_id, status=TicketStatus.IN_PROGRESS)
            self.logger.info(f"Comment added to ticket {ticket_id}: {comment_id}")
            return comment_id
            
        except Exception as e:
            self.logger.error(f"Failed to add comment: {str(e)}")
            return None

    async def get_ticket_comments(
        self,
        ticket_id: str,
        include_internal: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[TicketComment]:
        if not self.database:
            return []
        
        conditions = ["ticket_id = :ticket_id"]
        params = {"ticket_id": ticket_id, "limit": limit, "offset": offset}
        
        if not include_internal:
            conditions.append("is_internal = FALSE")
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT comment_id, ticket_id, author_id, author_name, author_type,
                       content, is_internal, created_at, metadata
                FROM ticket_comments
                {where_clause}
                ORDER BY created_at ASC
                LIMIT :limit OFFSET :offset
            """, params)
            
            comments = []
            for row in result:
                comment = TicketComment(
                    comment_id=row.comment_id,
                    ticket_id=row.ticket_id,
                    author_id=row.author_id,
                    author_name=row.author_name,
                    author_type=row.author_type,
                    content=row.content,
                    is_internal=row.is_internal,
                    created_at=row.created_at,
                    metadata=row.metadata or {}
                )
                comments.append(comment)
            
            return comments

    async def _check_escalations(self):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT ticket_id, assigned_to, created_at, due_date, priority
                    FROM support_tickets
                    WHERE status IN ('open', 'in_progress', 'pending_customer', 'pending_vendor')
                    AND due_date < CURRENT_TIMESTAMP
                """)
                
                for row in result:
                    await self._escalate_ticket(row.ticket_id, "overdue")
                    
        except Exception as e:
            self.logger.error(f"Failed to check escalations: {str(e)}")

    async def _check_sla_violations(self):
        try:
            if not self.database:
                return
            
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT ticket_id, priority, created_at, due_date
                    FROM support_tickets
                    WHERE status IN ('open', 'in_progress')
                    AND due_date < CURRENT_TIMESTAMP
                """)
                
                for row in result:
                    await self._handle_sla_violation(row.ticket_id, row.priority)
                    
        except Exception as e:
            self.logger.error(f"Failed to check SLA violations: {str(e)}")

    async def _escalate_ticket(self, ticket_id: str, reason: str):
        try:
            if not self.database:
                return
            
            escalation_id = f"ESCALATION_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(ticket_id) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO ticket_escalations (
                        escalation_id, ticket_id, escalated_from, escalated_to, reason
                    ) VALUES (
                        :escalation_id, :ticket_id, :escalated_from, :escalated_to, :reason
                    )
                """, {
                    "escalation_id": escalation_id,
                    "ticket_id": ticket_id,
                    "escalated_from": "system",
                    "escalated_to": "manager",
                    "reason": reason
                })
                await session.commit()
            
            self.logger.warning(f"Ticket escalated: {ticket_id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate ticket: {str(e)}")

    async def _handle_sla_violation(self, ticket_id: str, priority: str):
        try:
            await self._escalate_ticket(ticket_id, f"SLA violation for {priority} priority ticket")
            self.logger.warning(f"SLA violation detected for ticket {ticket_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle SLA violation: {str(e)}")

    async def get_ticket_stats(
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
                    COUNT(*) as total_tickets,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tickets,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_tickets,
                    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets,
                    COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_tickets,
                    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent_tickets,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_tickets,
                    COUNT(CASE WHEN category = 'technical' THEN 1 END) as technical_tickets,
                    COUNT(CASE WHEN category = 'billing' THEN 1 END) as billing_tickets,
                    COUNT(CASE WHEN category = 'account' THEN 1 END) as account_tickets,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) as avg_resolution_hours
                FROM support_tickets
                WHERE created_at BETWEEN :start_date AND :end_date
            """, {"start_date": start_date, "end_date": end_date})
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_tickets": row.total_tickets,
                "open_tickets": row.open_tickets,
                "in_progress_tickets": row.in_progress_tickets,
                "resolved_tickets": row.resolved_tickets,
                "closed_tickets": row.closed_tickets,
                "critical_tickets": row.critical_tickets,
                "urgent_tickets": row.urgent_tickets,
                "high_tickets": row.high_tickets,
                "technical_tickets": row.technical_tickets,
                "billing_tickets": row.billing_tickets,
                "account_tickets": row.account_tickets,
                "avg_resolution_hours": float(row.avg_resolution_hours) if row.avg_resolution_hours else 0.0,
                "resolution_rate": (row.resolved_tickets / row.total_tickets * 100) if row.total_tickets > 0 else 0
            }

_ticket_manager: Optional[TicketManager] = None

async def get_ticket_manager() -> TicketManager:
    global _ticket_manager
    if _ticket_manager is None:
        _ticket_manager = TicketManager()
        await _ticket_manager.initialize()
    return _ticket_manager

async def init_ticket_manager() -> TicketManager:
    return await get_ticket_manager()
