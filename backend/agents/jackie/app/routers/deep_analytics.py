from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.deep_analytics_service import DeepAnalyticsService

router = APIRouter(prefix="/deep-analytics", tags=["Deep JackieCampaign Analytics"])

@router.post("/campaign-analysis/{campaign_id}")
def analyze_campaign_performance(campaign_id: str, analysis_depth: str = "comprehensive", 
                               include_sentiment: bool = True, db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.analyze_campaign_performance(campaign_id, analysis_depth, include_sentiment)

@router.post("/sentiment-analysis")
def perform_sentiment_analysis(content_data: List[Dict[str, Any]], analysis_type: str = "comprehensive", 
                             db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.perform_sentiment_analysis(content_data, analysis_type)

@router.post("/benchmark/{campaign_id}")
def benchmark_campaign_performance(campaign_id: str, benchmark_metrics: List[str], 
                                 industry_standard: str = "auto", db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.benchmark_campaign_performance(campaign_id, benchmark_metrics, industry_standard)

@router.post("/actionable-insights")
def generate_actionable_insights(campaign_data: Dict[str, Any], insight_focus: List[str], 
                               db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.generate_actionable_insights(campaign_data, insight_focus)

@router.post("/cross-channel-analysis")
def analyze_cross_channel_performance(campaign_ids: List[str], channel_metrics: Dict[str, Any], 
                                    db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.analyze_cross_channel_performance(campaign_ids, channel_metrics)

@router.get("/performance-report/{campaign_id}")
def generate_performance_report(campaign_id: str, report_type: str = "comprehensive", 
                              include_recommendations: bool = True, db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.generate_performance_report(campaign_id, report_type, include_recommendations)

@router.get("/analytics-summary")
def get_deep_analytics_summary(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = DeepAnalyticsService(db)
    return service.get_deep_analytics_summary(timeframe)
