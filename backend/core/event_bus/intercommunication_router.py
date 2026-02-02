from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .intercommunication_service import (
    get_intercommunication_service,
    IntercommunicationService,
    TaskStatus,
    TaskPriority,
    Task,
    TaskSummary
)
from ..authentication.auth_manager import get_current_user
from ..database.models import User, UserTier
from ..database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intercommunication", tags=["intercommunication"])

class TaskCreateRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent creating the task")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    priority: str = Field(default="medium", description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_agents: Optional[List[str]] = Field(None, description="List of assigned agents")
    dependencies: Optional[List[str]] = Field(None, description="Task dependencies")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")

class TaskUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="New task status")
    progress: Optional[float] = Field(None, description="Task progress (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class AgentMessageRequest(BaseModel):
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Destination agent ID")
    message_type: str = Field(..., description="Type of message")
    content: Dict[str, Any] = Field(..., description="Message content")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    priority: str = Field(default="medium", description="Message priority")

class IntercommunicationRequest(BaseModel):
    primary_agent: str = Field(..., description="Primary coordinating agent")
    secondary_agents: List[str] = Field(..., description="Secondary agents to coordinate with")
    task_description: str = Field(..., description="Description of the collaborative task")
    collaboration_goals: List[str] = Field(..., description="Goals for the collaboration")

class TaskSummaryRequest(BaseModel):
    task_id: str = Field(..., description="Task ID to complete")
    agent_id: str = Field(..., description="Agent completing the task")
    summary: str = Field(..., description="Task completion summary")
    metrics: Dict[str, Any] = Field(..., description="Task completion metrics")
    next_steps: List[str] = Field(..., description="Recommended next steps")

class TaskResponse(BaseModel):
    id: str
    user_id: int
    agent_id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    assigned_agents: List[str]
    dependencies: List[str]
    progress: float
    metadata: Dict[str, Any]

class TaskSummaryResponse(BaseModel):
    task_id: str
    agent_id: str
    summary: str
    completed_at: datetime
    metrics: Dict[str, Any]
    next_steps: List[str]

class IntercommunicationToggleRequest(BaseModel):
    enabled: bool

class IntercommunicationToggleResponse(BaseModel):
    enabled: bool
    can_use: bool

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Create a new task for agent coordination"""
    try:
        priority = TaskPriority(request.priority.lower())
        
        task = await intercomm_service.create_task(
            user_id=current_user.id,
            agent_id=request.agent_id,
            title=request.title,
            description=request.description,
            priority=priority,
            due_date=request.due_date,
            assigned_agents=request.assigned_agents,
            dependencies=request.dependencies,
            metadata=request.metadata
        )
        
        # Broadcast task creation via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_task_update
            await broadcast_task_update(current_user.id, {
                "id": task.id,
                "agent_id": task.agent_id,
                "agent_key": task.agent_id,  # For compatibility
                "status": task.status.value,
                "title": task.title,
                "description": task.description,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast task creation: {e}")
        
        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            agent_id=task.agent_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            assigned_agents=task.assigned_agents,
            dependencies=task.dependencies,
            progress=task.progress,
            metadata=task.metadata
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/intercommunication", response_model=IntercommunicationToggleResponse)
async def get_intercommunication_setting(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    can_use = (current_user.tier or UserTier.FREE) in {UserTier.STARTER, UserTier.PRO}
    return IntercommunicationToggleResponse(enabled=bool(current_user.intercommunication_enabled), can_use=can_use)

@router.put("/intercommunication", response_model=IntercommunicationToggleResponse)
async def set_intercommunication_setting(
    req: IntercommunicationToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    can_use = (current_user.tier or UserTier.FREE) in {UserTier.STARTER, UserTier.PRO}
    if not can_use and req.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Intercommunication requires Starter or Pro")
    current_user.intercommunication_enabled = bool(req.enabled)
    await db.commit()
    return IntercommunicationToggleResponse(enabled=current_user.intercommunication_enabled, can_use=can_use)

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Update task status and progress"""
    try:
        status_obj = None
        if request.status:
            status_obj = TaskStatus(request.status.lower())
        
        success = await intercomm_service.update_task_status(
            task_id=task_id,
            status=status_obj,
            progress=request.progress,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Get updated task
        user_tasks = await intercomm_service.get_user_tasks(current_user.id)
        task = next((t for t in user_tasks if t.id == task_id), None)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Broadcast task update via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_task_update
            await broadcast_task_update(current_user.id, {
                "id": task.id,
                "agent_id": task.agent_id,
                "agent_key": task.agent_id,
                "status": task.status.value,
                "title": task.title,
                "description": task.description,
                "progress": task.progress,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast task update: {e}")
        
        return TaskResponse(
            id=task.id,
            user_id=task.user_id,
            agent_id=task.agent_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            assigned_agents=task.assigned_agents,
            dependencies=task.dependencies,
            progress=task.progress,
            metadata=task.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Get all tasks for the current user"""
    try:
        tasks = await intercomm_service.get_user_tasks(current_user.id)
        
        return [
            TaskResponse(
                id=task.id,
                user_id=task.user_id,
                agent_id=task.agent_id,
                title=task.title,
                description=task.description,
                status=task.status.value,
                priority=task.priority.value,
                created_at=task.created_at,
                updated_at=task.updated_at,
                due_date=task.due_date,
                assigned_agents=task.assigned_agents,
                dependencies=task.dependencies,
                progress=task.progress,
                metadata=task.metadata
            )
            for task in tasks
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )

@router.post("/messages")
async def send_agent_message(
    request: AgentMessageRequest,
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Send a message between agents"""
    try:
        priority = TaskPriority(request.priority.lower())
        
        message = await intercomm_service.send_agent_message(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            message_type=request.message_type,
            content=request.content,
            task_id=request.task_id,
            priority=priority
        )
        
        return {
            "success": True,
            "message_id": message.id,
            "timestamp": message.timestamp.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.post("/intercommunication")
async def initiate_intercommunication(
    request: IntercommunicationRequest,
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Initiate intercommunication between multiple agents"""
    try:
        result = await intercomm_service.initiate_intercommunication(
            user_id=current_user.id,
            primary_agent=request.primary_agent,
            secondary_agents=request.secondary_agents,
            task_description=request.task_description,
            collaboration_goals=request.collaboration_goals
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate intercommunication: {str(e)}"
        )

@router.post("/tasks/complete", response_model=TaskSummaryResponse)
async def complete_task_with_summary(
    request: TaskSummaryRequest,
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Complete a task and generate a summary"""
    try:
        task_summary = await intercomm_service.complete_task_with_summary(
            task_id=request.task_id,
            agent_id=request.agent_id,
            summary=request.summary,
            metrics=request.metrics,
            next_steps=request.next_steps
        )
        
        if not task_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Broadcast task completion via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_task_update
            await broadcast_task_update(current_user.id, {
                "id": task_summary.task_id,
                "agent_id": task_summary.agent_id,
                "agent_key": task_summary.agent_id,
                "status": "completed",
                "completed_at": task_summary.completed_at.isoformat() if task_summary.completed_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast task completion: {e}")
        
        return TaskSummaryResponse(
            task_id=task_summary.task_id,
            agent_id=task_summary.agent_id,
            summary=task_summary.summary,
            completed_at=task_summary.completed_at,
            metrics=task_summary.metrics,
            next_steps=task_summary.next_steps
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete task: {str(e)}"
        )

@router.get("/summaries", response_model=List[TaskSummaryResponse])
async def get_task_summaries(
    current_user: User = Depends(get_current_user),
    intercomm_service: IntercommunicationService = Depends(get_intercommunication_service)
):
    """Get task summaries for the current user"""
    try:
        summaries = await intercomm_service.get_task_summaries(current_user.id)
        
        return [
            TaskSummaryResponse(
                task_id=summary.task_id,
                agent_id=summary.agent_id,
                summary=summary.summary,
                completed_at=summary.completed_at,
                metrics=summary.metrics,
                next_steps=summary.next_steps
            )
            for summary in summaries
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task summaries: {str(e)}"
        )
