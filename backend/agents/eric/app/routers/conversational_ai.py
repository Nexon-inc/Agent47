from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.conversational_ai_service import ConversationalAIService
from ..database import get_db

router = APIRouter(prefix="/conversational-ai", tags=["Conversational AI"])
conversational_ai_service = ConversationalAIService()

class ChatMessageRequest(BaseModel):
    lead_id: int
    message: str
    context: Dict[str, Any]
    channel: str = "chat"

class VoiceInteractionRequest(BaseModel):
    lead_id: int
    context: Dict[str, Any]

class DemoSchedulingRequest(BaseModel):
    lead_id: int
    demo_preferences: Dict[str, Any]

class ProductQuestionRequest(BaseModel):
    lead_id: int
    question: str
    context: Dict[str, Any]

class ConversationHistoryRequest(BaseModel):
    lead_id: int
    limit: int = 50

@router.post("/process-chat")
async def process_chat_message(request: ChatMessageRequest):
    """Process incoming chat message and generate response"""
    try:
        result = await conversational_ai_service.process_chat_message(
            lead_id=request.lead_id,
            message=request.message,
            context=request.context,
            channel=request.channel
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

@router.post("/voice-interaction")
async def handle_voice_interaction(
    request: VoiceInteractionRequest,
    audio_file: UploadFile = File(...)
):
    """Handle voice interaction and generate voice response"""
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        result = await conversational_ai_service.handle_voice_interaction(
            lead_id=request.lead_id,
            audio_data=audio_data,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle voice interaction: {str(e)}")

@router.post("/schedule-demo")
async def schedule_demo(request: DemoSchedulingRequest):
    """Schedule a demo for the lead"""
    try:
        result = await conversational_ai_service.schedule_demo(
            lead_id=request.lead_id,
            demo_preferences=request.demo_preferences
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule demo: {str(e)}")

@router.post("/answer-product-question")
async def answer_product_questions(request: ProductQuestionRequest):
    """Answer product-related questions"""
    try:
        result = await conversational_ai_service.answer_product_questions(
            lead_id=request.lead_id,
            question=request.question,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer product question: {str(e)}")

@router.get("/conversation-history")
async def get_conversation_history(
    lead_id: int,
    limit: int = 50
):
    """Get conversation history for lead"""
    try:
        result = await conversational_ai_service.get_conversation_history(
            lead_id=lead_id,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@router.get("/intent-analysis")
async def analyze_message_intent(message: str, context: Dict[str, Any] = {}):
    """Analyze message intent and sentiment"""
    try:
        # This would typically be part of the chat processing, but can be called separately
        analysis_prompt = f"""
        Analyze this sales conversation message and determine:
        1. Intent (demo_request, product_question, pricing_inquiry, objection, general_inquiry)
        2. Sentiment (positive, neutral, negative)
        3. Urgency level (low, medium, high)
        4. Engagement level (low, medium, high)
        
        Message: "{message}"
        Context: {context}
        
        Provide analysis in JSON format.
        """
        
        # For now, return a basic analysis
        return {
            "message": message,
            "intent": "general_inquiry",
            "confidence": 0.7,
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "urgency": "medium",
            "engagement": "medium",
            "engagement_score": 0.5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze message intent: {str(e)}")

@router.get("/response-templates")
async def get_response_templates():
    """Get available response templates"""
    return {
        "demo_request": {
            "template": "I'd be happy to schedule a demo for you! What would be the best time for a 30-minute demo?",
            "suggested_actions": ["schedule_demo", "send_case_study"],
            "next_steps": ["Confirm demo time", "Send calendar invitation"]
        },
        "product_question": {
            "template": "Great question! Let me provide you with some relevant information about our product.",
            "suggested_actions": ["send_product_info", "schedule_demo", "connect_specialist"],
            "next_steps": ["Follow up with product materials"]
        },
        "pricing_inquiry": {
            "template": "I understand you're interested in our pricing. Our solutions are tailored to your specific needs.",
            "suggested_actions": ["schedule_discovery_call", "send_pricing_guide"],
            "next_steps": ["Schedule discovery call", "Prepare customized quote"]
        },
        "objection": {
            "template": "I appreciate you sharing that concern. Let me address this by sharing how other companies have successfully overcome similar challenges.",
            "suggested_actions": ["share_case_study", "customer_reference", "schedule_call"],
            "next_steps": ["Provide case study", "Arrange customer reference call"]
        },
        "general_inquiry": {
            "template": "Thank you for reaching out! I'm here to help you learn more about how our solution can benefit your business.",
            "suggested_actions": ["schedule_demo", "send_information", "connect_specialist"],
            "next_steps": ["Understand specific needs", "Provide relevant information"]
        }
    }

@router.get("/demo-slots")
async def get_available_demo_slots():
    """Get available demo time slots"""
    # This would typically integrate with a calendar system
    return {
        "available_slots": [
            {
                "date": "2024-01-15",
                "time": "10:00 AM",
                "timezone": "UTC",
                "duration": "30 minutes",
                "type": "product_demo"
            },
            {
                "date": "2024-01-15",
                "time": "2:00 PM",
                "timezone": "UTC",
                "duration": "30 minutes",
                "type": "product_demo"
            },
            {
                "date": "2024-01-16",
                "time": "11:00 AM",
                "timezone": "UTC",
                "duration": "30 minutes",
                "type": "product_demo"
            }
        ],
        "demo_types": [
            {
                "type": "product_demo",
                "duration": "30 minutes",
                "description": "Comprehensive product demonstration"
            },
            {
                "type": "technical_demo",
                "duration": "45 minutes",
                "description": "Technical deep-dive and integration discussion"
            },
            {
                "type": "executive_briefing",
                "duration": "20 minutes",
                "description": "High-level executive overview"
            }
        ]
    }

@router.get("/health")
async def health_check():
    """Health check for conversational AI service"""
    return {
        "status": "healthy",
        "service": "conversational_ai",
        "timestamp": datetime.now().isoformat()
    }
