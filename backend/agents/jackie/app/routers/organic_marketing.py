from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.organic_marketing_service import OrganicMarketingService

router = APIRouter(prefix="/organic-marketing", tags=["Organic Marketing"])


class OrganicStrategyRequest(BaseModel):
    business_info: Dict[str, Any]
    target_audience: List[str]
    goals: List[str]


class ContentPieceRequest(BaseModel):
    topic: str
    content_type: str
    target_audience: List[str]
    seo_keywords: List[str]


class SocialPostRequest(BaseModel):
    platform: str
    content_brief: str
    target_audience: List[str]
    engagement_goals: Dict[str, Any]


class CommunityEngagementRequest(BaseModel):
    community_type: str
    engagement_strategy: Dict[str, Any]
    target_members: List[str]

@router.post("/strategy")
def create_organic_strategy(request: OrganicStrategyRequest, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.create_organic_strategy(request.business_info, request.target_audience, request.goals)

@router.post("/content")
def generate_content_piece(request: ContentPieceRequest, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.generate_content_piece(request.topic, request.content_type, request.target_audience, request.seo_keywords)

@router.post("/social-post")
def create_social_post(request: SocialPostRequest, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.create_social_post(request.platform, request.content_brief, request.target_audience, request.engagement_goals)

@router.post("/community-engagement")
def build_community_engagement(request: CommunityEngagementRequest, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.build_community_engagement(request.community_type, request.engagement_strategy, request.target_members)

@router.post("/seo-optimization")
def optimize_seo_organically(website_url: str, target_keywords: List[str], industry: str, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.optimize_seo_organically(website_url, target_keywords, industry)

@router.post("/guest-posting")
def create_guest_posting_strategy(industry: str, target_publications: List[str], content_themes: List[str], db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.create_guest_posting_strategy(industry, target_publications, content_themes)

@router.post("/influencer-relationships")
def develop_influencer_relationships(industry: str, target_influencers: List[str], relationship_goals: Dict[str, Any], db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.develop_influencer_relationships(industry, target_influencers, relationship_goals)

@router.post("/ugc-campaign")
def create_user_generated_content_campaign(campaign_brief: Dict[str, Any], target_audience: List[str], db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.create_user_generated_content_campaign(campaign_brief, target_audience)

@router.post("/local-seo")
def optimize_local_seo(business_location: Dict[str, Any], local_keywords: List[str], industry: str, db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.optimize_local_seo(business_location, local_keywords, industry)

@router.post("/email-newsletter")
def create_email_newsletter_strategy(subscriber_segments: List[str], content_themes: List[str], db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.create_email_newsletter_strategy(subscriber_segments, content_themes)

@router.get("/analytics")
def get_organic_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.get_organic_analytics(timeframe)

@router.post("/batch-content")
def batch_create_content(content_batch: List[Dict[str, Any]], db: Session = Depends(get_db)):
    service = OrganicMarketingService(db)
    return service.batch_create_content(content_batch)
