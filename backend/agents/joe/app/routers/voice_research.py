from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.voice_research_service import VoiceResearchService

router = APIRouter(prefix="/voice-research", tags=["Voice Research"])

class VoiceQueryRequest(BaseModel):
    audio_data: str = Field(..., description="Audio data for voice query")
    query_type: str = Field(default="general", description="Type of query")

# Dependency
async def get_voice_research_service() -> VoiceResearchService:
    service = VoiceResearchService()
    await service.initialize()
    return service

@router.post("/process-query")
async def process_voice_query(
    request: VoiceQueryRequest,
    service: VoiceResearchService = Depends(get_voice_research_service)
):
    """Process voice query and convert to research request"""
    try:
        result = await service.process_voice_query(
            user_id=1,  # TODO: Get from authentication
            audio_data=request.audio_data,
            query_type=request.query_type
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

@router.get("/commands")
async def get_voice_commands(service: VoiceResearchService = Depends(get_voice_research_service)):
    """Get available voice commands for research"""
    try:
        result = await service.get_voice_commands(
            user_id=1  # TODO: Get from authentication
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["commands"],
                "message": f"Retrieved {result['total_commands']} voice commands"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get voice commands: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice commands: {str(e)}"
        )

@router.get("/supported-languages")
async def get_supported_languages(service: VoiceResearchService = Depends(get_voice_research_service)):
    """Get supported languages for voice research"""
    languages = [
        {
            "code": "en",
            "name": "English",
            "support_level": "Full",
            "accuracy": "95%"
        },
        {
            "code": "es",
            "name": "Spanish",
            "support_level": "Full",
            "accuracy": "92%"
        },
        {
            "code": "fr",
            "name": "French",
            "support_level": "Full",
            "accuracy": "90%"
        },
        {
            "code": "de",
            "name": "German",
            "support_level": "Full",
            "accuracy": "88%"
        }
    ]
    
    return {
        "status": "success",
        "data": languages,
        "message": f"Retrieved {len(languages)} supported languages"
    }
