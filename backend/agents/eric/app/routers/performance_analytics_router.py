from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.performance_analytics_service import PerformanceAnalyticsService

router = APIRouter(prefix="/performance-analytics", tags=["Performance Analytics"])
performance_analytics_service = PerformanceAnalyticsService()

# Request models
class PerformanceMetricsRequest(BaseModel):
    brand_id: str
    time_period: str = "30d"
    team_id: Optional[str] = None
    metrics_type: str = "all"

class ConversionTrackingRequest(BaseModel):
    brand_id: str
    funnel_stage: str
    time_period: str = "30d"

class ResponseTimeAnalysisRequest(BaseModel):
    brand_id: str
    channel: str = "all"
    time_period: str = "30d"

class TeamPerformanceRequest(BaseModel):
    team_id: str
    brand_id: str
    start_date: datetime
    end_date: datetime

class PerformanceReportRequest(BaseModel):
    brand_id: str
    report_type: str = "comprehensive"
    time_period: str = "30d"

class SalesTeamMetricsRequest(BaseModel):
    brand_id: str
    team_id: Optional[str] = None

class CustomerEngagementRequest(BaseModel):
    brand_id: str
    time_period: str = "30d"

# Response models
class PerformanceMetricsResponse(BaseModel):
    brand_id: str
    time_period: str
    overall_metrics: Dict[str, Any]
    conversion_analytics: Dict[str, Any]
    response_time_analytics: Dict[str, Any]
    team_performance: Dict[str, Any]
    insights: List[str]
    recommendations: List[Dict[str, Any]]

class ConversionTrackingResponse(BaseModel):
    brand_id: str
    funnel_stage: str
    time_period: str
    conversion_data: Dict[str, Any]
    conversion_metrics: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    optimization_recommendations: List[Dict[str, Any]]

class ResponseTimeAnalysisResponse(BaseModel):
    brand_id: str
    channel: str
    time_period: str
    response_time_data: Dict[str, Any]
    response_metrics: Dict[str, Any]
    improvement_opportunities: List[Dict[str, Any]]
    optimization_strategies: List[Dict[str, Any]]

class TeamPerformanceResponse(BaseModel):
    team_id: str
    brand_id: str
    date_range: Dict[str, datetime]
    team_data: Dict[str, Any]
    individual_metrics: Dict[str, Any]
    team_rankings: List[Dict[str, Any]]
    performance_insights: List[str]
    improvement_recommendations: List[Dict[str, Any]]

class PerformanceReportResponse(BaseModel):
    brand_id: str
    report_type: str
    time_period: str
    generated_at: datetime
    executive_summary: Dict[str, Any]
    detailed_analysis: Dict[str, Any]
    action_items: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

class SalesTeamMetricsResponse(BaseModel):
    brand_id: str
    team_id: Optional[str]
    sales_team_data: Dict[str, Any]
    kpis: Dict[str, Any]
    efficiency_metrics: Dict[str, Any]
    productivity_metrics: Dict[str, Any]
    performance_insights: List[str]
    improvement_opportunities: List[Dict[str, Any]]

class CustomerEngagementResponse(BaseModel):
    brand_id: str
    time_period: str
    engagement_data: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    engagement_patterns: Dict[str, Any]
    engagement_opportunities: List[Dict[str, Any]]
    engagement_strategies: List[Dict[str, Any]]

@router.post("/metrics", response_model=PerformanceMetricsResponse)
async def get_comprehensive_performance_metrics(request: PerformanceMetricsRequest):
    """Get comprehensive performance metrics for a brand"""
    try:
        result = await performance_analytics_service.get_comprehensive_performance_metrics(
            brand_id=request.brand_id,
            time_period=request.time_period
        )
        return PerformanceMetricsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.post("/conversion-tracking", response_model=ConversionTrackingResponse)
async def track_conversion_rates(request: ConversionTrackingRequest):
    """Track conversion rates across different funnel stages"""
    try:
        result = await performance_analytics_service.track_conversion_rates(
            brand_id=request.brand_id,
            funnel_stage=request.funnel_stage,
            time_period=request.time_period
        )
        return ConversionTrackingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track conversion rates: {str(e)}")

@router.post("/response-time-analysis", response_model=ResponseTimeAnalysisResponse)
async def analyze_response_times(request: ResponseTimeAnalysisRequest):
    """Analyze response times across different channels"""
    try:
        result = await performance_analytics_service.analyze_response_times(
            brand_id=request.brand_id,
            channel=request.channel,
            time_period=request.time_period
        )
        return ResponseTimeAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze response times: {str(e)}")

@router.post("/team-performance", response_model=TeamPerformanceResponse)
async def get_team_performance_dashboard(request: TeamPerformanceRequest):
    """Get comprehensive team performance dashboard"""
    try:
        result = await performance_analytics_service.get_team_performance_dashboard(
            team_id=request.team_id,
            brand_id=request.brand_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return TeamPerformanceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team performance dashboard: {str(e)}")

@router.post("/performance-report", response_model=PerformanceReportResponse)
async def generate_performance_report(request: PerformanceReportRequest):
    """Generate comprehensive performance report"""
    try:
        result = await performance_analytics_service.generate_performance_report(
            brand_id=request.brand_id,
            report_type=request.report_type,
            time_period=request.time_period
        )
        return PerformanceReportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate performance report: {str(e)}")

@router.post("/sales-team-metrics", response_model=SalesTeamMetricsResponse)
async def track_sales_team_metrics(request: SalesTeamMetricsRequest):
    """Track comprehensive sales team metrics"""
    try:
        result = await performance_analytics_service.track_sales_team_metrics(
            brand_id=request.brand_id,
            team_id=request.team_id
        )
        return SalesTeamMetricsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track sales team metrics: {str(e)}")

@router.post("/customer-engagement", response_model=CustomerEngagementResponse)
async def analyze_customer_engagement_metrics(request: CustomerEngagementRequest):
    """Analyze customer engagement metrics"""
    try:
        result = await performance_analytics_service.analyze_customer_engagement_metrics(
            brand_id=request.brand_id,
            time_period=request.time_period
        )
        return CustomerEngagementResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze customer engagement metrics: {str(e)}")

@router.get("/kpis/{brand_id}")
async def get_key_performance_indicators(brand_id: str, time_period: str = "30d"):
    """Get key performance indicators for a brand"""
    try:
        kpis = {
            "brand_id": brand_id,
            "time_period": time_period,
            "conversion_rate": 0.15,
            "response_time_avg": 2.5,
            "revenue_growth": 0.25,
            "customer_satisfaction": 4.3,
            "team_productivity": 0.78,
            "lead_quality_score": 0.82,
            "deal_velocity": 45,
            "win_rate": 0.65
        }
        return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get KPIs: {str(e)}")

@router.get("/benchmarks/{brand_id}")
async def get_performance_benchmarks(brand_id: str):
    """Get performance benchmarks for comparison"""
    try:
        benchmarks = {
            "brand_id": brand_id,
            "industry_benchmarks": {
                "conversion_rate": {"industry_avg": 0.12, "top_performers": 0.20},
                "response_time": {"industry_avg": 4.0, "top_performers": 1.5},
                "customer_satisfaction": {"industry_avg": 4.0, "top_performers": 4.5},
                "deal_velocity": {"industry_avg": 60, "top_performers": 30}
            },
            "competitor_analysis": {
                "competitor_a": {"conversion_rate": 0.14, "response_time": 3.5},
                "competitor_b": {"conversion_rate": 0.11, "response_time": 4.2},
                "competitor_c": {"conversion_rate": 0.16, "response_time": 2.8}
            }
        }
        return benchmarks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get benchmarks: {str(e)}")

@router.get("/trends/{brand_id}")
async def get_performance_trends(brand_id: str, time_period: str = "90d"):
    """Get performance trends over time"""
    try:
        trends = {
            "brand_id": brand_id,
            "time_period": time_period,
            "conversion_rate_trend": {
                "direction": "improving",
                "growth_rate": 0.05,
                "monthly_data": [0.12, 0.13, 0.14, 0.15]
            },
            "response_time_trend": {
                "direction": "improving",
                "improvement_rate": 0.15,
                "monthly_data": [3.2, 3.0, 2.8, 2.5]
            },
            "revenue_trend": {
                "direction": "increasing",
                "growth_rate": 0.25,
                "monthly_data": [350000, 380000, 420000, 450000]
            }
        }
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")

@router.get("/team-rankings/{brand_id}")
async def get_team_rankings(brand_id: str):
    """Get team performance rankings"""
    try:
        rankings = {
            "brand_id": brand_id,
            "team_rankings": [
                {
                    "rank": 1,
                    "team_id": "team_001",
                    "team_name": "Enterprise Sales",
                    "performance_score": 0.92,
                    "conversion_rate": 0.18,
                    "revenue_per_rep": 75000
                },
                {
                    "rank": 2,
                    "team_id": "team_002",
                    "team_name": "SMB Sales",
                    "performance_score": 0.85,
                    "conversion_rate": 0.15,
                    "revenue_per_rep": 55000
                },
                {
                    "rank": 3,
                    "team_id": "team_003",
                    "team_name": "Inside Sales",
                    "performance_score": 0.78,
                    "conversion_rate": 0.12,
                    "revenue_per_rep": 45000
                }
            ]
        }
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team rankings: {str(e)}")

@router.get("/individual-rankings/{team_id}")
async def get_individual_rankings(team_id: str):
    """Get individual performance rankings within a team"""
    try:
        rankings = {
            "team_id": team_id,
            "individual_rankings": [
                {
                    "rank": 1,
                    "member_id": "member_001",
                    "name": "John Doe",
                    "performance_score": 0.95,
                    "conversion_rate": 0.20,
                    "revenue_generated": 80000,
                    "leads_handled": 250
                },
                {
                    "rank": 2,
                    "member_id": "member_002",
                    "name": "Jane Smith",
                    "performance_score": 0.88,
                    "conversion_rate": 0.17,
                    "revenue_generated": 70000,
                    "leads_handled": 220
                },
                {
                    "rank": 3,
                    "member_id": "member_003",
                    "name": "Mike Johnson",
                    "performance_score": 0.82,
                    "conversion_rate": 0.15,
                    "revenue_generated": 65000,
                    "leads_handled": 200
                }
            ]
        }
        return rankings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get individual rankings: {str(e)}")

@router.get("/performance-insights/{brand_id}")
async def get_performance_insights(brand_id: str):
    """Get AI-generated performance insights"""
    try:
        insights = {
            "brand_id": brand_id,
            "insights": [
                {
                    "insight": "Response time improvements have led to 20% increase in conversion rates",
                    "confidence": 0.92,
                    "impact": "high",
                    "recommendation": "Continue optimizing response times across all channels"
                },
                {
                    "insight": "Team performance varies significantly - top performers are 3x more productive",
                    "confidence": 0.88,
                    "impact": "medium",
                    "recommendation": "Implement mentorship program to share best practices"
                },
                {
                    "insight": "Email response times are the biggest bottleneck in the sales funnel",
                    "confidence": 0.85,
                    "impact": "high",
                    "recommendation": "Implement automated email responses for immediate acknowledgment"
                },
                {
                    "insight": "Q4 shows consistent performance peaks across all metrics",
                    "confidence": 0.90,
                    "impact": "medium",
                    "recommendation": "Plan additional resources for Q4 to maximize performance"
                }
            ]
        }
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance insights: {str(e)}")

@router.get("/optimization-opportunities/{brand_id}")
async def get_optimization_opportunities(brand_id: str):
    """Get optimization opportunities for performance improvement"""
    try:
        opportunities = {
            "brand_id": brand_id,
            "opportunities": [
                {
                    "opportunity": "Automate email responses",
                    "current_performance": 4.2,
                    "target_performance": 1.5,
                    "potential_improvement": "64%",
                    "effort_required": "medium",
                    "expected_roi": "high"
                },
                {
                    "opportunity": "Enhance lead scoring",
                    "current_performance": 0.15,
                    "target_performance": 0.20,
                    "potential_improvement": "33%",
                    "effort_required": "high",
                    "expected_roi": "high"
                },
                {
                    "opportunity": "Implement team training",
                    "current_performance": 0.78,
                    "target_performance": 0.85,
                    "potential_improvement": "9%",
                    "effort_required": "medium",
                    "expected_roi": "medium"
                },
                {
                    "opportunity": "Optimize follow-up sequences",
                    "current_performance": 3,
                    "target_performance": 5,
                    "potential_improvement": "67%",
                    "effort_required": "low",
                    "expected_roi": "medium"
                }
            ]
        }
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization opportunities: {str(e)}")

@router.get("/performance-alerts/{brand_id}")
async def get_performance_alerts(brand_id: str):
    """Get performance alerts and notifications"""
    try:
        alerts = {
            "brand_id": brand_id,
            "alerts": [
                {
                    "alert_id": "alert_001",
                    "type": "performance_decline",
                    "severity": "medium",
                    "message": "Conversion rate has dropped by 15% in the last week",
                    "triggered_at": "2024-01-15T10:00:00Z",
                    "recommended_action": "Review recent lead quality and adjust scoring criteria"
                },
                {
                    "alert_id": "alert_002",
                    "type": "response_time_increase",
                    "severity": "high",
                    "message": "Average response time has increased to 6 hours",
                    "triggered_at": "2024-01-14T15:30:00Z",
                    "recommended_action": "Check team availability and implement automated responses"
                },
                {
                    "alert_id": "alert_003",
                    "type": "team_performance",
                    "severity": "low",
                    "message": "Team member John Doe has exceeded performance targets",
                    "triggered_at": "2024-01-13T09:15:00Z",
                    "recommended_action": "Recognize achievement and share best practices"
                }
            ]
        }
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance alerts: {str(e)}")
