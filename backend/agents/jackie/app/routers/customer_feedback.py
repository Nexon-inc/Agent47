from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.customer_feedback_service import CustomerFeedbackService

router = APIRouter(prefix="/customer-feedback", tags=["Customer Feedback Loop"])

@router.post("/collect-feedback")
async def collect_customer_feedback(campaign_id: str, feedback_data: Dict[str, Any], feedback_type: str = "survey"):
    try:
        service = CustomerFeedbackService()
        await service.initialize()
        return await service.collect_customer_feedback(campaign_id, feedback_data, feedback_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-survey")
async def analyze_survey_data(survey_id: str, survey_responses: List[Dict[str, Any]]):
    try:
        service = CustomerFeedbackService()
        await service.initialize()
        return await service.analyze_survey_data(survey_id, survey_responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refine-campaign")
async def refine_campaign_based_on_feedback(campaign_id: str, feedback_insights: Dict[str, Any]):
    try:
        service = CustomerFeedbackService()
        await service.initialize()
        return await service.refine_campaign_based_on_feedback(campaign_id, feedback_insights)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_feedback_analytics(timeframe: str = "30d"):
    try:
        service = CustomerFeedbackService()
        await service.initialize()
        return await service.get_feedback_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
