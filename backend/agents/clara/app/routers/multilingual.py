from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.multilingual_service import MultilingualService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = None

class LocalizedResponseRequest(BaseModel):
    response_template: str
    language: str
    context: Optional[Dict[str, Any]] = None

class LanguagePreferenceRequest(BaseModel):
    language: str

async def get_multilingual_service() -> MultilingualService:
    """Dependency to get multilingual service"""
    service = MultilingualService()
    await service.initialize()
    return service

@router.post("/detect", response_model=Dict[str, Any])
async def detect_language(
    request: TranslationRequest,
    customer_id: Optional[int] = Query(None),
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Detect language of input text"""
    try:
        result = await multilingual_service.detect_language(
            text=request.text,
            customer_id=customer_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate", response_model=Dict[str, Any])
async def translate_text(
    request: TranslationRequest,
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Translate text to target language"""
    try:
        result = await multilingual_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/localized-response", response_model=Dict[str, Any])
async def get_localized_response(
    request: LocalizedResponseRequest,
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Get localized response based on language and context"""
    try:
        result = await multilingual_service.get_localized_response(
            response_template=request.response_template,
            language=request.language,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages", response_model=Dict[str, Any])
async def get_supported_languages(
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Get list of supported languages"""
    try:
        result = await multilingual_service.get_supported_languages()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/customers/{customer_id}/language", response_model=Dict[str, Any])
async def update_customer_language_preference(
    customer_id: int,
    request: LanguagePreferenceRequest,
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Update customer's language preference"""
    try:
        result = await multilingual_service.update_customer_language_preference(
            customer_id=customer_id,
            language=request.language
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/language", response_model=Dict[str, Any])
async def get_customer_language_preference(
    customer_id: int,
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Get customer's language preference"""
    try:
        # Get customer language preference from the service
        result = await multilingual_service.get_customer_language_preference(customer_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_multilingual_health(
    multilingual_service: MultilingualService = Depends(get_multilingual_service)
):
    """Check health status of multilingual service"""
    try:
        return {
            "success": True,
            "service": "multilingual",
            "status": "healthy",
            "supported_languages_count": len(multilingual_service._supported_languages),
            "translation_cache_size": len(multilingual_service._translation_cache),
            "message": "Multilingual service is operational"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "multilingual",
            "status": "error",
            "error": str(e)
        }
