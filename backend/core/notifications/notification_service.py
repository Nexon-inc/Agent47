import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from backend.core.event_bus.kafka_manager import EventBus, get_kafka
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.cache.redis_manager import init_redis

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_MESSAGE = "agent_message"
    SYSTEM_ALERT = "system_alert"
    INTEGRATION_ERROR = "integration_error"
    PLATFORM_UPDATE = "platform_update"
    BILLING_REMINDER = "billing_reminder"
    SECURITY_ALERT = "security_alert"
    INTER_AGENT_COMMUNICATION = "inter_agent_communication"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    STARRED = "starred"

@dataclass
class Notification:
    id: str
    user_id: int
    agent_id: Optional[str]
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    timestamp: datetime
    status: NotificationStatus
    metadata: Dict[str, Any] = None
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

@dataclass
class NotificationSummary:
    total_notifications: int
    unread_count: int
    starred_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_notifications: List[Notification]

class NotificationService:
    """Service for managing user notifications and inbox"""
    
    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
        self.notifications: Dict[str, Notification] = {}
        self.agent_icons = {
            "aria": "🌐",
            "clara": "🎧", 
            "eric": "💰",
            "jackie": "📢",
            "shakes": "✍️",
            "joe": "🔍",
            "purity": "💡"
        }
    
    async def initialize(self):
        """Initialize notification service"""
        if self._initialized:
            return
        
        try:
            kafka_manager = await get_kafka()
            self.event_bus = kafka_manager.event_bus
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            
            # Subscribe to notification events
            await self._setup_event_handlers()
            
            self._initialized = True
            logger.info("Notification service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
            raise
    
    async def _setup_event_handlers(self):
        """Setup event handlers for notification events"""
        self.event_bus.register_handler("task.completed", self._handle_task_completed)
        self.event_bus.register_handler("task.failed", self._handle_task_failed)
        self.event_bus.register_handler("agent.message", self._handle_agent_message)
        self.event_bus.register_handler("system.alert", self._handle_system_alert)
        self.event_bus.register_handler("integration.error", self._handle_integration_error)
        self.event_bus.register_handler("platform.update", self._handle_platform_update)
        self.event_bus.register_handler("billing.reminder", self._handle_billing_reminder)
        self.event_bus.register_handler("security.alert", self._handle_security_alert)
        self.event_bus.register_handler("agent.communication", self._handle_inter_agent_communication)
        
        # Subscribe to topics
        await self.event_bus.subscribe_to_topic("task.completed")
        await self.event_bus.subscribe_to_topic("task.failed")
        await self.event_bus.subscribe_to_topic("agent.message")
        await self.event_bus.subscribe_to_topic("system.alert")
        await self.event_bus.subscribe_to_topic("integration.error")
        await self.event_bus.subscribe_to_topic("platform.update")
        await self.event_bus.subscribe_to_topic("billing.reminder")
        await self.event_bus.subscribe_to_topic("security.alert")
        await self.event_bus.subscribe_to_topic("agent.communication")
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        agent_id: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> Notification:
        """Create a new notification"""
        if not self._initialized:
            await self.initialize()
        
        notification_id = f"notif_{user_id}_{datetime.utcnow().timestamp()}"
        
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            agent_id=agent_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            status=NotificationStatus.UNREAD,
            metadata=metadata or {}
        )
        
        self.notifications[notification_id] = notification
        
        # Publish notification event
        await self.event_bus.publish_event("notification.created", {
            "notification": asdict(notification),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Broadcast notification via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(user_id, {
                "id": notification_id,
                "type": notification_type.value,
                "title": title,
                "message": message,
                "agent_id": agent_id,
                "priority": priority.value,
                "metadata": metadata or {},
                "timestamp": notification.timestamp.isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast notification: {e}")
        
        logger.info(f"Notification created: {notification_type.value} for user {user_id}")
        return notification
    
    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        filter_type: Optional[NotificationType] = None,
        filter_status: Optional[NotificationStatus] = None,
        filter_agent: Optional[str] = None
    ) -> List[Notification]:
        """Get notifications for a user with filtering"""
        if not self._initialized:
            await self.initialize()
        
        # Filter notifications by user
        user_notifications = [
            notif for notif in self.notifications.values()
            if notif.user_id == user_id
        ]
        
        # Apply filters
        if filter_type:
            user_notifications = [n for n in user_notifications if n.type == filter_type]
        
        if filter_status:
            user_notifications = [n for n in user_notifications if n.status == filter_status]
        
        if filter_agent:
            user_notifications = [n for n in user_notifications if n.agent_id == filter_agent]
        
        # Sort by timestamp (newest first)
        user_notifications.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        return user_notifications[offset:offset + limit]
    
    async def get_notification_summary(self, user_id: int) -> NotificationSummary:
        """Get notification summary for a user"""
        if not self._initialized:
            await self.initialize()
        
        user_notifications = [
            notif for notif in self.notifications.values()
            if notif.user_id == user_id
        ]
        
        total_notifications = len(user_notifications)
        unread_count = len([n for n in user_notifications if n.status == NotificationStatus.UNREAD])
        starred_count = len([n for n in user_notifications if n.status == NotificationStatus.STARRED])
        
        # Count by type
        by_type = {}
        for notif in user_notifications:
            type_name = notif.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        # Count by priority
        by_priority = {}
        for notif in user_notifications:
            priority_name = notif.priority.value
            by_priority[priority_name] = by_priority.get(priority_name, 0) + 1
        
        # Get recent notifications (last 10)
        recent_notifications = sorted(user_notifications, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return NotificationSummary(
            total_notifications=total_notifications,
            unread_count=unread_count,
            starred_count=starred_count,
            by_type=by_type,
            by_priority=by_priority,
            recent_notifications=recent_notifications
        )
    
    async def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as read"""
        if not self._initialized:
            await self.initialize()
        
        if notification_id in self.notifications:
            notif = self.notifications[notification_id]
            if notif.user_id == user_id:
                notif.status = NotificationStatus.READ
                notif.read_at = datetime.utcnow()
                return True
        
        return False
    
    async def mark_notification_starred(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as starred"""
        if not self._initialized:
            await self.initialize()
        
        if notification_id in self.notifications:
            notif = self.notifications[notification_id]
            if notif.user_id == user_id:
                notif.status = NotificationStatus.STARRED
                return True
        
        return False
    
    async def archive_notification(self, notification_id: str, user_id: int) -> bool:
        """Archive a notification"""
        if not self._initialized:
            await self.initialize()
        
        if notification_id in self.notifications:
            notif = self.notifications[notification_id]
            if notif.user_id == user_id:
                notif.status = NotificationStatus.ARCHIVED
                notif.archived_at = datetime.utcnow()
                return True
        
        return False
    
    async def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        if not self._initialized:
            await self.initialize()
        
        count = 0
        for notif in self.notifications.values():
            if (notif.user_id == user_id and 
                notif.status == NotificationStatus.UNREAD):
                notif.status = NotificationStatus.READ
                notif.read_at = datetime.utcnow()
                count += 1
        
        return count
    
    async def generate_mock_notifications(self, user_id: int, count: int = 20):
        """Generate mock notifications for demonstration"""
        import random
        
        agents = ["aria", "clara", "eric", "jackie", "shakes", "joe", "purity"]
        notification_types = [
            NotificationType.TASK_COMPLETED,
            NotificationType.TASK_FAILED,
            NotificationType.AGENT_MESSAGE,
            NotificationType.SYSTEM_ALERT,
            NotificationType.INTEGRATION_ERROR,
            NotificationType.PLATFORM_UPDATE,
            NotificationType.INTER_AGENT_COMMUNICATION
        ]
        
        priorities = [NotificationPriority.LOW, NotificationPriority.MEDIUM, NotificationPriority.HIGH]
        
        for i in range(count):
            agent = random.choice(agents)
            notif_type = random.choice(notification_types)
            priority = random.choice(priorities)
            
            # Generate appropriate title and message based on type
            if notif_type == NotificationType.TASK_COMPLETED:
                title = f"{agent.title()} completed a task"
                message = f"Your {agent} agent has successfully completed the assigned task. Check the results in your dashboard."
            elif notif_type == NotificationType.TASK_FAILED:
                title = f"{agent.title()} task failed"
                message = f"A task assigned to {agent} has failed. Please review the error details and retry if necessary."
            elif notif_type == NotificationType.AGENT_MESSAGE:
                title = f"Message from {agent.title()}"
                message = f"Your {agent} agent has sent you a message. Click to view the full conversation."
            elif notif_type == NotificationType.SYSTEM_ALERT:
                title = "System Alert"
                message = "A system alert has been triggered. Please review the details and take appropriate action."
            elif notif_type == NotificationType.INTEGRATION_ERROR:
                title = "Integration Error"
                message = f"An error occurred with one of your platform integrations. Please check the connection status."
            elif notif_type == NotificationType.PLATFORM_UPDATE:
                title = "Platform Update"
                message = "One of your connected platforms has been updated. New features may be available."
            elif notif_type == NotificationType.INTER_AGENT_COMMUNICATION:
                title = "Agent Collaboration"
                message = f"Your agents are collaborating on a task. {agent.title()} is working with other agents to complete your request."
            else:
                title = f"Notification from {agent.title()}"
                message = f"You have a new notification from your {agent} agent."
            
            await self.create_notification(
                user_id=user_id,
                notification_type=notif_type,
                title=title,
                message=message,
                agent_id=agent,
                priority=priority,
                metadata={
                    "agent_icon": self.agent_icons.get(agent, "🤖"),
                    "generated": True
                }
            )
    
    async def _handle_task_completed(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task completion events"""
        try:
            task_data = event_data.get("data", {})
            user_id = task_data.get("user_id")
            agent_id = task_data.get("agent_id")
            task_title = task_data.get("title", "Task")
            
            if user_id and agent_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.TASK_COMPLETED,
                    title=f"{agent_id.title()} completed a task",
                    message=f"Your {agent_id} agent has successfully completed '{task_title}'. Check the results in your dashboard.",
                    agent_id=agent_id,
                    priority=NotificationPriority.MEDIUM,
                    metadata={
                        "task_id": task_data.get("id"),
                        "agent_icon": self.agent_icons.get(agent_id, "🤖")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    async def _handle_task_failed(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task failure events"""
        try:
            task_data = event_data.get("data", {})
            user_id = task_data.get("user_id")
            agent_id = task_data.get("agent_id")
            task_title = task_data.get("title", "Task")
            error_message = task_data.get("error", "Unknown error")
            
            if user_id and agent_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.TASK_FAILED,
                    title=f"{agent_id.title()} task failed",
                    message=f"A task '{task_title}' assigned to {agent_id} has failed: {error_message}. Please review and retry.",
                    agent_id=agent_id,
                    priority=NotificationPriority.HIGH,
                    metadata={
                        "task_id": task_data.get("id"),
                        "error": error_message,
                        "agent_icon": self.agent_icons.get(agent_id, "🤖")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
    
    async def _handle_agent_message(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle agent message events"""
        try:
            message_data = event_data.get("data", {})
            user_id = message_data.get("user_id")
            agent_id = message_data.get("from_agent")
            message_content = message_data.get("content", {})
            
            if user_id and agent_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.AGENT_MESSAGE,
                    title=f"Message from {agent_id.title()}",
                    message=f"Your {agent_id} agent has sent you a message. Click to view the full conversation.",
                    agent_id=agent_id,
                    priority=NotificationPriority.MEDIUM,
                    metadata={
                        "message_id": message_data.get("id"),
                        "agent_icon": self.agent_icons.get(agent_id, "🤖")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling agent message: {e}")
    
    async def _handle_system_alert(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle system alert events"""
        try:
            alert_data = event_data.get("data", {})
            user_id = alert_data.get("user_id")
            alert_type = alert_data.get("type", "System Alert")
            alert_message = alert_data.get("message", "A system alert has been triggered.")
            
            if user_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.SYSTEM_ALERT,
                    title=alert_type,
                    message=alert_message,
                    priority=NotificationPriority.HIGH,
                    metadata={
                        "alert_type": alert_type,
                        "system_generated": True
                    }
                )
        except Exception as e:
            logger.error(f"Error handling system alert: {e}")
    
    async def _handle_integration_error(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle integration error events"""
        try:
            error_data = event_data.get("data", {})
            user_id = error_data.get("user_id")
            platform = error_data.get("platform", "Unknown Platform")
            error_message = error_data.get("error", "Integration error occurred")
            
            if user_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.INTEGRATION_ERROR,
                    title=f"{platform} Integration Error",
                    message=f"An error occurred with your {platform} integration: {error_message}. Please check the connection.",
                    priority=NotificationPriority.HIGH,
                    metadata={
                        "platform": platform,
                        "error": error_message
                    }
                )
        except Exception as e:
            logger.error(f"Error handling integration error: {e}")
    
    async def _handle_platform_update(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle platform update events"""
        try:
            update_data = event_data.get("data", {})
            user_id = update_data.get("user_id")
            platform = update_data.get("platform", "Platform")
            update_message = update_data.get("message", "Platform has been updated")
            
            if user_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.PLATFORM_UPDATE,
                    title=f"{platform} Update",
                    message=update_message,
                    priority=NotificationPriority.LOW,
                    metadata={
                        "platform": platform,
                        "update_type": update_data.get("type", "general")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling platform update: {e}")
    
    async def _handle_billing_reminder(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle billing reminder events"""
        try:
            billing_data = event_data.get("data", {})
            user_id = billing_data.get("user_id")
            reminder_type = billing_data.get("type", "Billing Reminder")
            message = billing_data.get("message", "Please review your billing information")
            
            if user_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.BILLING_REMINDER,
                    title=reminder_type,
                    message=message,
                    priority=NotificationPriority.MEDIUM,
                    metadata={
                        "billing_type": reminder_type,
                        "amount": billing_data.get("amount")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling billing reminder: {e}")
    
    async def _handle_security_alert(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle security alert events"""
        try:
            security_data = event_data.get("data", {})
            user_id = security_data.get("user_id")
            alert_type = security_data.get("type", "Security Alert")
            message = security_data.get("message", "A security alert has been triggered")
            
            if user_id:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.SECURITY_ALERT,
                    title=alert_type,
                    message=message,
                    priority=NotificationPriority.URGENT,
                    metadata={
                        "security_type": alert_type,
                        "ip_address": security_data.get("ip_address"),
                        "user_agent": security_data.get("user_agent")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling security alert: {e}")
    
    async def _handle_inter_agent_communication(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle inter-agent communication events"""
        try:
            comm_data = event_data.get("data", {})
            user_id = comm_data.get("user_id")
            from_agent = comm_data.get("from_agent")
            to_agent = comm_data.get("to_agent")
            message_type = comm_data.get("message_type", "collaboration")
            
            if user_id and from_agent and to_agent:
                await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.INTER_AGENT_COMMUNICATION,
                    title="Agent Collaboration",
                    message=f"Your {from_agent.title()} and {to_agent.title()} agents are collaborating on a task. This may take some time to complete.",
                    agent_id=from_agent,
                    priority=NotificationPriority.LOW,
                    metadata={
                        "from_agent": from_agent,
                        "to_agent": to_agent,
                        "message_type": message_type,
                        "agent_icon": self.agent_icons.get(from_agent, "🤖")
                    }
                )
        except Exception as e:
            logger.error(f"Error handling inter-agent communication: {e}")

# Global notification service instance
notification_service = NotificationService()

async def get_notification_service() -> NotificationService:
    return notification_service

async def init_notifications():
    await notification_service.initialize()

async def close_notifications():
    # Cleanup if needed
    pass
