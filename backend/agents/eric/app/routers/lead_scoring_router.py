from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from ..services.lead_scoring_service import LeadScoringService
from core.authentication.auth_manager import AuthManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lead-scoring", tags=["EricLead Scoring"])

# Pydantic models
class LeadScoringRequest(BaseModel):
    lead_id: str
    lead_data: Dict[str, Any]

class BehavioralScoringRequest(BaseModel):
    lead_id: str
    behavioral_data: Dict[str, Any]

class DemographicScoringRequest(BaseModel):
    lead_id: str
    demographic_data: Dict[str, Any]

class IntentScoringRequest(BaseModel):
    lead_id: str
    intent_data: Dict[str, Any]

class EngagementScoringRequest(BaseModel):
    lead_id: str
    engagement_data: Dict[str, Any]

class CompanyFitScoringRequest(BaseModel):
    lead_id: str
    company_data: Dict[str, Any]

class ScoringUpdateRequest(BaseModel):
    lead_id: str
    scoring_criteria: Dict[str, Any]

# Initialize services
lead_scoring_service = LeadScoringService()
auth_manager = AuthManager()

@router.post("/score-lead")
async def score_lead(request: LeadScoringRequest):
    """Score a lead using AI-powered algorithms"""
    try:
        result = await lead_scoring_service.score_lead(
            request.lead_id,
            request.lead_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/behavioral-scoring")
async def score_behavioral_patterns(request: BehavioralScoringRequest):
    """Score lead based on behavioral patterns"""
    try:
        result = await lead_scoring_service.score_behavioral_patterns(
            request.lead_id,
            request.behavioral_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring behavioral patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demographic-scoring")
async def score_demographic_fit(request: DemographicScoringRequest):
    """Score lead based on demographic fit"""
    try:
        result = await lead_scoring_service.score_demographic_fit(
            request.lead_id,
            request.demographic_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring demographic fit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intent-scoring")
async def score_purchase_intent(request: IntentScoringRequest):
    """Score lead based on purchase intent"""
    try:
        result = await lead_scoring_service.score_purchase_intent(
            request.lead_id,
            request.intent_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring purchase intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/engagement-scoring")
async def score_engagement_level(request: EngagementScoringRequest):
    """Score lead based on engagement level"""
    try:
        result = await lead_scoring_service.score_engagement_level(
            request.lead_id,
            request.engagement_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring engagement level: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/company-fit-scoring")
async def score_company_fit(request: CompanyFitScoringRequest):
    """Score lead based on company fit"""
    try:
        result = await lead_scoring_service.score_company_fit(
            request.lead_id,
            request.company_data
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error scoring company fit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}/score")
async def get_lead_score(lead_id: str):
    """Get current score for a specific lead"""
    try:
        result = await lead_scoring_service.get_lead_score(lead_id)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting lead score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}/score-history")
async def get_lead_score_history(lead_id: str):
    """Get score history for a specific lead"""
    try:
        result = await lead_scoring_service.get_lead_score_history(lead_id)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting lead score history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/high-priority")
async def get_high_priority_leads(limit: int = 50):
    """Get list of high priority leads"""
    try:
        result = await lead_scoring_service.get_high_priority_leads(limit)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting high priority leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/qualified")
async def get_qualified_leads(limit: int = 50):
    """Get list of qualified leads"""
    try:
        result = await lead_scoring_service.get_qualified_leads(limit)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting qualified leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/qualify")
async def qualify_lead(lead_id: str):
    """Qualify a lead based on scoring"""
    try:
        result = await lead_scoring_service.qualify_lead(lead_id)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error qualifying lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/disqualify")
async def disqualify_lead(lead_id: str, reason: str):
    """Disqualify a lead"""
    try:
        result = await lead_scoring_service.disqualify_lead(lead_id, reason)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error disqualifying lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/leads/{lead_id}/update-scoring")
async def update_lead_scoring(request: ScoringUpdateRequest):
    """Update lead scoring criteria"""
    try:
        result = await lead_scoring_service.update_lead_scoring(
            request.lead_id,
            request.scoring_criteria
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error updating lead scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scoring-models")
async def get_scoring_models():
    """Get available scoring models"""
    try:
        result = await lead_scoring_service.get_scoring_models()
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting scoring models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scoring-models/train")
async def train_scoring_model(model_name: str, training_data: Dict[str, Any]):
    """Train a scoring model with new data"""
    try:
        result = await lead_scoring_service.train_scoring_model(model_name, training_data)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error training scoring model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scoring-models/{model_name}/performance")
async def get_model_performance(model_name: str):
    """Get performance metrics for a scoring model"""
    try:
        result = await lead_scoring_service.get_model_performance(model_name)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/scoring-trends")
async def get_scoring_trends(time_period: str = "30d"):
    """Get scoring trends and analytics"""
    try:
        result = await lead_scoring_service.get_scoring_trends(time_period)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting scoring trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/score-distribution")
async def get_score_distribution():
    """Get distribution of lead scores"""
    try:
        result = await lead_scoring_service.get_score_distribution()
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting score distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/conversion-rates")
async def get_conversion_rates_by_score():
    """Get conversion rates by score ranges"""
    try:
        result = await lead_scoring_service.get_conversion_rates_by_score()
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting conversion rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-score")
async def bulk_score_leads(lead_ids: List[str]):
    """Score multiple leads in bulk"""
    try:
        result = await lead_scoring_service.bulk_score_leads(lead_ids)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error bulk scoring leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thresholds")
async def get_scoring_thresholds():
    """Get current scoring thresholds"""
    try:
        result = await lead_scoring_service.get_scoring_thresholds()
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting scoring thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/thresholds")
async def update_scoring_thresholds(thresholds: Dict[str, Any]):
    """Update scoring thresholds"""
    try:
        result = await lead_scoring_service.update_scoring_thresholds(thresholds)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error updating scoring thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}/scoring-breakdown")
async def get_lead_scoring_breakdown(lead_id: str):
    """Get detailed scoring breakdown for a lead"""
    try:
        result = await lead_scoring_service.get_lead_scoring_breakdown(lead_id)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting lead scoring breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/manual-score")
async def set_manual_score(lead_id: str, score: float, reason: str):
    """Set manual score for a lead"""
    try:
        result = await lead_scoring_service.set_manual_score(lead_id, score, reason)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error setting manual score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}/scoring-factors")
async def get_lead_scoring_factors(lead_id: str):
    """Get factors that influenced lead scoring"""
    try:
        result = await lead_scoring_service.get_lead_scoring_factors(lead_id)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting lead scoring factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
