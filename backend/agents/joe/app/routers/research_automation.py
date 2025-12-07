from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.research_automation_service import ResearchAutomationService

router = APIRouter(prefix="/research-automation", tags=["Research Automation"])

class WorkflowCreationRequest(BaseModel):
    workflow_config: Dict[str, Any] = Field(..., description="Workflow configuration")

class ResearchTaskRequest(BaseModel):
    research_task: Dict[str, Any] = Field(..., description="Research task to execute")

# Dependency
async def get_research_automation_service() -> ResearchAutomationService:
    service = ResearchAutomationService()
    await service.initialize()
    return service

@router.post("/create-workflow")
async def create_research_workflow(
    request: WorkflowCreationRequest,
    service: ResearchAutomationService = Depends(get_research_automation_service)
):
    """Create an automated research workflow"""
    try:
        result = await service.create_research_workflow(
            user_id=1,  # TODO: Get from authentication
            workflow_config=request.workflow_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["workflow_data"],
                "message": "Research workflow created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research workflow: {str(e)}"
        )

@router.post("/execute-research")
async def execute_automated_research(
    request: ResearchTaskRequest,
    service: ResearchAutomationService = Depends(get_research_automation_service)
):
    """Execute an automated research task"""
    try:
        result = await service.execute_automated_research(
            user_id=1,  # TODO: Get from authentication
            research_task=request.research_task
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["execution_data"],
                "message": "Automated research executed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research execution failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute automated research: {str(e)}"
        )

@router.get("/workflow-templates")
async def get_workflow_templates(service: ResearchAutomationService = Depends(get_research_automation_service)):
    """Get available workflow templates"""
    templates = [
        {
            "id": "market_research",
            "name": "Market Research",
            "description": "Automated market research workflow",
            "steps": ["Data Collection", "Analysis", "Reporting"],
            "schedule": "Daily",
            "estimated_time": "2 hours/week"
        },
        {
            "id": "competitor_monitoring",
            "name": "Competitor Monitoring",
            "description": "Automated competitor tracking workflow",
            "steps": ["Competitor Tracking", "Alert Generation", "Report Creation"],
            "schedule": "Daily",
            "estimated_time": "1 hour/week"
        },
        {
            "id": "trend_analysis",
            "name": "Trend Analysis",
            "description": "Automated trend monitoring workflow",
            "steps": ["Trend Detection", "Analysis", "Forecasting"],
            "schedule": "Weekly",
            "estimated_time": "3 hours/week"
        },
        {
            "id": "sentiment_tracking",
            "name": "Sentiment Tracking",
            "description": "Automated sentiment analysis workflow",
            "steps": ["Data Collection", "Sentiment Analysis", "Reporting"],
            "schedule": "Daily",
            "estimated_time": "1.5 hours/week"
        }
    ]
    
    return {
        "status": "success",
        "data": templates,
        "message": f"Retrieved {len(templates)} workflow templates"
    }
