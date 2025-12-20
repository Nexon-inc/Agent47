from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.market_trend_alerts_service import MarketTrendAlertsService, MarketTrend, TrendAlert, CompetitorCampaign
from ..database import get_eric_database
from core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/market-trend-alerts", tags=["Market Trend Alerts"])
trend_service = MarketTrendAlertsService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class MarketTrendCreate(BaseModel):
    trend_name: str
    industry: str
    description: str
    impact_level: str
    confidence_score: float
    evidence: List[str] = []
    affected_segments: List[str] = []
    opportunities: List[str] = []
    threats: List[str] = []
    recommended_actions: List[str] = []

class TrendAlertCreate(BaseModel):
    trend_id: int
    alert_type: str
    severity: str
    message: str

class TrendDetectionRequest(BaseModel):
    industry: str
    data_sources: List[str]

class CampaignMonitoringRequest(BaseModel):
    industry: str

class StrategicRecommendationsRequest(BaseModel):
    industry: str

# Market Trend Endpoints
@router.post("/trends", response_model=MarketTrend, summary="Create Market Trend")
async def create_market_trend(trend_data: MarketTrendCreate):
    """Create a new market trend for monitoring"""
    try:
        market_trend = MarketTrend(**trend_data.dict())
        created_trend = await trend_service.create_market_trend(market_trend)
        return created_trend
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create market trend: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends", response_model=List[MarketTrend], summary="Get Market Trends")
async def get_market_trends(industry: str = None, status: str = None):
    """Get market trends, optionally filtered by industry and status"""
    try:
        trends = await trend_service.get_market_trends(industry, status)
        return trends
    except Exception as e:
        logger.error(f"Failed to get market trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends/{trend_id}", response_model=MarketTrend, summary="Get Market Trend")
async def get_market_trend(trend_id: int):
    """Get a specific market trend by ID"""
    try:
        trends = await trend_service.get_market_trends()
        trend = next((t for t in trends if t.id == trend_id), None)
        
        if not trend:
            raise HTTPException(status_code=404, detail="Market trend not found")
        
        return trend
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market trend {trend_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trends/detect", response_model=List[MarketTrend], summary="Detect Market Trends")
async def detect_market_trends(request: TrendDetectionRequest):
    """Automatically detect market trends from various data sources"""
    try:
        detected_trends = await trend_service.detect_market_trends(
            request.industry,
            request.data_sources
        )
        return detected_trends
    except Exception as e:
        logger.error(f"Failed to detect market trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trend Alert Endpoints
@router.post("/alerts", response_model=TrendAlert, summary="Create Trend Alert")
async def create_trend_alert(alert_data: TrendAlertCreate):
    """Create a new trend alert"""
    try:
        alert = await trend_service.create_trend_alert(
            alert_data.trend_id,
            alert_data.alert_type,
            alert_data.severity,
            alert_data.message
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create trend alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/alerts", response_model=List[TrendAlert], summary="Get Trend Alerts")
async def get_trend_alerts(trend_id: int = None, severity: str = None, resolved: bool = None):
    """Get trend alerts with optional filtering"""
    try:
        alerts = await trend_service.get_trend_alerts(trend_id, severity, resolved)
        return alerts
    except Exception as e:
        logger.error(f"Failed to get trend alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/alerts/{alert_id}/acknowledge", summary="Acknowledge Trend Alert")
async def acknowledge_trend_alert(alert_id: int):
    """Acknowledge a trend alert"""
    try:
        success = await trend_service.acknowledge_alert(alert_id)
        
        if success:
            return {"message": "Alert acknowledged successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/alerts/{alert_id}/resolve", summary="Resolve Trend Alert")
async def resolve_trend_alert(alert_id: int):
    """Resolve a trend alert"""
    try:
        success = await trend_service.resolve_alert(alert_id)
        
        if success:
            return {"message": "Alert resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Competitor Campaign Monitoring Endpoints
@router.post("/campaigns/monitor", response_model=List[CompetitorCampaign], summary="Monitor Competitor Campaigns")
async def monitor_competitor_campaigns(request: CampaignMonitoringRequest):
    """Monitor and analyze competitor campaigns"""
    try:
        campaigns = await trend_service.monitor_competitor_campaigns(request.industry)
        return campaigns
    except Exception as e:
        logger.error(f"Failed to monitor competitor campaigns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/campaigns/{industry}", response_model=List[CompetitorCampaign], summary="Get Competitor Campaigns")
async def get_competitor_campaigns(industry: str):
    """Get monitored competitor campaigns for an industry"""
    try:
        campaigns = await trend_service.monitor_competitor_campaigns(industry)
        return campaigns
    except Exception as e:
        logger.error(f"Failed to get competitor campaigns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Strategic Recommendations Endpoints
@router.post("/strategic-recommendations", summary="Generate Strategic Recommendations")
async def generate_strategic_recommendations(request: StrategicRecommendationsRequest):
    """Generate strategic recommendations based on market trends and competitor analysis"""
    try:
        recommendations = await trend_service.generate_strategic_recommendations(request.industry)
        return recommendations
    except Exception as e:
        logger.error(f"Failed to generate strategic recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/strategic-recommendations/{industry}", summary="Get Strategic Recommendations")
async def get_strategic_recommendations(industry: str):
    """Get strategic recommendations for an industry"""
    try:
        recommendations = await trend_service.generate_strategic_recommendations(industry)
        return recommendations
    except Exception as e:
        logger.error(f"Failed to get strategic recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@router.get("/analytics/trends/{industry}", summary="Get Trend Analytics")
async def get_trend_analytics(industry: str):
    """Get analytics for market trends in an industry"""
    try:
        trends = await trend_service.get_market_trends(industry)
        
        # Calculate analytics
        total_trends = len(trends)
        high_impact_trends = len([t for t in trends if t.impact_level == "high"])
        medium_impact_trends = len([t for t in trends if t.impact_level == "medium"])
        low_impact_trends = len([t for t in trends if t.impact_level == "low"])
        
        avg_confidence = sum(t.confidence_score for t in trends) / total_trends if total_trends > 0 else 0
        
        return {
            "industry": industry,
            "total_trends": total_trends,
            "impact_distribution": {
                "high": high_impact_trends,
                "medium": medium_impact_trends,
                "low": low_impact_trends
            },
            "average_confidence": avg_confidence,
            "trend_categories": list(set(t.trend_name.split()[0] for t in trends)),
            "most_affected_segments": list(set(segment for t in trends for segment in t.affected_segments))
        }
    except Exception as e:
        logger.error(f"Failed to get trend analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/alerts/{industry}", summary="Get Alert Analytics")
async def get_alert_analytics(industry: str):
    """Get analytics for trend alerts in an industry"""
    try:
        alerts = await trend_service.get_trend_alerts()
        
        # Filter alerts by industry trends
        trends = await trend_service.get_market_trends(industry)
        trend_ids = [t.id for t in trends]
        industry_alerts = [a for a in alerts if a.trend_id in trend_ids]
        
        total_alerts = len(industry_alerts)
        critical_alerts = len([a for a in industry_alerts if a.severity == "critical"])
        high_alerts = len([a for a in industry_alerts if a.severity == "high"])
        medium_alerts = len([a for a in industry_alerts if a.severity == "medium"])
        low_alerts = len([a for a in industry_alerts if a.severity == "low"])
        
        resolved_alerts = len([a for a in industry_alerts if a.resolved])
        acknowledged_alerts = len([a for a in industry_alerts if a.acknowledged])
        
        return {
            "industry": industry,
            "total_alerts": total_alerts,
            "severity_distribution": {
                "critical": critical_alerts,
                "high": high_alerts,
                "medium": medium_alerts,
                "low": low_alerts
            },
            "status_distribution": {
                "resolved": resolved_alerts,
                "acknowledged": acknowledged_alerts,
                "pending": total_alerts - resolved_alerts
            },
            "alert_types": list(set(a.alert_type for a in industry_alerts))
        }
    except Exception as e:
        logger.error(f"Failed to get alert analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/campaigns/{industry}", summary="Get Campaign Analytics")
async def get_campaign_analytics(industry: str):
    """Get analytics for competitor campaigns in an industry"""
    try:
        campaigns = await trend_service.monitor_competitor_campaigns(industry)
        
        total_campaigns = len(campaigns)
        high_impact_campaigns = len([c for c in campaigns if c.impact_assessment == "high"])
        medium_impact_campaigns = len([c for c in campaigns if c.impact_assessment == "medium"])
        low_impact_campaigns = len([c for c in campaigns if c.impact_assessment == "low"])
        
        campaign_types = list(set(c.campaign_type for c in campaigns))
        channels = list(set(channel for c in campaigns for channel in c.channels))
        
        total_budget = sum(c.estimated_budget for c in campaigns if c.estimated_budget)
        avg_budget = total_budget / len([c for c in campaigns if c.estimated_budget]) if campaigns else 0
        
        return {
            "industry": industry,
            "total_campaigns": total_campaigns,
            "impact_distribution": {
                "high": high_impact_campaigns,
                "medium": medium_impact_campaigns,
                "low": low_impact_campaigns
            },
            "campaign_types": campaign_types,
            "channels": channels,
            "budget_metrics": {
                "total_budget": total_budget,
                "average_budget": avg_budget
            },
            "competitors": list(set(c.competitor_name for c in campaigns))
        }
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/industries", summary="Get Supported Industries")
async def get_supported_industries():
    """Get list of supported industries for trend monitoring"""
    try:
        industries = [
            "technology",
            "healthcare",
            "finance",
            "manufacturing",
            "retail",
            "education",
            "real_estate",
            "consulting"
        ]
        
        return {
            "industries": industries,
            "total_count": len(industries)
        }
    except Exception as e:
        logger.error(f"Failed to get supported industries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/data-sources", summary="Get Data Sources")
async def get_data_sources():
    """Get list of data sources used for trend detection"""
    try:
        data_sources = [
            "competitor_activities",
            "social_media",
            "industry_news",
            "customer_behavior",
            "market_data",
            "financial_reports",
            "patent_filings",
            "job_postings"
        ]
        
        return {
            "data_sources": data_sources,
            "total_count": len(data_sources),
            "description": "Data sources used for automatic trend detection"
        }
    except Exception as e:
        logger.error(f"Failed to get data sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/alert-types", summary="Get Alert Types")
async def get_alert_types():
    """Get list of supported alert types"""
    try:
        alert_types = [
            "new_trend",
            "trend_acceleration",
            "trend_deceleration",
            "trend_reversal"
        ]
        
        return {
            "alert_types": alert_types,
            "total_count": len(alert_types)
        }
    except Exception as e:
        logger.error(f"Failed to get alert types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/severity-levels", summary="Get Severity Levels")
async def get_severity_levels():
    """Get list of supported severity levels"""
    try:
        severity_levels = [
            "critical",
            "high",
            "medium",
            "low"
        ]
        
        return {
            "severity_levels": severity_levels,
            "total_count": len(severity_levels)
        }
    except Exception as e:
        logger.error(f"Failed to get severity levels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/campaign-types", summary="Get Campaign Types")
async def get_campaign_types():
    """Get list of supported campaign types for monitoring"""
    try:
        campaign_types = [
            "email",
            "social_media",
            "content",
            "advertising",
            "pricing",
            "influencer",
            "event",
            "partnership"
        ]
        
        return {
            "campaign_types": campaign_types,
            "total_count": len(campaign_types)
        }
    except Exception as e:
        logger.error(f"Failed to get campaign types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="Market Trend Alerts Health Check")
async def health_check():
    """Check the health of the market trend alerts service"""
    try:
        # Test basic functionality
        test_trends = await trend_service.get_market_trends()
        test_alerts = await trend_service.get_trend_alerts()
        
        return {
            "status": "healthy",
            "service": "Market Trend Alerts",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "Market Trend Detection",
                "Trend Alert Management",
                "Competitor Campaign Monitoring",
                "Strategic Recommendations",
                "Analytics and Reporting"
            ],
            "trends_loaded": len(test_trends),
            "alerts_loaded": len(test_alerts)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
