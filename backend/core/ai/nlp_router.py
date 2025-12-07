"""
NLP Router

This module provides NLP processing endpoints for agent chat functionality.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..authentication.auth_manager import get_current_active_user
from ..database.models import User
from .ai_service_manager import AIServiceManager
from ..logs import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/nlp", tags=["NLP"])

class NLPProcessRequest(BaseModel):
    """Request model for NLP processing"""
    text: str
    context: Optional[Dict[str, Any]] = None
    agent: Optional[str] = None
    user_id: Optional[int] = None

class NLPProcessResponse(BaseModel):
    """Response model for NLP processing"""
    success: bool
    processed_text: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/process", response_model=NLPProcessResponse)
async def process_nlp_text(
    request: NLPProcessRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process text using NLP services (Chutes API integration)
    
    This endpoint processes user input text and returns:
    - Intent detection
    - Entity extraction
    - Sentiment analysis
    - Processed response
    """
    try:
        logger.info(f"Processing NLP request for user {current_user.id}: {request.text[:100]}...")
        
        # Initialize AI service manager
        ai_manager = AIServiceManager()
        await ai_manager.initialize()
        
        # Prepare messages for LLM processing
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI assistant helping with {request.agent or 'general'} tasks. 
                Analyze the user's message and provide:
                1. Intent classification (greeting, question, request, complaint, etc.)
                2. Key entities mentioned
                3. Sentiment analysis (positive, negative, neutral)
                4. A helpful response
                
                Context: {request.context or 'No additional context'}
                Agent: {request.agent or 'General'}
                """
            },
            {
                "role": "user", 
                "content": request.text
            }
        ]
        
        # Process with AI service
        ai_request = {
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        ai_response = await ai_manager.generate_text(ai_request)
        
        if ai_response.success:
            # Parse the AI response to extract structured data
            response_text = ai_response.text_content or ""
            
            # Simple intent detection based on keywords
            intent = _detect_intent(request.text)
            
            # Simple sentiment analysis
            sentiment = _analyze_sentiment(request.text)
            
            # Extract entities (simplified)
            entities = _extract_entities(request.text)
            
            return NLPProcessResponse(
                success=True,
                processed_text=response_text,
                intent=intent,
                entities=entities,
                sentiment=sentiment,
                confidence=0.8,
                metadata={
                    "agent": request.agent,
                    "user_id": current_user.id,
                    "processing_time": "fast",
                    "model": "grok-llm"
                }
            )
        else:
            logger.error(f"NLP processing failed: {ai_response.error}")
            return NLPProcessResponse(
                success=False,
                error=f"AI processing failed: {ai_response.error}"
            )
            
    except Exception as e:
        logger.error(f"NLP processing error: {str(e)}", exc_info=True)
        return NLPProcessResponse(
            success=False,
            error=f"Internal server error: {str(e)}"
        )

def _detect_intent(text: str) -> str:
    """Simple intent detection based on keywords"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "greeting"
    elif any(word in text_lower for word in ["help", "what can you do", "capabilities", "features"]):
        return "help_request"
    elif any(word in text_lower for word in ["create", "make", "generate", "write"]):
        return "creation_request"
    elif any(word in text_lower for word in ["analyze", "analysis", "report", "insights"]):
        return "analysis_request"
    elif any(word in text_lower for word in ["schedule", "plan", "organize", "calendar"]):
        return "scheduling_request"
    elif any(word in text_lower for word in ["problem", "issue", "error", "bug", "fix"]):
        return "problem_report"
    elif "?" in text:
        return "question"
    else:
        return "general"

def _analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis based on keywords"""
    text_lower = text.lower()
    
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "like", "happy", "pleased"]
    negative_words = ["bad", "terrible", "awful", "hate", "dislike", "angry", "frustrated", "disappointed", "sad", "upset"]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def _extract_entities(text: str) -> Dict[str, Any]:
    """Simple entity extraction"""
    entities = {
        "platforms": [],
        "tools": [],
        "time_mentions": [],
        "numbers": []
    }
    
    # Extract platform mentions
    platforms = ["facebook", "instagram", "twitter", "linkedin", "tiktok", "youtube", "pinterest"]
    for platform in platforms:
        if platform in text.lower():
            entities["platforms"].append(platform)
    
    # Extract tool mentions
    tools = ["analytics", "scheduling", "content", "ads", "automation", "chat", "email"]
    for tool in tools:
        if tool in text.lower():
            entities["tools"].append(tool)
    
    # Extract time mentions
    time_words = ["today", "tomorrow", "yesterday", "week", "month", "year", "morning", "afternoon", "evening"]
    for time_word in time_words:
        if time_word in text.lower():
            entities["time_mentions"].append(time_word)
    
    # Extract numbers
    import re
    numbers = re.findall(r'\d+', text)
    entities["numbers"] = numbers
    
    return entities

@router.get("/health")
async def nlp_health_check():
    """Health check for NLP service"""
    try:
        ai_manager = AIServiceManager()
        await ai_manager.initialize()
        
        # Test with a simple request
        test_request = {
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = await ai_manager.generate_text(test_request)
        
        return {
            "status": "healthy" if response.success else "unhealthy",
            "service": "nlp",
            "ai_service_status": "connected" if response.success else "disconnected",
            "timestamp": "2025-01-15T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"NLP health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "nlp", 
            "error": str(e),
            "timestamp": "2025-01-15T12:00:00Z"
        }
