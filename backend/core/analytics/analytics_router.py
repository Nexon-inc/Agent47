from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import logging

from ..database.connection import get_db
from ..database.models import (
    User,
    Task,
    TaskStatus,
    Agent,
    Event,
    EventType,
    IntegrationAuditLog,
)
from ..authentication.auth_manager import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    try:
        # Task counts by status
        from sqlalchemy import select
        status_counts_result = await db.execute(
            select(Task.status, func.count(Task.id))
            .filter(Task.user_id == current_user.id)
            .group_by(Task.status)
        )
        status_counts = status_counts_result.all()
        counts_map = {status.value: count for status, count in status_counts}
        total_tasks = sum(counts_map.values())
        completed = counts_map.get(TaskStatus.COMPLETED.value, 0)
        failed = counts_map.get(TaskStatus.FAILED.value, 0)
        success_rate = (completed / total_tasks) * 100 if total_tasks > 0 else 0.0

        # Recent events (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_events_result = await db.execute(
            select(func.count(Event.id))
            .join(Task, Task.id == Event.task_id)
            .filter(and_(Task.user_id == current_user.id, Event.timestamp >= week_ago))
        )
        recent_events = recent_events_result.scalar()

        return {
            "tasks": counts_map,
            "total_tasks": total_tasks,
            "success_rate": round(success_rate, 2),
            "recent_events": recent_events or 0,
        }
    except Exception as e:
        logger.error(f"Analytics summary error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/tasks/overview")
async def tasks_overview(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    try:
        # Tasks created per day for last 7 days
        start_date = datetime.utcnow() - timedelta(days=6)
        per_day_result = await db.execute(
            select(func.date_trunc('day', Task.created_at).label('day'), func.count(Task.id))
            .filter(and_(Task.user_id == current_user.id, Task.created_at >= start_date))
            .group_by('day')
            .order_by('day')
        )
        per_day = per_day_result.all()
        return {"per_day": [{"day": d.isoformat(), "count": c} for d, c in per_day]}
    except Exception as e:
        logger.error(f"Tasks overview error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/agents/usage")
async def agents_usage(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    try:
        rows_result = await db.execute(
            select(Agent.name, func.count(Task.id))
            .join(Task, Task.agent_id == Agent.id)
            .filter(Task.user_id == current_user.id)
            .group_by(Agent.name)
            .order_by(desc(func.count(Task.id)))
        )
        rows = rows_result.all()
        return {"agents": [{"name": name, "tasks": count} for name, count in rows]}
    except Exception as e:
        logger.error(f"Agents usage error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/integrations/usage")
async def integrations_usage(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    try:
        last_30 = datetime.utcnow() - timedelta(days=30)
        rows_result = await db.execute(
            select(IntegrationAuditLog.integration_name, func.count(IntegrationAuditLog.id))
            .filter(and_(IntegrationAuditLog.user_id == current_user.id, IntegrationAuditLog.timestamp >= last_30))
            .group_by(IntegrationAuditLog.integration_name)
            .order_by(desc(func.count(IntegrationAuditLog.id)))
        )
        rows = rows_result.all()
        return {"integrations": [{"name": name, "events": count} for name, count in rows]}
    except Exception as e:
        logger.error(f"Integrations usage error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from .analytics_service import (
    get_analytics_service,
    AnalyticsService,
    MetricType,
    TimePeriod
)
from ..authentication.auth_manager import get_current_user
from ..user_management.user_manager import User

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

class AnalyticsSummaryResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    success_rate: float
    average_response_time: float
    total_engagement: float
    roi_percentage: float
    user_satisfaction: float
    period_start: datetime
    period_end: datetime
    agent_breakdown: Dict[str, Dict[str, Any]]

class ChartDataResponse(BaseModel):
    date: str
    value: float
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UsageDistributionResponse(BaseModel):
    name: str
    value: int
    percentage: float
    color: str

class DetailedDataResponse(BaseModel):
    id: str
    task: str
    agent: str
    engagement: str
    response_time: str
    roi: str
    satisfaction: str
    date: str
    status: str

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    period_days: int = Query(30, description="Number of days to analyze"),
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics summary for a user"""
    try:
        summary = await analytics_service.get_user_analytics(
            user_id=current_user.id,
            period_days=period_days,
            agent_id=agent_id
        )
        
        return AnalyticsSummaryResponse(
            total_tasks=summary.total_tasks,
            completed_tasks=summary.completed_tasks,
            success_rate=summary.success_rate,
            average_response_time=summary.average_response_time,
            total_engagement=summary.total_engagement,
            roi_percentage=summary.roi_percentage,
            user_satisfaction=summary.user_satisfaction,
            period_start=summary.period_start,
            period_end=summary.period_end,
            agent_breakdown=summary.agent_breakdown
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}"
        )

@router.get("/chart-data", response_model=List[ChartDataResponse])
async def get_chart_data(
    metric_type: str = Query(..., description="Type of metric to analyze"),
    period_days: int = Query(30, description="Number of days to analyze"),
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    group_by: str = Query("day", description="Group data by day, week, or month"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get chart data for analytics visualization"""
    try:
        # Validate metric type
        try:
            metric_enum = MetricType(metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric type: {metric_type}"
            )
        
        # Validate group_by
        try:
            period_enum = TimePeriod(group_by.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid group_by: {group_by}"
            )
        
        chart_data = await analytics_service.get_chart_data(
            user_id=current_user.id,
            metric_type=metric_enum,
            period_days=period_days,
            agent_id=agent_id,
            group_by=period_enum
        )
        
        return [
            ChartDataResponse(
                date=point.date,
                value=point.value,
                agent_id=point.agent_id,
                metadata=point.metadata
            )
            for point in chart_data
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart data: {str(e)}"
        )

@router.get("/usage-distribution", response_model=List[UsageDistributionResponse])
async def get_usage_distribution(
    period_days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get usage distribution across agents"""
    try:
        distribution = await analytics_service.get_usage_distribution(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return [
            UsageDistributionResponse(
                name=item["name"],
                value=item["value"],
                percentage=item["percentage"],
                color=item["color"]
            )
            for item in distribution
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage distribution: {str(e)}"
        )

@router.get("/detailed-data", response_model=List[DetailedDataResponse])
async def get_detailed_data(
    period_days: int = Query(30, description="Number of days to analyze"),
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed analytics data for tables"""
    try:
        detailed_data = await analytics_service.get_detailed_data(
            user_id=current_user.id,
            period_days=period_days,
            agent_id=agent_id,
            limit=limit
        )
        
        return [
            DetailedDataResponse(
                id=item["id"],
                task=item["task"],
                agent=item["agent"],
                engagement=item["engagement"],
                response_time=item["response_time"],
                roi=item["roi"],
                satisfaction=item["satisfaction"],
                date=item["date"],
                status=item["status"]
            )
            for item in detailed_data
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed data: {str(e)}"
        )

@router.post("/generate-mock-data")
async def generate_mock_data(
    days: int = Query(30, description="Number of days of mock data to generate"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate mock analytics data for demonstration"""
    try:
        await analytics_service.generate_mock_data(
            user_id=current_user.id,
            days=days
        )
        
        return {
            "success": True,
            "message": f"Generated {days} days of mock analytics data",
            "user_id": current_user.id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mock data: {str(e)}"
        )

@router.post("/record-metric")
async def record_metric(
    agent_id: str,
    metric_type: str,
    value: float,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Record a new analytics metric"""
    try:
        # Validate metric type
        try:
            metric_enum = MetricType(metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric type: {metric_type}"
            )
        
        metric = await analytics_service.record_metric(
            user_id=current_user.id,
            agent_id=agent_id,
            metric_type=metric_enum,
            value=value,
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "metric_id": metric.id,
            "message": "Metric recorded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record metric: {str(e)}"
        )

@router.get("/export")
async def export_analytics(
    period_days: int = Query(30, description="Number of days to export"),
    format: str = Query("csv", description="Export format (csv, json)"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Export analytics data"""
    try:
        if format not in ["csv", "json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'csv' or 'json'"
            )
        
        # Get detailed data
        detailed_data = await analytics_service.get_detailed_data(
            user_id=current_user.id,
            period_days=period_days,
            limit=10000  # Large limit for export
        )
        
        if format == "json":
            return {
                "data": detailed_data,
                "exported_at": datetime.utcnow().isoformat(),
                "period_days": period_days,
                "total_records": len(detailed_data)
            }
        else:  # CSV format
            import csv
            import io
            
            output = io.StringIO()
            if detailed_data:
                writer = csv.DictWriter(output, fieldnames=detailed_data[0].keys())
                writer.writeheader()
                writer.writerows(detailed_data)
            
            return {
                "csv_data": output.getvalue(),
                "exported_at": datetime.utcnow().isoformat(),
                "period_days": period_days,
                "total_records": len(detailed_data)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics: {str(e)}"
        )
