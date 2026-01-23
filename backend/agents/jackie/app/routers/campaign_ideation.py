from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_db
from ..services.campaign_ideation_service import CampaignIdeationService

router = APIRouter(prefix="/campaign-ideation", tags=["AI-Powered JackieCampaign Ideation"])

class IdeationRequest(BaseModel):
    industry: str
    target_audience: List[str]
    campaign_goals: List[str]
    budget_range: str
    timeframe: str
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CampaignIdeaResponse(BaseModel):
    id: str
    title: str
    description: str
    concept_type: str
    target_audience: List[str]
    estimated_budget: Dict[str, Any]
    expected_roi: float
    implementation_timeline: str
    risk_level: str
    created_at: datetime

@router.post("/generate-ideas", response_model=List[CampaignIdeaResponse])
async def generate_campaign_ideas(
    request: IdeationRequest,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        results = service.generate_campaign_ideas(
            request.industry,
            request.target_audience,
            request.campaign_goals,
            request.budget_range,
            request.timeframe,
            request.constraints
        )
        return [
            CampaignIdeaResponse(
                id=result["id"],
                title=result["title"],
                description=result["description"],
                concept_type=result["concept_type"],
                target_audience=result["target_audience"],
                estimated_budget=result["estimated_budget"],
                expected_roi=result["expected_roi"],
                implementation_timeline=result["implementation_timeline"],
                risk_level=result["risk_level"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/{idea_id}", response_model=CampaignIdeaResponse)
async def get_campaign_idea(idea_id: str, db: Session = Depends(get_db)):
    service = CampaignIdeationService(db)
    try:
        result = service.get_campaign_idea(idea_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return CampaignIdeaResponse(
            id=result["id"],
            title=result["title"],
            description=result["description"],
            concept_type=result["concept_type"],
            target_audience=result["target_audience"],
            estimated_budget=result["estimated_budget"],
            expected_roi=result["expected_roi"],
            implementation_timeline=result["implementation_timeline"],
            risk_level=result["risk_level"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas", response_model=List[CampaignIdeaResponse])
async def list_campaign_ideas(
    industry: Optional[str] = None,
    concept_type: Optional[str] = None,
    budget_range: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        results = service.list_campaign_ideas(industry, concept_type, budget_range, risk_level, limit, offset)
        return [
            CampaignIdeaResponse(
                id=result["id"],
                title=result["title"],
                description=result["description"],
                concept_type=result["concept_type"],
                target_audience=result["target_audience"],
                estimated_budget=result["estimated_budget"],
                expected_roi=result["expected_roi"],
                implementation_timeline=result["implementation_timeline"],
                risk_level=result["risk_level"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/refine")
async def refine_campaign_idea(
    idea_id: str,
    refinement_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.refine_campaign_idea(idea_id, refinement_criteria)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {
            "message": "JackieCampaign idea refined successfully",
            "refined_idea": result["refined_idea"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/expand")
async def expand_campaign_idea(
    idea_id: str,
    expansion_type: str,
    additional_context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.expand_campaign_idea(idea_id, expansion_type, additional_context)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {
            "message": "JackieCampaign idea expanded successfully",
            "expanded_details": result["expanded_details"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/validate")
async def validate_campaign_idea(
    idea_id: str,
    validation_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.validate_campaign_idea(idea_id, validation_criteria)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/implement")
async def implement_campaign_idea(
    idea_id: str,
    implementation_plan: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.implement_campaign_idea(idea_id, implementation_plan)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {
            "message": "JackieCampaign idea implementation started",
            "campaign_id": result["campaign_id"],
            "implementation_status": result["implementation_status"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trends/analyze")
async def analyze_trends_for_ideation(
    industry: str,
    timeframe: str = "30d",
    trend_sources: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.analyze_trends_for_ideation(industry, timeframe, trend_sources)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{industry}")
async def get_industry_trends(
    industry: str,
    trend_category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        trends = service.get_industry_trends(industry, trend_category, limit, offset)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/competitors/analyze")
async def analyze_competitor_campaigns(
    competitors: List[str],
    industry: str,
    analysis_period: str = "90d",
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.analyze_competitor_campaigns(competitors, industry, analysis_period)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/competitors/{competitor}/campaigns")
async def get_competitor_campaigns(
    competitor: str,
    campaign_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        campaigns = service.get_competitor_campaigns(competitor, campaign_type, limit, offset)
        return {"campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inspiration/generate")
async def generate_inspiration(
    inspiration_type: str,
    context: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.generate_inspiration(inspiration_type, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inspiration/sources")
async def get_inspiration_sources(
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        sources = service.get_inspiration_sources(source_type)
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/brainstorming/session")
async def start_brainstorming_session(
    session_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.start_brainstorming_session(session_config)
        return {
            "message": "Brainstorming session started",
            "session_id": result["session_id"],
            "session_status": result["session_status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brainstorming/{session_id}/ideas")
async def get_brainstorming_ideas(
    session_id: str,
    idea_category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        ideas = service.get_brainstorming_ideas(session_id, idea_category, limit, offset)
        return {"ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/brainstorming/{session_id}/add-idea")
async def add_brainstorming_idea(
    session_id: str,
    idea_content: str,
    idea_category: str = "general",
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.add_brainstorming_idea(session_id, idea_content, idea_category)
        return {
            "message": "Idea added to brainstorming session",
            "idea_id": result["idea_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/rate")
async def rate_campaign_idea(
    idea_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.rate_campaign_idea(idea_id, rating, feedback)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {"message": "Idea rated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/{idea_id}/ratings")
async def get_idea_ratings(
    idea_id: str,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        ratings = service.get_idea_ratings(idea_id)
        if not ratings:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {"ratings": ratings}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/favorite")
async def favorite_campaign_idea(
    idea_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.favorite_campaign_idea(idea_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {"message": "Idea favorited successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/favorites/{user_id}")
async def get_user_favorites(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        favorites = service.get_user_favorites(user_id, limit, offset)
        return {"favorites": favorites}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/share")
async def share_campaign_idea(
    idea_id: str,
    share_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.share_campaign_idea(idea_id, share_config)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {
            "message": "Idea shared successfully",
            "share_url": result["share_url"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/batch-generate")
async def batch_generate_ideas(
    batch_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.batch_generate_ideas(batch_config)
        return {
            "message": f"Generated {result['generated_count']} ideas successfully",
            "ideas": result["ideas"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/top-rated")
async def get_top_rated_ideas(
    industry: Optional[str] = None,
    timeframe: str = "30d",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        ideas = service.get_top_rated_ideas(industry, timeframe, limit)
        return {"ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/trending")
async def get_trending_ideas(
    industry: Optional[str] = None,
    timeframe: str = "7d",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        ideas = service.get_trending_ideas(industry, timeframe, limit)
        return {"ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/duplicate")
async def duplicate_campaign_idea(
    idea_id: str,
    customization: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        result = service.duplicate_campaign_idea(idea_id, customization)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign idea not found")
        return {
            "message": "Idea duplicated successfully",
            "new_idea_id": result["new_idea_id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/ideation")
async def get_ideation_analytics(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        analytics = service.get_ideation_analytics(timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/ideas/{idea_id}/performance")
async def get_idea_performance_analytics(
    idea_id: str,
    metrics: List[str],
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CampaignIdeationService(db)
    try:
        analytics = service.get_idea_performance_analytics(idea_id, metrics, timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
