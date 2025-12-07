from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.research_automation_scheduler_service import ResearchAutomationSchedulerService
from backend.core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/research-automation-scheduler", tags=["Research Automation Scheduler"])

class TaskSchedulingRequest(BaseModel):
    task_config: Dict[str, Any] = Field(..., description="Configuration for the research task")
    schedule_type: str = Field(default="recurring", description="Type of schedule (one-time, recurring)")

class ScheduledTasksRequest(BaseModel):
    status_filter: str = Field(default="all", description="Filter tasks by status")

# Dependencies
async def get_research_automation_scheduler_service() -> ResearchAutomationSchedulerService:
    service = ResearchAutomationSchedulerService()
    await service.initialize()
    return service

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Get current user ID from authentication token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        auth_manager = AuthManager()
        user_data = await auth_manager.verify_token(token)
        return user_data.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

@router.post("/schedule-task")
async def schedule_research_task(
    request: TaskSchedulingRequest,
    service: ResearchAutomationSchedulerService = Depends(get_research_automation_scheduler_service),
    user_id: int = Depends(get_current_user_id)
):
    """Schedule a new automated research task"""
    try:
        result = await service.schedule_research_task(
            user_id=user_id,
            task_config=request.task_config,
            schedule_type=request.schedule_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["scheduled_task"],
                "message": "Research task scheduled successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task scheduling failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule research task: {str(e)}"
        )

@router.post("/get-scheduled-tasks")
async def get_scheduled_tasks(
    request: ScheduledTasksRequest,
    service: ResearchAutomationSchedulerService = Depends(get_research_automation_scheduler_service),
    user_id: int = Depends(get_current_user_id)
):
    """Get user's scheduled research tasks"""
    try:
        result = await service.get_scheduled_tasks(
            user_id=user_id,
            status_filter=request.status_filter
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["scheduled_tasks"],
                "message": "Scheduled tasks retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get scheduled tasks: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduled tasks: {str(e)}"
        )

@router.get("/task-templates")
async def get_task_templates(service: ResearchAutomationSchedulerService = Depends(get_research_automation_scheduler_service)):
    """Get available research task templates"""
    task_templates = [
        {
            "template_id": "competitor_analysis",
            "name": "Competitor Analysis",
            "description": "Automated competitor monitoring and analysis",
            "frequency_options": ["daily", "weekly", "bi_weekly", "monthly"],
            "data_sources": ["web", "social_media", "news", "ads"],
            "output_formats": ["report", "dashboard", "email", "slack"],
            "estimated_duration": "2-4 hours"
        },
        {
            "template_id": "market_trends",
            "name": "Market Trends Monitoring",
            "description": "Track industry trends and market changes",
            "frequency_options": ["daily", "weekly", "bi_weekly"],
            "data_sources": ["news", "social_media", "industry_reports", "google_trends"],
            "output_formats": ["trend_report", "visualization", "alert"],
            "estimated_duration": "1-3 hours"
        },
        {
            "template_id": "news_monitoring",
            "name": "News Monitoring",
            "description": "Monitor industry news and mentions",
            "frequency_options": ["hourly", "daily", "twice_daily"],
            "data_sources": ["news_apis", "rss_feeds", "social_media"],
            "output_formats": ["news_summary", "alert", "digest"],
            "estimated_duration": "30 minutes - 1 hour"
        },
        {
            "template_id": "social_media_listening",
            "name": "Social Media Listening",
            "description": "Monitor brand mentions and conversations",
            "frequency_options": ["hourly", "daily", "real_time"],
            "data_sources": ["twitter", "facebook", "instagram", "linkedin"],
            "output_formats": ["sentiment_report", "mention_summary", "alert"],
            "estimated_duration": "1-2 hours"
        },
        {
            "template_id": "industry_report",
            "name": "Industry Report Generation",
            "description": "Generate comprehensive industry analysis reports",
            "frequency_options": ["weekly", "monthly", "quarterly"],
            "data_sources": ["market_data", "industry_reports", "company_financials"],
            "output_formats": ["pdf_report", "presentation", "executive_summary"],
            "estimated_duration": "4-8 hours"
        }
    ]
    
    return {
        "status": "success",
        "data": task_templates,
        "message": f"Retrieved {len(task_templates)} task templates"
    }
