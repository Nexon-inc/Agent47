from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from ..services.sales_funnel_service import SalesFunnelService, FunnelStage, FunnelMetrics
from ..database import get_eric_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/funnel", tags=["Sales Funnel Management"])

# Request/Response Models
class FunnelStageCreate(BaseModel):
    name: str = Field(..., description="Stage name")
    description: str = Field(..., description="Stage description")
    position: int = Field(..., description="Stage position in funnel")
    conversion_rate: float = Field(0.0, description="Expected conversion rate")
    avg_days_in_stage: float = Field(0.0, description="Average days in stage")
    is_active: bool = Field(True, description="Whether stage is active")
    color: str = Field("#3B82F6", description="Stage color for visualization")
    criteria: Dict[str, Any] = Field({}, description="Stage qualification criteria")
    automation_rules: List[Dict[str, Any]] = Field([], description="Automation rules for stage")

class FunnelStageUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Stage name")
    description: Optional[str] = Field(None, description="Stage description")
    position: Optional[int] = Field(None, description="Stage position in funnel")
    conversion_rate: Optional[float] = Field(None, description="Expected conversion rate")
    avg_days_in_stage: Optional[float] = Field(None, description="Average days in stage")
    is_active: Optional[bool] = Field(None, description="Whether stage is active")
    color: Optional[str] = Field(None, description="Stage color for visualization")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Stage qualification criteria")
    automation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Automation rules for stage")

class MoveDealRequest(BaseModel):
    deal_id: int = Field(..., description="Deal ID to move")
    new_stage: str = Field(..., description="New stage name")

class AutomationRulesRequest(BaseModel):
    automation_rules: List[Dict[str, Any]] = Field(..., description="Automation rules for the stage")

class DateRangeRequest(BaseModel):
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")

class FunnelVisualizationResponse(BaseModel):
    stages: List[FunnelStage]
    current_data: Dict[str, Dict[str, Any]]
    historical_data: List[Dict[str, Any]]
    generated_at: str

class FunnelOptimizationResponse(BaseModel):
    stage: str
    deal_count: int
    avg_deal_value: float
    activity_breakdown: Dict[str, int]
    recommendations: List[str]
    potential_conversion_improvement: float
    estimated_revenue_impact: float

class FunnelPerformanceReport(BaseModel):
    report_generated_at: str
    date_range: Dict[str, str]
    overall_metrics: FunnelMetrics
    team_performance: List[Dict[str, Any]]
    top_stages: List[Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]

# Service instance
funnel_service = SalesFunnelService()

@router.post("/stages", response_model=FunnelStage, summary="Create Funnel Stage")
async def create_funnel_stage(stage_data: FunnelStageCreate):
    """Create a new funnel stage"""
    try:
        stage = FunnelStage(**stage_data.dict())
        created_stage = await funnel_service.create_funnel_stage(stage)
        return created_stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create funnel stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stages", response_model=List[FunnelStage], summary="Get All Funnel Stages")
async def get_funnel_stages(active_only: bool = Query(True, description="Return only active stages")):
    """Get all funnel stages"""
    try:
        stages = await funnel_service.get_funnel_stages(active_only=active_only)
        return stages
    except Exception as e:
        logger.error(f"Failed to get funnel stages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stages/{stage_id}", response_model=FunnelStage, summary="Get Funnel Stage by ID")
async def get_funnel_stage(stage_id: int):
    """Get a specific funnel stage by ID"""
    try:
        stages = await funnel_service.get_funnel_stages(active_only=False)
        stage = next((s for s in stages if s.id == stage_id), None)
        
        if not stage:
            raise HTTPException(status_code=404, detail="Funnel stage not found")
        
        return stage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get funnel stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/stages/{stage_id}", response_model=FunnelStage, summary="Update Funnel Stage")
async def update_funnel_stage(stage_id: int, stage_data: FunnelStageUpdate):
    """Update a funnel stage"""
    try:
        # Get current stage data
        stages = await funnel_service.get_funnel_stages(active_only=False)
        current_stage = next((s for s in stages if s.id == stage_id), None)
        
        if not current_stage:
            raise HTTPException(status_code=404, detail="Funnel stage not found")
        
        # Update only provided fields
        update_data = stage_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_stage, field, value)
        
        updated_stage = await funnel_service.update_funnel_stage(stage_id, current_stage)
        return updated_stage
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update funnel stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/stages/{stage_id}", summary="Delete Funnel Stage")
async def delete_funnel_stage(stage_id: int):
    """Delete a funnel stage"""
    try:
        success = await funnel_service.delete_funnel_stage(stage_id)
        if success:
            return {"message": "Funnel stage deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete funnel stage")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete funnel stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/metrics", response_model=FunnelMetrics, summary="Get Funnel Metrics")
async def get_funnel_metrics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """Get comprehensive funnel metrics and analytics"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = {"start": start_date, "end": end_date}
        
        metrics = await funnel_service.get_funnel_metrics(date_range)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get funnel metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/deals/move", summary="Move Deal to Stage")
async def move_deal_to_stage(request: MoveDealRequest):
    """Move a deal to a specific funnel stage"""
    try:
        success = await funnel_service.move_deal_to_stage(request.deal_id, request.new_stage)
        if success:
            return {"message": f"Deal {request.deal_id} moved to {request.new_stage} successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to move deal")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to move deal to stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/visualization", response_model=FunnelVisualizationResponse, summary="Get Funnel Visualization")
async def get_funnel_visualization():
    """Get funnel visualization data for charts and graphs"""
    try:
        visualization_data = await funnel_service.get_funnel_visualization()
        return visualization_data
    except Exception as e:
        logger.error(f"Failed to get funnel visualization: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/optimize/{stage_name}", response_model=FunnelOptimizationResponse, summary="Optimize Funnel Stage")
async def optimize_funnel_stage(stage_name: str):
    """Analyze and optimize conversion for a specific funnel stage"""
    try:
        optimization_data = await funnel_service.optimize_funnel_conversion(stage_name)
        
        if "message" in optimization_data:
            raise HTTPException(status_code=404, detail=optimization_data["message"])
        
        return optimization_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize funnel stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/stages/{stage_name}/automation", summary="Create Funnel Automation")
async def create_funnel_automation(stage_name: str, request: AutomationRulesRequest):
    """Create automation rules for a funnel stage"""
    try:
        success = await funnel_service.create_funnel_automation(stage_name, request.automation_rules)
        if success:
            return {"message": f"Automation rules created for stage '{stage_name}' successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create automation rules")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create funnel automation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/performance-report", response_model=FunnelPerformanceReport, summary="Get Funnel Performance Report")
async def get_funnel_performance_report(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """Generate comprehensive funnel performance report"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = {"start": start_date, "end": end_date}
        
        report = await funnel_service.get_funnel_performance_report(date_range)
        return report
    except Exception as e:
        logger.error(f"Failed to generate funnel performance report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stages/{stage_name}/deals", summary="Get Deals in Stage")
async def get_deals_in_stage(
    stage_name: str,
    limit: int = Query(50, description="Number of deals to return"),
    offset: int = Query(0, description="Number of deals to skip")
):
    """Get all deals in a specific funnel stage"""
    try:
        async with get_eric_database() as session:
            from sqlalchemy import select
            from ..models import Deal
            
            deals_query = select(Deal).where(
                Deal.stage == stage_name
            ).limit(limit).offset(offset)
            
            result = await session.execute(deals_query)
            deals = result.scalars().all()
            
            return {
                "stage": stage_name,
                "deals": [
                    {
                        "id": deal.id,
                        "title": deal.title,
                        "value": deal.value,
                        "status": deal.status,
                        "created_at": deal.created_at.isoformat(),
                        "updated_at": deal.updated_at.isoformat() if deal.updated_at else None
                    }
                    for deal in deals
                ],
                "total_count": len(deals)
            }
    except Exception as e:
        logger.error(f"Failed to get deals in stage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health", summary="Funnel Service Health Check")
async def funnel_health_check():
    """Health check for funnel service"""
    try:
        # Test basic functionality
        stages = await funnel_service.get_funnel_stages()
        return {
            "status": "healthy",
            "service": "sales_funnel",
            "stages_count": len(stages),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Funnel service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
