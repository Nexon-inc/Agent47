from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.collaborative_workflows_service import CollaborativeWorkflowsService

router = APIRouter(prefix="/collaborative-workflows", tags=["Collaborative Workflows"])

class WorkflowCreationRequest(BaseModel):
    workflow_config: Dict[str, Any] = Field(..., description="Workflow configuration")

class PermissionUpdateRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID for permission updates")
    permission_updates: Dict[str, Any] = Field(..., description="Permission updates to apply")

# Dependency
async def get_collaborative_workflows_service() -> CollaborativeWorkflowsService:
    service = CollaborativeWorkflowsService()
    await service.initialize()
    return service

@router.post("/create-workflow")
async def create_collaborative_workflow(
    request: WorkflowCreationRequest,
    service: CollaborativeWorkflowsService = Depends(get_collaborative_workflows_service)
):
    """Create a new collaborative research workflow"""
    try:
        result = await service.create_collaborative_workflow(
            user_id=1,  # TODO: Get from authentication
            workflow_config=request.workflow_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["workflow_data"],
                "message": "Collaborative workflow created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collaborative workflow: {str(e)}"
        )

@router.post("/manage-permissions")
async def manage_collaboration_permissions(
    request: PermissionUpdateRequest,
    service: CollaborativeWorkflowsService = Depends(get_collaborative_workflows_service)
):
    """Manage collaboration permissions for a workflow"""
    try:
        result = await service.manage_collaboration_permissions(
            user_id=1,  # TODO: Get from authentication
            workflow_id=request.workflow_id,
            permission_updates=request.permission_updates
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["permission_data"],
                "message": "Collaboration permissions updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Permission management failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to manage collaboration permissions: {str(e)}"
        )

@router.get("/workflow-templates")
async def get_workflow_templates(service: CollaborativeWorkflowsService = Depends(get_collaborative_workflows_service)):
    """Get available collaborative workflow templates"""
    templates = [
        {
            "id": "market_research",
            "name": "Market Research Collaboration",
            "description": "Multi-team market research workflow",
            "stages": ["Planning", "Data Collection", "Analysis", "Reporting"],
            "estimated_duration": "4-6 weeks",
            "team_size": "3-8 members"
        },
        {
            "id": "competitive_analysis",
            "name": "Competitive Analysis",
            "description": "Collaborative competitor research workflow",
            "stages": ["Competitor Identification", "Data Gathering", "Analysis", "Strategy"],
            "estimated_duration": "2-4 weeks",
            "team_size": "2-5 members"
        },
        {
            "id": "product_research",
            "name": "Product Research",
            "description": "Product development research collaboration",
            "stages": ["User Research", "Market Analysis", "Prototyping", "Validation"],
            "estimated_duration": "6-8 weeks",
            "team_size": "4-10 members"
        },
        {
            "id": "trend_analysis",
            "name": "Trend Analysis",
            "description": "Collaborative trend monitoring workflow",
            "stages": ["Trend Detection", "Data Collection", "Analysis", "Forecasting"],
            "estimated_duration": "3-5 weeks",
            "team_size": "2-6 members"
        }
    ]
    
    return {
        "status": "success",
        "data": templates,
        "message": f"Retrieved {len(templates)} workflow templates"
    }
