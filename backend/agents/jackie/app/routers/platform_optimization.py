from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.platform_optimization_service import PlatformOptimizationService

router = APIRouter(prefix="/platform-optimization", tags=["Platform-Specific Optimization"])

@router.post("/tiktok")
def optimize_for_tiktok(content_brief: Dict[str, Any], target_audience: List[str], 
                       content_type: str = "video", db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.optimize_for_tiktok(content_brief, target_audience, content_type)

@router.post("/shopify-ads")
def optimize_for_shopify_ads(product_data: Dict[str, Any], ad_format: str, 
                           target_audience: List[str], db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.optimize_for_shopify_ads(product_data, ad_format, target_audience)

@router.post("/threads")
def optimize_for_threads(content_brief: Dict[str, Any], engagement_goals: Dict[str, Any], 
                        db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.optimize_for_threads(content_brief, engagement_goals)

@router.post("/emerging-channel")
def create_emerging_channel_strategy(channel_name: str, channel_data: Dict[str, Any], 
                                   target_audience: List[str], db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.create_emerging_channel_strategy(channel_name, channel_data, target_audience)

@router.post("/platform-content")
def create_platform_content(platform: str, content_brief: Dict[str, Any], 
                          platform_specific_requirements: Dict[str, Any], db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.create_platform_content(platform, content_brief, platform_specific_requirements)

@router.post("/trends")
def analyze_platform_trends(platform: str, trend_analysis: Dict[str, Any], db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.analyze_platform_trends(platform, trend_analysis)

@router.get("/analytics")
def get_platform_optimization_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = PlatformOptimizationService(db)
    return service.get_platform_optimization_analytics(timeframe)
