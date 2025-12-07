"""
User Admin Panel Router
Provides comprehensive dashboard for users to view their agent activity and data
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database.connection import get_db
from ..database.models import User, UserSelectedAgent, Task, TaskStatus, UserAnalytics
from ..authentication.auth_manager import get_current_active_user
from ..analytics.analytics_service import AnalyticsService, get_analytics_service
from ..platforms.oauth_service import get_oauth_service
from ..integrations.integration_manager import IntegrationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user-admin", tags=["user-admin"])

@router.get("/dashboard")
async def get_user_admin_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive user admin dashboard data"""
    try:
        # Get selected agents
        agents_result = await db.execute(
            select(UserSelectedAgent).where(UserSelectedAgent.user_id == current_user.id)
        )
        selected_agents = agents_result.scalars().all()
        
        # Get task statistics
        tasks_result = await db.execute(
            select(
                Task.agent_id,
                func.count(Task.id).label("total_tasks"),
                func.sum(func.cast(Task.status == TaskStatus.COMPLETED, int)).label("completed_tasks"),
                func.sum(func.cast(Task.status == TaskStatus.FAILED, int)).label("failed_tasks")
            ).where(
                Task.user_id == current_user.id
            ).group_by(Task.agent_id)
        )
        task_stats = tasks_result.all()
        
        # Get analytics summary
        analytics_summary = await analytics_service.get_user_analytics(
            user_id=current_user.id,
            period_days=30
        )
        
        # Get platform connections
        oauth_service = await get_oauth_service()
        platforms = await oauth_service.get_user_platforms(current_user.id)
        
        # Get integrations
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        integrations = await integration_manager.get_user_integration_usage(current_user.id)
        
        # Build agent details
        agent_details = []
        for agent in selected_agents:
            # Get task stats for this agent
            agent_task_stats = next(
                (stat for stat in task_stats if stat.agent_id == agent.agent_key),
                None
            )
            
            # Get recent tasks
            recent_tasks_result = await db.execute(
                select(Task).where(
                    and_(
                        Task.user_id == current_user.id,
                        Task.agent_id == agent.agent_key
                    )
                ).order_by(Task.created_at.desc()).limit(5)
            )
            recent_tasks = recent_tasks_result.scalars().all()
            
            agent_details.append({
                "agent_key": agent.agent_key,
                "status": agent.status,
                "automation_enabled": agent.automation_enabled,
                "configuration": agent.configuration or {},
                "statistics": {
                    "total_tasks": agent_task_stats.total_tasks if agent_task_stats else 0,
                    "completed_tasks": agent_task_stats.completed_tasks if agent_task_stats else 0,
                    "failed_tasks": agent_task_stats.failed_tasks if agent_task_stats else 0,
                    "success_rate": (
                        (agent_task_stats.completed_tasks / agent_task_stats.total_tasks * 100)
                        if agent_task_stats and agent_task_stats.total_tasks > 0 else 0
                    )
                },
                "recent_tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status.value,
                        "priority": task.priority.value if task.priority else "medium",
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None
                    }
                    for task in recent_tasks
                ]
            })
        
        return {
            "success": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "tier": current_user.tier.value if current_user.tier else "free"
            },
            "agents": agent_details,
            "analytics": {
                "total_tasks": analytics_summary.total_tasks,
                "completed_tasks": analytics_summary.completed_tasks,
                "success_rate": analytics_summary.success_rate,
                "average_response_time": analytics_summary.average_response_time,
                "total_engagement": analytics_summary.total_engagement,
                "roi_percentage": analytics_summary.roi_percentage,
                "user_satisfaction": analytics_summary.user_satisfaction,
                "agent_breakdown": analytics_summary.agent_breakdown
            },
            "platforms": {
                "connected": len([p for p in platforms if p.get("status") == "active"]),
                "total": len(platforms),
                "list": [
                    {
                        "platform_name": p.get("platform_name"),
                        "display_name": p.get("display_name"),
                        "status": p.get("status"),
                        "connected_at": p.get("connected_at")
                    }
                    for p in platforms
                ]
            },
            "integrations": {
                "active": len([i for i in integrations if i.status.value == "active"]),
                "total": len(integrations),
                "list": [
                    {
                        "integration_name": i.integration_name,
                        "status": i.status.value,
                        "credentials_status": i.credentials_status.value,
                        "last_used": i.last_used.isoformat() if i.last_used else None
                    }
                    for i in integrations
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user admin dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )

@router.get("/agents/{agent_key}/details")
async def get_agent_details(
    agent_key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed information about a specific agent"""
    try:
        # Verify agent is selected by user
        agent_result = await db.execute(
            select(UserSelectedAgent).where(
                and_(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == agent_key
                )
            )
        )
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or not selected"
            )
        
        # Get all tasks for this agent
        tasks_result = await db.execute(
            select(Task).where(
                and_(
                    Task.user_id == current_user.id,
                    Task.agent_id == agent_key
                )
            ).order_by(Task.created_at.desc())
        )
        all_tasks = tasks_result.scalars().all()
        
        # Get task statistics
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
        pending_tasks = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
        in_progress_tasks = len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS])
        
        # Get analytics for this agent
        agent_analytics = await analytics_service.get_user_analytics(
            user_id=current_user.id,
            period_days=30,
            agent_id=agent_key
        )
        
        return {
            "success": True,
            "agent": {
                "agent_key": agent.agent_key,
                "status": agent.status,
                "automation_enabled": agent.automation_enabled,
                "configuration": agent.configuration or {},
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            },
            "statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_tasks": pending_tasks,
                "in_progress_tasks": in_progress_tasks,
                "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "analytics": {
                "total_tasks": agent_analytics.total_tasks,
                "completed_tasks": agent_analytics.completed_tasks,
                "success_rate": agent_analytics.success_rate,
                "average_response_time": agent_analytics.average_response_time,
                "total_engagement": agent_analytics.total_engagement
            },
            "recent_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value if task.priority else "medium",
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "metadata": task.metadata or {}
                }
                for task in all_tasks[:20]  # Last 20 tasks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent details: {str(e)}"
        )

@router.get("/tasks")
async def get_user_tasks(
    agent_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's tasks with optional filtering"""
    try:
        query = select(Task).where(Task.user_id == current_user.id)
        
        if agent_key:
            query = query.where(Task.agent_id == agent_key)
        
        if status:
            try:
                task_status = TaskStatus(status)
                query = query.where(Task.status == task_status)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        query = query.order_by(Task.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return {
            "success": True,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "agent_id": task.agent_id,
                    "status": task.status.value,
                    "priority": task.priority.value if task.priority else "medium",
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "metadata": task.metadata or {}
                }
                for task in tasks
            ],
            "total": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )

@router.get("/analytics")
async def get_user_analytics(
    period_days: int = 30,
    agent_key: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get user analytics data"""
    try:
        analytics = await analytics_service.get_user_analytics(
            user_id=current_user.id,
            period_days=period_days,
            agent_id=agent_key
        )
        
        return {
            "success": True,
            "analytics": {
                "total_tasks": analytics.total_tasks,
                "completed_tasks": analytics.completed_tasks,
                "success_rate": analytics.success_rate,
                "average_response_time": analytics.average_response_time,
                "total_engagement": analytics.total_engagement,
                "roi_percentage": analytics.roi_percentage,
                "user_satisfaction": analytics.user_satisfaction,
                "period_start": analytics.period_start,
                "period_end": analytics.period_end,
                "agent_breakdown": analytics.agent_breakdown
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

