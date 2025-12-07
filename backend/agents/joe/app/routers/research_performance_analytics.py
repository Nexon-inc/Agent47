"""
Research Performance Analytics Router

This router handles performance metrics and analytics endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.research_performance_analytics_service import ResearchPerformanceAnalyticsService

router = APIRouter(prefix="/research-performance-analytics", tags=["Research Performance Analytics"])

class PerformanceReportRequest(BaseModel):
    report_config: Dict[str, Any] = Field(..., description="Configuration for performance report generation")

class MetricsTrackingRequest(BaseModel):
    metrics_data: Dict[str, Any] = Field(..., description="Performance metrics data to track")

# Dependency
async def get_research_performance_analytics_service() -> ResearchPerformanceAnalyticsService:
    service = ResearchPerformanceAnalyticsService()
    await service.initialize()
    return service

@router.post("/generate-report")
async def generate_performance_report(
    request: PerformanceReportRequest,
    service: ResearchPerformanceAnalyticsService = Depends(get_research_performance_analytics_service)
):
    """Generate comprehensive research performance report"""
    try:
        result = await service.generate_performance_report(
            user_id=1,  # TODO: Get from authentication
            report_config=request.report_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["report_data"],
                "message": "Performance report generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )

@router.post("/track-metrics")
async def track_research_metrics(
    request: MetricsTrackingRequest,
    service: ResearchPerformanceAnalyticsService = Depends(get_research_performance_analytics_service)
):
    """Track and update research performance metrics"""
    try:
        result = await service.track_research_metrics(
            user_id=1,  # TODO: Get from authentication
            metrics_data=request.metrics_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["tracking_data"],
                "message": "Performance metrics tracked successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Metrics tracking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track metrics: {str(e)}"
        )

@router.get("/metric-types")
async def get_available_metric_types(service: ResearchPerformanceAnalyticsService = Depends(get_research_performance_analytics_service)):
    """Get available performance metric types for tracking"""
    metric_types = [
        {
            "id": "efficiency",
            "name": "Efficiency Metrics",
            "description": "Measure research process efficiency",
            "metrics": ["data_collection_speed", "analysis_time", "insight_generation_speed"],
            "units": ["% improvement", "minutes", "insights/hour"]
        },
        {
            "id": "quality",
            "name": "Quality Metrics",
            "description": "Measure research output quality",
            "metrics": ["data_accuracy", "insight_relevance", "stakeholder_satisfaction"],
            "units": ["%", "score", "rating"]
        },
        {
            "id": "productivity",
            "name": "Productivity Metrics",
            "description": "Measure research output quantity",
            "metrics": ["projects_completed", "tasks_finished", "reports_generated"],
            "units": ["count", "count", "count"]
        },
        {
            "id": "automation",
            "name": "Automation Metrics",
            "description": "Measure automation adoption and effectiveness",
            "metrics": ["automation_rate", "time_saved", "error_reduction"],
            "units": ["%", "hours", "%"]
        },
        {
            "id": "collaboration",
            "name": "Collaboration Metrics",
            "description": "Measure team collaboration effectiveness",
            "metrics": ["team_coordination", "knowledge_sharing", "cross_functional_work"],
            "units": ["score", "score", "score"]
        }
    ]
    
    return {
        "status": "success",
        "data": metric_types,
        "message": f"Retrieved {len(metric_types)} metric type categories"
    }
