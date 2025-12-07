from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.lead_generation_service import LeadGenerationService
from ..database import get_db

router = APIRouter(prefix="/lead-generation", tags=["Lead Generation"])
lead_generation_service = LeadGenerationService()

class WebsiteDataRequest(BaseModel):
    brand_id: int
    website_data: Dict[str, Any]

class SocialMediaDataRequest(BaseModel):
    brand_id: int
    platform: str
    engagement_data: Dict[str, Any]

class LeadQualificationRequest(BaseModel):
    lead_id: int
    qualification_criteria: Dict[str, Any]

class IntentScoringRequest(BaseModel):
    lead_id: int
    intent_signals: Dict[str, Any]

class LeadRecommendationsRequest(BaseModel):
    brand_id: int
    filters: Optional[Dict[str, Any]] = None

@router.post("/identify-from-website")
async def identify_leads_from_website(request: WebsiteDataRequest):
    """Identify leads from website analytics and forms"""
    try:
        result = await lead_generation_service.identify_leads_from_website(
            brand_id=request.brand_id,
            website_data=request.website_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify leads from website: {str(e)}")

@router.post("/identify-from-social-media")
async def identify_leads_from_social_media(request: SocialMediaDataRequest):
    """Identify leads from social media engagement"""
    try:
        result = await lead_generation_service.identify_leads_from_social_media(
            brand_id=request.brand_id,
            platform=request.platform,
            engagement_data=request.engagement_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify leads from social media: {str(e)}")

@router.post("/qualify-lead")
async def qualify_lead(request: LeadQualificationRequest):
    """Qualify a lead based on criteria"""
    try:
        result = await lead_generation_service.qualify_lead(
            lead_id=request.lead_id,
            qualification_criteria=request.qualification_criteria
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to qualify lead: {str(e)}")

@router.post("/score-intent")
async def score_lead_intent(request: IntentScoringRequest):
    """Score lead based on intent signals"""
    try:
        result = await lead_generation_service.score_lead_intent(
            lead_id=request.lead_id,
            intent_signals=request.intent_signals
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score lead intent: {str(e)}")

@router.post("/recommendations")
async def get_lead_recommendations(request: LeadRecommendationsRequest):
    """Get lead recommendations based on filters"""
    try:
        result = await lead_generation_service.get_lead_recommendations(
            brand_id=request.brand_id,
            filters=request.filters
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lead recommendations: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for lead generation service"""
    return {
        "status": "healthy",
        "service": "lead_generation",
        "timestamp": datetime.now().isoformat()
    }
