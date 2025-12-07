from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..services.team_sales_dashboard_service import (
    TeamSalesDashboardService, TeamDashboardMetrics, SalesRepPerformance
)
from ..database import get_db
from backend.core.authentication.auth import get_current_user

router = APIRouter(prefix="/team-sales-dashboard", tags=["Team Sales Dashboard"])

# Initialize service
dashboard_service = TeamSalesDashboardService()


class DashboardExportRequest(BaseModel):
    date_range: str = "30d"
    format: str = "json"


@router.get("/metrics/{team_id}")
async def get_team_dashboard_metrics(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> TeamDashboardMetrics:
    """Get comprehensive team dashboard metrics"""
    try:
        metrics = await dashboard_service.get_team_dashboard_metrics(
            db=db,
            team_id=team_id,
            date_range=date_range
        )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/performance/{team_id}")
async def get_sales_rep_performance(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    sort_by: str = Query("revenue", description="Sort by: revenue, deals_count, conversion_rate, efficiency_score"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[SalesRepPerformance]:
    """Get individual sales rep performance with rankings"""
    try:
        performance = await dashboard_service.get_sales_rep_performance(
            db=db,
            team_id=team_id,
            date_range=date_range,
            sort_by=sort_by
        )
        return performance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance data: {str(e)}")


@router.get("/real-time/{team_id}")
async def get_real_time_updates(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get real-time dashboard updates"""
    try:
        updates = await dashboard_service.get_real_time_updates(
            db=db,
            team_id=team_id
        )
        return updates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time updates: {str(e)}")


@router.get("/pipeline/{team_id}")
async def get_pipeline_analytics(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed pipeline analytics"""
    try:
        analytics = await dashboard_service.get_pipeline_analytics(
            db=db,
            team_id=team_id
        )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline analytics: {str(e)}")


@router.get("/comparison/{team_id}")
async def get_team_comparison(
    team_id: int,
    comparison_period: str = Query("30d", description="Comparison period: 7d, 30d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Compare team performance with previous period"""
    try:
        comparison = await dashboard_service.get_team_comparison(
            db=db,
            team_id=team_id,
            comparison_period=comparison_period
        )
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team comparison: {str(e)}")


@router.post("/export/{team_id}")
async def export_dashboard_data(
    team_id: int,
    export_request: DashboardExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export dashboard data for reporting"""
    try:
        export_result = await dashboard_service.export_dashboard_data(
            db=db,
            team_id=team_id,
            date_range=export_request.date_range,
            format=export_request.format
        )
        return export_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export dashboard data: {str(e)}")


@router.get("/leaderboard/{team_id}")
async def get_team_leaderboard(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    limit: int = Query(10, description="Number of top performers to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get team leaderboard with top performers"""
    try:
        performance = await dashboard_service.get_sales_rep_performance(
            db=db,
            team_id=team_id,
            date_range=date_range,
            sort_by="revenue"
        )
        
        # Get top performers
        top_performers = performance[:limit]
        
        # Calculate team averages
        if performance:
            avg_revenue = sum(p.revenue for p in performance) / len(performance)
            avg_conversion = sum(p.conversion_rate for p in performance) / len(performance)
            avg_efficiency = sum(p.efficiency_score for p in performance) / len(performance)
        else:
            avg_revenue = avg_conversion = avg_efficiency = 0
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "top_performers": [p.dict() for p in top_performers],
            "team_averages": {
                "avg_revenue": avg_revenue,
                "avg_conversion_rate": avg_conversion,
                "avg_efficiency_score": avg_efficiency
            },
            "total_reps": len(performance)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")


@router.get("/trends/{team_id}")
async def get_performance_trends(
    team_id: int,
    metric: str = Query("revenue", description="Metric to analyze: revenue, deals_count, conversion_rate"),
    period: str = Query("30d", description="Analysis period: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get performance trends over time"""
    try:
        # Get comparison data for trend analysis
        comparison = await dashboard_service.get_team_comparison(
            db=db,
            team_id=team_id,
            comparison_period=period
        )
        
        if metric in comparison["changes"]:
            trend_data = comparison["changes"][metric]
            
            return {
                "team_id": team_id,
                "metric": metric,
                "period": period,
                "current_value": trend_data["current"],
                "previous_value": trend_data["previous"],
                "change_percent": trend_data["change_percent"],
                "trend": trend_data["trend"],
                "analysis": {
                    "is_improving": trend_data["trend"] == "up",
                    "change_magnitude": abs(trend_data["change_percent"]),
                    "performance_level": "excellent" if trend_data["change_percent"] > 20 else 
                                       "good" if trend_data["change_percent"] > 10 else
                                       "stable" if trend_data["change_percent"] > -5 else "needs_attention"
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Metric '{metric}' not available")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance trends: {str(e)}")


@router.get("/insights/{team_id}")
async def get_team_insights(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI-powered insights and recommendations"""
    try:
        # Get all dashboard data
        metrics = await dashboard_service.get_team_dashboard_metrics(db, team_id, date_range)
        performance = await dashboard_service.get_sales_rep_performance(db, team_id, date_range)
        pipeline = await dashboard_service.get_pipeline_analytics(db, team_id)
        comparison = await dashboard_service.get_team_comparison(db, team_id, date_range)
        
        # Generate insights
        insights = []
        
        # Revenue insights
        if metrics.total_revenue > 0:
            if metrics.conversion_rate < 10:
                insights.append({
                    "type": "warning",
                    "category": "conversion",
                    "title": "Low Conversion Rate",
                    "description": f"Your conversion rate of {metrics.conversion_rate:.1f}% is below industry average. Consider improving lead qualification.",
                    "priority": "high"
                })
            
            if metrics.response_time_avg > 4:
                insights.append({
                    "type": "warning",
                    "category": "response_time",
                    "title": "Slow Response Times",
                    "description": f"Average response time of {metrics.response_time_avg:.1f} hours may be losing opportunities.",
                    "priority": "medium"
                })
        
        # Performance insights
        if performance:
            top_performer = performance[0]
            bottom_performer = performance[-1]
            
            if top_performer.revenue > 0 and bottom_performer.revenue > 0:
                revenue_gap = (top_performer.revenue - bottom_performer.revenue) / top_performer.revenue * 100
                
                if revenue_gap > 50:
                    insights.append({
                        "type": "info",
                        "category": "performance_gap",
                        "title": "Performance Gap Detected",
                        "description": f"There's a {revenue_gap:.1f}% gap between top and bottom performers. Consider training programs.",
                        "priority": "medium"
                    })
        
        # Pipeline insights
        if pipeline["total_pipeline_value"] > 0:
            pipeline_health = pipeline["total_pipeline_value"] / (metrics.total_revenue * 3)  # 3x pipeline rule
            
            if pipeline_health < 2:
                insights.append({
                    "type": "warning",
                    "category": "pipeline",
                    "title": "Pipeline Health",
                    "description": "Your pipeline may be too small. Focus on lead generation activities.",
                    "priority": "high"
                })
        
        # Trend insights
        improved_metrics = comparison["summary"]["improved_metrics"]
        declined_metrics = comparison["summary"]["declined_metrics"]
        
        if improved_metrics:
            insights.append({
                "type": "success",
                "category": "trends",
                "title": "Improving Metrics",
                "description": f"Great progress on: {', '.join(improved_metrics)}",
                "priority": "low"
            })
        
        if declined_metrics:
            insights.append({
                "type": "warning",
                "category": "trends",
                "title": "Declining Metrics",
                "description": f"Need attention on: {', '.join(declined_metrics)}",
                "priority": "high"
            })
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "insights": insights,
            "summary": {
                "total_insights": len(insights),
                "high_priority": len([i for i in insights if i["priority"] == "high"]),
                "medium_priority": len([i for i in insights if i["priority"] == "medium"]),
                "low_priority": len([i for i in insights if i["priority"] == "low"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team insights: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the team sales dashboard service"""
    try:
        health_status = await dashboard_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "team_sales_dashboard",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
