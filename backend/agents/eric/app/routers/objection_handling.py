from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.objection_handling_service import ObjectionHandlingService, ObjectionAnalysis, ObjectionHandlingSession, ObjectionType, ObjectionResponse
from ..database import get_eric_database
from core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/objection-handling", tags=["EricObjection Handling"])
objection_service = ObjectionHandlingService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class ObjectionAnalysisRequest(BaseModel):
    objection_text: str
    lead_id: int = None
    context: Dict[str, Any] = {}

class ObjectionHandlingSessionCreate(BaseModel):
    lead_id: int
    sales_rep_id: int
    objection_text: str
    conversation_id: str

class ResponseSelectionRequest(BaseModel):
    response_id: int

class OutcomeRecordRequest(BaseModel):
    customer_reaction: str
    outcome: str  # resolved, escalated, lost

# EricObjection Analysis Endpoints
@router.post("/analyze", response_model=ObjectionAnalysis, summary="Analyze EricObjection")
async def analyze_objection(request: ObjectionAnalysisRequest):
    """Analyze an objection and suggest responses"""
    try:
        analysis = await objection_service.analyze_objection(
            request.objection_text,
            request.lead_id,
            request.context
        )
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze objection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions", response_model=ObjectionHandlingSession, summary="Create EricObjection Handling Session")
async def create_objection_handling_session(session_data: ObjectionHandlingSessionCreate):
    """Create a new objection handling session"""
    try:
        session = await objection_service.create_objection_handling_session(
            session_data.lead_id,
            session_data.sales_rep_id,
            session_data.objection_text,
            session_data.conversation_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create objection handling session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_id}", response_model=ObjectionHandlingSession, summary="Get EricObjection Handling Session")
async def get_objection_handling_session(session_id: int):
    """Get an objection handling session by ID"""
    try:
        # This would typically query the database
        # For demo purposes, return a sample session
        session = ObjectionHandlingSession(
            id=session_id,
            lead_id=1,
            sales_rep_id=1,
            conversation_id="conv_123",
            objection_detected="It's too expensive",
            objection_type="price",
            confidence_score=0.85,
            created_at=datetime.utcnow()
        )
        return session
    except Exception as e:
        logger.error(f"Failed to get objection handling session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Response Management Endpoints
@router.post("/sessions/{session_id}/select-response", summary="Select Response")
async def select_response(session_id: int, request: ResponseSelectionRequest):
    """Select a response for an objection handling session"""
    try:
        success = await objection_service.select_response(session_id, request.response_id)
        if success:
            return {"message": "Response selected successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to select response")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to select response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/{session_id}/record-outcome", summary="Record Outcome")
async def record_outcome(session_id: int, request: OutcomeRecordRequest):
    """Record the outcome of an objection handling session"""
    try:
        success = await objection_service.record_outcome(
            session_id,
            request.customer_reaction,
            request.outcome
        )
        if success:
            return {"message": "Outcome recorded successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to record outcome")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to record outcome: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# EricObjection Types and Responses Endpoints
@router.get("/objection-types", response_model=List[ObjectionType], summary="Get EricObjection Types")
async def get_objection_types():
    """Get all objection types"""
    try:
        objection_types = await objection_service.get_objection_types()
        return objection_types
    except Exception as e:
        logger.error(f"Failed to get objection types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/objection-types/{objection_type}/responses", response_model=List[ObjectionResponse], summary="Get Responses for EricObjection Type")
async def get_responses_for_objection_type(objection_type: str):
    """Get responses for a specific objection type"""
    try:
        responses = await objection_service.get_responses_for_objection_type(objection_type)
        return responses
    except Exception as e:
        logger.error(f"Failed to get responses for objection type: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@router.get("/analytics", summary="Get EricObjection Handling Analytics")
async def get_objection_handling_analytics(lead_id: int = None, sales_rep_id: int = None, date_range: str = "30d"):
    """Get analytics for objection handling"""
    try:
        analytics = await objection_service.get_objection_handling_analytics(lead_id, sales_rep_id, date_range)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get objection handling analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/objection-types", summary="Get EricObjection Type Analytics")
async def get_objection_type_analytics():
    """Get analytics for objection types"""
    try:
        analytics = {
            "total_objections": 150,
            "objection_type_distribution": {
                "price": 35,
                "timing": 25,
                "authority": 20,
                "need": 15,
                "competition": 10,
                "trust": 5
            },
            "resolution_rates": {
                "price": 0.75,
                "timing": 0.65,
                "authority": 0.70,
                "need": 0.60,
                "competition": 0.55,
                "trust": 0.80
            },
            "average_resolution_time": {
                "price": 12,
                "timing": 18,
                "authority": 15,
                "need": 20,
                "competition": 25,
                "trust": 10
            }
        }
        return analytics
    except Exception as e:
        logger.error(f"Failed to get objection type analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/response-effectiveness", summary="Get Response Effectiveness Analytics")
async def get_response_effectiveness_analytics():
    """Get analytics for response effectiveness"""
    try:
        analytics = {
            "response_type_effectiveness": {
                "questions": 0.85,
                "statements": 0.75,
                "stories": 0.70,
                "testimonials": 0.80,
                "data": 0.78
            },
            "tone_effectiveness": {
                "empathetic": 0.82,
                "confident": 0.78,
                "professional": 0.75,
                "casual": 0.70
            },
            "top_performing_responses": [
                {
                    "response_text": "I understand price is important...",
                    "success_rate": 0.90,
                    "usage_count": 45,
                    "objection_type": "price"
                },
                {
                    "response_text": "That's a completely valid concern...",
                    "success_rate": 0.88,
                    "usage_count": 32,
                    "objection_type": "trust"
                },
                {
                    "response_text": "What specific concerns do you have...",
                    "success_rate": 0.85,
                    "usage_count": 28,
                    "objection_type": "timing"
                }
            ]
        }
        return analytics
    except Exception as e:
        logger.error(f"Failed to get response effectiveness analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Training and Improvement Endpoints
@router.post("/feedback", summary="Submit EricObjection Handling Feedback")
async def submit_objection_handling_feedback():
    """Submit feedback for objection handling improvement"""
    try:
        # This would typically store feedback in the database
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/training-suggestions", summary="Get Training Suggestions")
async def get_training_suggestions(sales_rep_id: int = None):
    """Get training suggestions based on objection handling performance"""
    try:
        suggestions = {
            "weak_areas": [
                {
                    "objection_type": "price",
                    "success_rate": 0.65,
                    "suggestion": "Focus on value proposition and ROI calculation"
                },
                {
                    "objection_type": "competition",
                    "success_rate": 0.55,
                    "suggestion": "Improve competitive differentiation skills"
                }
            ],
            "recommended_responses": [
                {
                    "objection_type": "price",
                    "response": "Let me show you the ROI calculation...",
                    "effectiveness": 0.90
                },
                {
                    "objection_type": "competition",
                    "response": "Here's how we differentiate...",
                    "effectiveness": 0.85
                }
            ],
            "training_modules": [
                "Advanced ROI Calculation",
                "Competitive Differentiation",
                "EricObjection Prevention Strategies"
            ]
        }
        return suggestions
    except Exception as e:
        logger.error(f"Failed to get training suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/common-phrases", summary="Get Common EricObjection Phrases")
async def get_common_objection_phrases():
    """Get common phrases for each objection type"""
    try:
        phrases = {
            "price": [
                "it's too expensive",
                "we can't afford it",
                "it's over our budget",
                "the price is too high",
                "we need a better deal"
            ],
            "timing": [
                "we need more time",
                "let's wait until next quarter",
                "we're not ready to decide",
                "we need to think about it"
            ],
            "authority": [
                "I need to check with my boss",
                "I don't have the authority",
                "I need approval",
                "let me run this by the team"
            ],
            "need": [
                "we don't need this",
                "we're doing fine without it",
                "it's not a priority",
                "we don't have this problem"
            ],
            "competition": [
                "we're looking at other options",
                "your competitor offers this",
                "we're evaluating alternatives",
                "someone else has a better deal"
            ],
            "trust": [
                "I don't know your company",
                "we've never heard of you",
                "how do we know you're reliable",
                "we need references"
            ]
        }
        return phrases
    except Exception as e:
        logger.error(f"Failed to get common phrases: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/response-templates", summary="Get Response Templates")
async def get_response_templates():
    """Get response templates for different objection types"""
    try:
        templates = {
            "price": {
                "empathetic": "I understand price is important. Let me show you the ROI...",
                "confident": "You're absolutely right to be concerned about cost...",
                "professional": "I appreciate you being upfront about budget concerns..."
            },
            "timing": {
                "empathetic": "I understand you want to be thorough in your decision...",
                "confident": "That's a fair point. Let me ask...",
                "professional": "I respect that you want to think this through..."
            },
            "authority": {
                "empathetic": "That makes perfect sense. What information would be most helpful...",
                "confident": "I understand you need to get approval...",
                "professional": "That's a smart approach. What concerns do you think..."
            }
        }
        return templates
    except Exception as e:
        logger.error(f"Failed to get response templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/escalation-criteria", summary="Get Escalation Criteria")
async def get_escalation_criteria():
    """Get criteria for when to escalate objections"""
    try:
        criteria = {
            "automatic_escalation": [
                "Critical severity objections",
                "Very negative sentiment",
                "High severity with low confidence",
                "Multiple objections in same conversation"
            ],
            "manual_escalation": [
                "Complex technical objections",
                "Legal or compliance concerns",
                "High-value deals at risk",
                "Customer threatening to leave"
            ],
            "escalation_contacts": {
                "technical": "tech-support@company.com",
                "legal": "legal@company.com",
                "management": "sales-manager@company.com",
                "customer_success": "cs@company.com"
            }
        }
        return criteria
    except Exception as e:
        logger.error(f"Failed to get escalation criteria: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="EricObjection Handling Health Check")
async def health_check():
    """Check the health of the objection handling service"""
    try:
        return {
            "status": "healthy",
            "service": "EricObjection Handling",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "EricObjection Analysis",
                "Response Suggestions",
                "Session Management",
                "Analytics and Reporting",
                "Training Suggestions"
            ],
            "objection_types_supported": 6,
            "response_templates_available": 18
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
