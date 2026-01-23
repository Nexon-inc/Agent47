from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.customer_engagement_service import CustomerEngagementService
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/customer-engagement", tags=["Customer Engagement"])

class CreateChatbotRequest(BaseModel):
    name: str
    description: str
    platform: str
    brand_voice: str
    capabilities: List[str]

class ChatMessageRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class EngagementCampaignRequest(BaseModel):
    name: str
    target_audience: List[str]
    engagement_type: str
    content: Dict[str, Any]
    schedule: Dict[str, Any]

class ChatbotResponse(BaseModel):
    id: int
    name: str
    description: str
    platform: str
    brand_voice: str
    capabilities: List[str]
    status: str
    created_at: datetime

@router.post("/chatbots", response_model=ChatbotResponse)
async def create_chatbot(
    request: CreateChatbotRequest,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.create_chatbot(
            request.name,
            request.description,
            request.platform,
            request.brand_voice,
            request.capabilities
        )
        return ChatbotResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            platform=result["platform"],
            brand_voice=result["brand_voice"],
            capabilities=result["capabilities"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(chatbot_id: int, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        result = service.get_chatbot(chatbot_id)
        if not result:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        return ChatbotResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            platform=result["platform"],
            brand_voice=result["brand_voice"],
            capabilities=result["capabilities"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chatbots", response_model=List[ChatbotResponse])
async def list_chatbots(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        results = service.list_chatbots(platform, status, limit, offset)
        return [
            ChatbotResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                platform=result["platform"],
                brand_voice=result["brand_voice"],
                capabilities=result["capabilities"],
                status=result["status"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chatbots/{chatbot_id}/start")
async def start_chatbot(chatbot_id: int, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        result = service.start_chatbot(chatbot_id)
        if not result:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        return {"message": "Chatbot started successfully", "status": result["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chatbots/{chatbot_id}/stop")
async def stop_chatbot(chatbot_id: int, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        result = service.stop_chatbot(chatbot_id)
        if not result:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        return {"message": "Chatbot stopped successfully", "status": result["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/message")
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.process_message(
            request.message,
            request.user_id,
            request.session_id,
            request.context
        )
        return {
            "response": result["response"],
            "session_id": result["session_id"],
            "intent": result["intent"],
            "confidence": result["confidence"],
            "suggestions": result["suggestions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        result = service.get_chat_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/sessions/{session_id}/end")
async def end_chat_session(session_id: str, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        result = service.end_chat_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session ended successfully", "summary": result["summary"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns")
async def create_engagement_campaign(
    request: EngagementCampaignRequest,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.create_engagement_campaign(
            request.name,
            request.target_audience,
            request.engagement_type,
            request.content,
            request.schedule
        )
        return {
            "message": "Engagement campaign created successfully",
            "campaign_id": result["campaign_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns")
async def list_engagement_campaigns(
    status: Optional[str] = None,
    engagement_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        campaigns = service.list_engagement_campaigns(status, engagement_type, limit, offset)
        return {"campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(campaign_id: int, db: Session = Depends(get_db)):
    service = CustomerEngagementService(db)
    try:
        analytics = service.get_campaign_analytics(campaign_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_engagement_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        overview = service.get_engagement_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/sentiment")
async def get_sentiment_analysis(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        sentiment = service.get_sentiment_analysis(timeframe)
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.submit_feedback(feedback_data)
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": result["feedback_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback")
async def get_feedback(
    feedback_type: Optional[str] = None,
    rating: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        feedback = service.get_feedback(feedback_type, rating, limit, offset)
        return {"feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/rules")
async def create_automation_rule(
    rule_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.create_automation_rule(rule_data)
        return {
            "message": "Automation rule created successfully",
            "rule_id": result["rule_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automation/rules")
async def list_automation_rules(
    status: Optional[str] = None,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        rules = service.list_automation_rules(status, rule_type)
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/surveys")
async def create_survey(
    survey_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        result = service.create_survey(survey_data)
        return {
            "message": "Survey created successfully",
            "survey_id": result["survey_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/surveys")
async def list_surveys(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        surveys = service.list_surveys(status, limit, offset)
        return {"surveys": surveys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/surveys/{survey_id}/responses")
async def get_survey_responses(
    survey_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerEngagementService(db)
    try:
        responses = service.get_survey_responses(survey_id, limit, offset)
        if not responses:
            raise HTTPException(status_code=404, detail="Survey not found")
        return {"responses": responses}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
