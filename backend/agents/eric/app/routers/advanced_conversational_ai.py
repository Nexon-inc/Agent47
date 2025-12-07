from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.advanced_conversational_ai_service import AdvancedConversationalAIService, ConversationContext, IndustryQuery, ConversationResponse
from ..database import get_eric_database
from backend.core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/advanced-conversational-ai", tags=["Advanced Conversational AI"])
conversational_ai_service = AdvancedConversationalAIService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class ConversationRequest(BaseModel):
    user_message: str
    conversation_id: str
    user_id: int
    lead_id: int = None
    deal_id: int = None
    industry: str = None

class IndustryQueryRequest(BaseModel):
    query: str
    industry: str
    user_id: int

class ConversationInsightsRequest(BaseModel):
    conversation_id: str

# Conversation Endpoints
@router.post("/conversations", response_model=ConversationResponse, summary="Process Conversation")
async def process_conversation(request: ConversationRequest):
    """Process user message and generate contextual response"""
    try:
        # Get or create conversation context
        context = await conversational_ai_service.get_conversation_context(request.conversation_id)
        
        if not context:
            context = ConversationContext(
                conversation_id=request.conversation_id,
                user_id=request.user_id,
                lead_id=request.lead_id,
                deal_id=request.deal_id,
                industry=request.industry,
                conversation_history=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        # Process conversation
        response = await conversational_ai_service.process_conversation(request.user_message, context)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversations/{conversation_id}/context", response_model=ConversationContext, summary="Get Conversation Context")
async def get_conversation_context(conversation_id: str):
    """Get conversation context by ID"""
    try:
        context = await conversational_ai_service.get_conversation_context(conversation_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Conversation context not found")
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/conversations/{conversation_id}/context", summary="Update Conversation Context")
async def update_conversation_context(conversation_id: str, context: ConversationContext):
    """Update conversation context"""
    try:
        success = await conversational_ai_service.update_conversation_context(context)
        
        if success:
            return {"message": "Conversation context updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update conversation context")
            
    except Exception as e:
        logger.error(f"Failed to update conversation context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Industry Query Endpoints
@router.post("/industry-queries", response_model=IndustryQuery, summary="Handle Industry-Specific Query")
async def handle_industry_query(request: IndustryQueryRequest):
    """Handle industry-specific queries with detailed responses"""
    try:
        query = await conversational_ai_service.handle_industry_specific_query(
            request.query,
            request.industry,
            request.user_id
        )
        return query
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to handle industry query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics and Insights Endpoints
@router.post("/conversations/insights", summary="Get Conversation Insights")
async def get_conversation_insights(request: ConversationInsightsRequest):
    """Get insights from conversation analysis"""
    try:
        insights = await conversational_ai_service.get_conversation_insights(request.conversation_id)
        return insights
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get conversation insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/conversations/{conversation_id}/sentiment", summary="Analyze Conversation Sentiment")
async def analyze_conversation_sentiment(conversation_id: str):
    """Analyze conversation sentiment and engagement"""
    try:
        context = await conversational_ai_service.get_conversation_context(conversation_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Conversation context not found")
        
        sentiment_analysis = await conversational_ai_service.analyze_conversation_sentiment(
            context.conversation_history
        )
        
        return sentiment_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze conversation sentiment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Knowledge Base Endpoints
@router.get("/knowledge-base/{industry}", summary="Get Industry Knowledge Base")
async def get_industry_knowledge_base(industry: str):
    """Get industry-specific knowledge base"""
    try:
        knowledge = await conversational_ai_service.get_industry_knowledge_base(industry)
        return knowledge
        
    except Exception as e:
        logger.error(f"Failed to get industry knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/industries", summary="Get Supported Industries")
async def get_supported_industries():
    """Get list of supported industries"""
    try:
        industries = [
            "technology",
            "healthcare", 
            "finance",
            "manufacturing",
            "retail",
            "education",
            "real_estate",
            "consulting"
        ]
        
        return {
            "industries": industries,
            "total_count": len(industries)
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported industries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/query-types", summary="Get Supported Query Types")
async def get_supported_query_types():
    """Get list of supported query types"""
    try:
        query_types = [
            "pricing",
            "technical", 
            "compliance",
            "support",
            "comparison",
            "timeline",
            "general"
        ]
        
        return {
            "query_types": query_types,
            "total_count": len(query_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported query types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/intents", summary="Get Supported Intents")
async def get_supported_intents():
    """Get list of supported conversation intents"""
    try:
        intents = [
            "pricing_inquiry",
            "technical_inquiry",
            "general_inquiry",
            "support_request",
            "comparison_request",
            "timeline_inquiry",
            "objection_handling",
            "closing_request"
        ]
        
        return {
            "intents": intents,
            "total_count": len(intents)
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported intents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="Advanced Conversational AI Health Check")
async def health_check():
    """Check the health of the advanced conversational AI service"""
    try:
        # Test basic functionality
        test_context = ConversationContext(
            conversation_id="test",
            user_id=1,
            industry="technology",
            conversation_history=[]
        )
        
        return {
            "status": "healthy",
            "service": "Advanced Conversational AI",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "Conversation Processing",
                "Industry-Specific Queries",
                "Sentiment Analysis",
                "Intent Detection",
                "Context Management",
                "Knowledge Base Access"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
