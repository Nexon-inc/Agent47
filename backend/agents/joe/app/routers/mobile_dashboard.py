from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.mobile_dashboard_service import MobileDashboardService

router = APIRouter(prefix="/mobile-dashboard", tags=["Mobile Dashboard"])

class DashboardDataRequest(BaseModel):
    dashboard_type: str = Field(default="overview", description="Type of dashboard to retrieve")

class LayoutCustomizationRequest(BaseModel):
    layout_preferences: Dict[str, Any] = Field(..., description="Layout customization preferences")

# Dependency
async def get_mobile_dashboard_service() -> MobileDashboardService:
    service = MobileDashboardService()
    await service.initialize()
    return service

@router.post("/get-dashboard")
async def get_mobile_dashboard_data(
    request: DashboardDataRequest,
    service: MobileDashboardService = Depends(get_mobile_dashboard_service)
):
    """Get mobile-optimized dashboard data"""
    try:
        result = await service.get_mobile_dashboard_data(
            user_id=1,  # TODO: Get from authentication
            dashboard_type=request.dashboard_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["dashboard_data"],
                "message": "Mobile dashboard data retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dashboard data retrieval failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mobile dashboard data: {str(e)}"
        )

@router.post("/customize-layout")
async def customize_mobile_layout(
    request: LayoutCustomizationRequest,
    service: MobileDashboardService = Depends(get_mobile_dashboard_service)
):
    """Customize mobile dashboard layout"""
    try:
        result = await service.customize_mobile_layout(
            user_id=1,  # TODO: Get from authentication
            layout_preferences=request.layout_preferences
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["layout_data"],
                "message": "Mobile dashboard layout customized successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Layout customization failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to customize mobile layout: {str(e)}"
        )

@router.get("/dashboard-types")
async def get_available_dashboard_types(service: MobileDashboardService = Depends(get_mobile_dashboard_service)):
    """Get available mobile dashboard types"""
    dashboard_types = [
        {
            "id": "overview",
            "name": "Overview Dashboard",
            "description": "High-level summary of all research activities",
            "widgets": ["Quick Stats", "Recent Insights", "Performance Chart"],
            "suitable_for": "Daily monitoring"
        },
        {
            "id": "project_focused",
            "name": "Project Dashboard",
            "description": "Detailed view of specific research projects",
            "widgets": ["Project Timeline", "Task Progress", "Team Activity"],
            "suitable_for": "Project management"
        },
        {
            "id": "analytics",
            "name": "Analytics Dashboard",
            "description": "Data-driven insights and performance metrics",
            "widgets": ["Trend Charts", "KPI Metrics", "Data Tables"],
            "suitable_for": "Data analysis"
        },
        {
            "id": "collaboration",
            "name": "Collaboration Dashboard",
            "description": "Team collaboration and communication tools",
            "widgets": ["Team Chat", "Shared Documents", "Meeting Schedule"],
            "suitable_for": "Team coordination"
        }
    ]
    
    return {
        "status": "success",
        "data": dashboard_types,
        "message": f"Retrieved {len(dashboard_types)} dashboard types"
    }
