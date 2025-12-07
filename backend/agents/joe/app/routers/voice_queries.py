from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.voice_queries_service import VoiceQueriesService

router = APIRouter(prefix="/voice-queries", tags=["Voice Queries"])

class VoiceQueryRequest(BaseModel):
    voice_input: str = Field(..., description="Voice input text to process")
    query_context: Dict[str, Any] = Field(default={}, description="Additional context for the query")

class QueryHistoryRequest(BaseModel):
    limit: int = Field(default=10, description="Number of recent queries to retrieve")

# Dependency
async def get_voice_queries_service() -> VoiceQueriesService:
    service = VoiceQueriesService()
    await service.initialize()
    return service

@router.post("/process-query")
async def process_voice_query(
    request: VoiceQueryRequest,
    service: VoiceQueriesService = Depends(get_voice_queries_service)
):
    """Process voice-based research queries"""
    try:
        result = await service.process_voice_query(
            user_id=1,  # TODO: Get from authentication
            voice_input=request.voice_input,
            query_context=request.query_context
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["query_data"],
                "message": "Voice query processed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Voice query processing failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice query: {str(e)}"
        )

@router.post("/get-history")
async def get_voice_query_history(
    request: QueryHistoryRequest,
    service: VoiceQueriesService = Depends(get_voice_queries_service)
):
    """Get user's voice query history"""
    try:
        result = await service.get_voice_query_history(
            user_id=1,  # TODO: Get from authentication
            limit=request.limit
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history_data"],
                "message": "Voice query history retrieved successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get query history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice query history: {str(e)}"
        )

@router.get("/supported-languages")
async def get_supported_languages(service: VoiceQueriesService = Depends(get_voice_queries_service)):
    """Get supported languages for voice queries"""
    languages = [
        {
            "code": "en",
            "name": "English",
            "description": "English language support",
            "accuracy": "95%",
            "features": ["Natural language processing", "Context understanding", "Multi-accent support"]
        },
        {
            "code": "es",
            "name": "Spanish",
            "description": "Spanish language support",
            "accuracy": "92%",
            "features": ["Latin American variants", "Formal/informal recognition", "Regional accents"]
        },
        {
            "code": "fr",
            "name": "French",
            "description": "French language support",
            "accuracy": "90%",
            "features": ["European and Canadian variants", "Formal language support", "Accent recognition"]
        },
        {
            "code": "de",
            "name": "German",
            "description": "German language support",
            "accuracy": "88%",
            "features": ["Standard German", "Regional dialects", "Technical terminology"]
        },
        {
            "code": "zh",
            "name": "Chinese",
            "description": "Chinese language support",
            "accuracy": "85%",
            "features": ["Mandarin and Cantonese", "Simplified and Traditional", "Tone recognition"]
        }
    ]
    
    return {
        "status": "success",
        "data": languages,
        "message": f"Retrieved {len(languages)} supported languages"
    }
