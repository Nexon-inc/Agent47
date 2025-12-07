import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from .kafka_manager import EventBus, get_kafka
from ..ai import get_ai_service_manager, AIServiceManager
from ..cache.redis_manager import init_redis
from ..config import settings

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Task:
    id: str
    user_id: int
    agent_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    assigned_agents: List[str] = None
    dependencies: List[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class AgentMessage:
    id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    task_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM

@dataclass
class TaskSummary:
    task_id: str
    agent_id: str
    summary: str
    completed_at: datetime
    metrics: Dict[str, Any]
    next_steps: List[str]

class IntercommunicationService:
    """Service for agent-to-agent communication and task coordination"""
    
    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
        self.active_tasks: Dict[str, Task] = {}
        self.agent_messages: List[AgentMessage] = []
        self.task_summaries: Dict[str, TaskSummary] = {}
    
    async def initialize(self):
        """Initialize intercommunication service"""
        if self._initialized:
            return
        
        try:
            kafka_manager = await get_kafka()
            self.event_bus = kafka_manager.event_bus
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            
            # Subscribe to agent communication topics
            await self._setup_event_handlers()
            
            self._initialized = True
            logger.info("Intercommunication service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize intercommunication service: {e}")
            raise
    
    async def _setup_event_handlers(self):
        """Setup event handlers for agent communication"""
        # Register handlers for different agent communication topics
        self.event_bus.register_handler("agent.communication", self._handle_agent_message)
        self.event_bus.register_handler("agent.task_update", self._handle_task_update)
        self.event_bus.register_handler("agent.task_complete", self._handle_task_completion)
        self.event_bus.register_handler("agent.intercommunication", self._handle_intercommunication)
        
        # Subscribe to topics
        await self.event_bus.subscribe_to_topic("agent.communication")
        await self.event_bus.subscribe_to_topic("agent.task_update")
        await self.event_bus.subscribe_to_topic("agent.task_complete")
        await self.event_bus.subscribe_to_topic("agent.intercommunication")
    
    async def create_task(
        self,
        user_id: int,
        agent_id: str,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        assigned_agents: List[str] = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """Create a new task for agent coordination"""
        if not self._initialized:
            await self.initialize()
        
        task_id = f"task_{user_id}_{agent_id}_{datetime.utcnow().timestamp()}"
        
        task = Task(
            id=task_id,
            user_id=user_id,
            agent_id=agent_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            due_date=due_date,
            assigned_agents=assigned_agents or [agent_id],
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.active_tasks[task_id] = task
        
        # Publish task creation event
        await self.event_bus.publish_event("agent.task_created", {
            "task": asdict(task),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Task created: {task_id} for agent {agent_id}")
        return task
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update task status and progress"""
        if not self._initialized:
            await self.initialize()
        
        if task_id not in self.active_tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.active_tasks[task_id]
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if progress is not None:
            task.progress = progress
        
        if metadata:
            task.metadata.update(metadata)
        
        # Publish task update event
        await self.event_bus.publish_event("agent.task_update", {
            "task_id": task_id,
            "status": status.value,
            "progress": task.progress,
            "metadata": task.metadata,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Task {task_id} status updated to {status.value}")
        return True
    
    async def send_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> AgentMessage:
        """Send a message between agents"""
        if not self._initialized:
            await self.initialize()
        
        message_id = f"msg_{from_agent}_{to_agent}_{datetime.utcnow().timestamp()}"
        
        message = AgentMessage(
            id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow(),
            task_id=task_id,
            priority=priority
        )
        
        self.agent_messages.append(message)
        
        # Publish agent message event
        await self.event_bus.publish_event("agent.communication", {
            "message": asdict(message),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Message sent from {from_agent} to {to_agent}: {message_type}")
        return message
    
    async def initiate_intercommunication(
        self,
        user_id: int,
        primary_agent: str,
        secondary_agents: List[str],
        task_description: str,
        collaboration_goals: List[str]
    ) -> Dict[str, Any]:
        """Initiate intercommunication between multiple agents"""
        if not self._initialized:
            await self.initialize()
        
        # Create a coordination task
        coordination_task = await self.create_task(
            user_id=user_id,
            agent_id=primary_agent,
            title="Agent Intercommunication",
            description=task_description,
            priority=TaskPriority.HIGH,
            assigned_agents=[primary_agent] + secondary_agents,
            metadata={
                "collaboration_goals": collaboration_goals,
                "intercommunication_type": "multi_agent"
            }
        )
        
        # Send coordination messages to all agents
        coordination_messages = []
        for agent in secondary_agents:
            message = await self.send_agent_message(
                from_agent=primary_agent,
                to_agent=agent,
                message_type="coordination_request",
                content={
                    "task_id": coordination_task.id,
                    "collaboration_goals": collaboration_goals,
                    "primary_agent": primary_agent,
                    "task_description": task_description
                },
                task_id=coordination_task.id,
                priority=TaskPriority.HIGH
            )
            coordination_messages.append(message)
        
        # Publish intercommunication event
        await self.event_bus.publish_event("agent.intercommunication", {
            "task_id": coordination_task.id,
            "primary_agent": primary_agent,
            "secondary_agents": secondary_agents,
            "collaboration_goals": collaboration_goals,
            "coordination_messages": [asdict(msg) for msg in coordination_messages],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Intercommunication initiated between {primary_agent} and {secondary_agents}")
        
        return {
            "success": True,
            "task_id": coordination_task.id,
            "coordination_messages": [asdict(msg) for msg in coordination_messages],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def complete_task_with_summary(
        self,
        task_id: str,
        agent_id: str,
        summary: str,
        metrics: Dict[str, Any],
        next_steps: List[str]
    ) -> TaskSummary:
        """Complete a task and generate a summary"""
        if not self._initialized:
            await self.initialize()
        
        if task_id not in self.active_tasks:
            logger.error(f"Task {task_id} not found")
            return None
        
        # Update task status to completed
        await self.update_task_status(task_id, TaskStatus.COMPLETED, progress=100.0)
        
        # Create task summary
        task_summary = TaskSummary(
            task_id=task_id,
            agent_id=agent_id,
            summary=summary,
            completed_at=datetime.utcnow(),
            metrics=metrics,
            next_steps=next_steps
        )
        
        self.task_summaries[task_id] = task_summary
        
        # Publish task completion event
        await self.event_bus.publish_event("agent.task_complete", {
            "task_summary": asdict(task_summary),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Task {task_id} completed by {agent_id}")
        return task_summary
    
    async def get_user_tasks(self, user_id: int) -> List[Task]:
        """Get all tasks for a user"""
        if not self._initialized:
            await self.initialize()
        
        user_tasks = [task for task in self.active_tasks.values() if task.user_id == user_id]
        return sorted(user_tasks, key=lambda x: x.created_at, reverse=True)
    
    async def get_task_summaries(self, user_id: int) -> List[TaskSummary]:
        """Get task summaries for a user"""
        if not self._initialized:
            await self.initialize()
        
        user_task_ids = [task.id for task in self.active_tasks.values() if task.user_id == user_id]
        user_summaries = [summary for task_id, summary in self.task_summaries.items() if task_id in user_task_ids]
        return sorted(user_summaries, key=lambda x: x.completed_at, reverse=True)
    
    async def _handle_agent_message(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle incoming agent messages"""
        try:
            message_data = event_data.get("data", {})
            message = message_data.get("message", {})
            
            # Process the message based on type
            message_type = message.get("message_type")
            if message_type == "coordination_request":
                await self._handle_coordination_request(message)
            elif message_type == "task_update":
                await self._handle_task_update_message(message)
            elif message_type == "collaboration_response":
                await self._handle_collaboration_response(message)
            
        except Exception as e:
            logger.error(f"Error handling agent message: {e}")
    
    async def _handle_task_update(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task update events"""
        try:
            task_data = event_data.get("data", {})
            task_id = task_data.get("task_id")
            
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus(task_data.get("status", task.status.value))
                task.progress = task_data.get("progress", task.progress)
                task.updated_at = datetime.utcnow()
                
                if task_data.get("metadata"):
                    task.metadata.update(task_data["metadata"])
                
                logger.info(f"Task {task_id} updated via event")
        
        except Exception as e:
            logger.error(f"Error handling task update: {e}")
    
    async def _handle_task_completion(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle task completion events"""
        try:
            summary_data = event_data.get("data", {})
            task_summary = summary_data.get("task_summary", {})
            
            task_id = task_summary.get("task_id")
            if task_id:
                # Store the summary
                summary = TaskSummary(
                    task_id=task_summary["task_id"],
                    agent_id=task_summary["agent_id"],
                    summary=task_summary["summary"],
                    completed_at=datetime.fromisoformat(task_summary["completed_at"]),
                    metrics=task_summary["metrics"],
                    next_steps=task_summary["next_steps"]
                )
                self.task_summaries[task_id] = summary
                
                logger.info(f"Task {task_id} completion summary received")
        
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    async def _handle_intercommunication(self, event_data: Dict[str, Any], event_key: str, topic: str):
        """Handle intercommunication events"""
        try:
            intercomm_data = event_data.get("data", {})
            task_id = intercomm_data.get("task_id")
            primary_agent = intercomm_data.get("primary_agent")
            secondary_agents = intercomm_data.get("secondary_agents", [])
            
            logger.info(f"Intercommunication event received for task {task_id}")
            
            # Update task metadata with intercommunication info
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.metadata.update({
                    "intercommunication_active": True,
                    "primary_agent": primary_agent,
                    "secondary_agents": secondary_agents,
                    "last_intercomm_update": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error handling intercommunication: {e}")
    
    async def _handle_coordination_request(self, message: Dict[str, Any]):
        """Handle coordination requests between agents"""
        # This would be implemented by individual agents
        pass
    
    async def _handle_task_update_message(self, message: Dict[str, Any]):
        """Handle task update messages"""
        # This would be implemented by individual agents
        pass
    
    async def _handle_collaboration_response(self, message: Dict[str, Any]):
        """Handle collaboration responses"""
        # This would be implemented by individual agents
        pass

# Global intercommunication service instance
intercommunication_service = IntercommunicationService()

async def get_intercommunication_service() -> IntercommunicationService:
    return intercommunication_service

async def init_intercommunication():
    await intercommunication_service.initialize()

async def close_intercommunication():
    # Cleanup if needed
    pass
