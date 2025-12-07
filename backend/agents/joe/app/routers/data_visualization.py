from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.data_visualization_service import DataVisualizationService

router = APIRouter(prefix="/data-visualization", tags=["Data Visualization"])

class VisualizationRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to visualize")
    chart_type: str = Field(default="bar", description="Type of chart to create")
    title: str = Field(None, description="Chart title")

# Dependency
async def get_data_visualization_service() -> DataVisualizationService:
    service = DataVisualizationService()
    await service.initialize()
    return service

@router.post("/create")
async def create_visualization(
    request: VisualizationRequest,
    service: DataVisualizationService = Depends(get_data_visualization_service)
):
    """Create data visualization"""
    try:
        result = await service.create_visualization(
            user_id=1,  # TODO: Get from authentication
            data=request.data,
            chart_type=request.chart_type,
            title=request.title
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["visualization"],
                "message": f"Visualization created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Visualization creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visualization: {str(e)}"
        )

@router.get("/templates")
async def get_visualization_templates(
    category: str = "general",
    service: DataVisualizationService = Depends(get_data_visualization_service)
):
    """Get visualization templates"""
    try:
        result = await service.get_visualization_templates(
            user_id=1,  # TODO: Get from authentication
            category=category
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["templates"],
                "message": f"Retrieved {result['total_templates']} visualization templates"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get templates: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get templates: {str(e)}"
        )

@router.get("/chart-types")
async def get_available_chart_types(service: DataVisualizationService = Depends(get_data_visualization_service)):
    """Get available chart types"""
    chart_types = [
        {
            "type": "bar",
            "name": "Bar Chart",
            "description": "Vertical or horizontal bars",
            "best_for": "Comparing categories"
        },
        {
            "type": "line",
            "name": "Line Chart",
            "description": "Connected data points",
            "best_for": "Showing trends over time"
        },
        {
            "type": "pie",
            "name": "Pie Chart",
            "description": "Circular segments",
            "best_for": "Showing proportions"
        },
        {
            "type": "scatter",
            "name": "Scatter Plot",
            "description": "Data points on x-y axis",
            "best_for": "Showing correlations"
        }
    ]
    
    return {
        "status": "success",
        "data": chart_types,
        "message": f"Retrieved {len(chart_types)} chart types"
    }
