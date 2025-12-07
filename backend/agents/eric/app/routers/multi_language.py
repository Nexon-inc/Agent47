from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.multi_language_service import MultiLanguageService, TranslationRequest, TranslationResponse, LocalizedContent, LanguageConfig, CulturalInsight
from ..database import get_eric_database
from backend.core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/multi-language", tags=["Multi-Language Support"])
multi_language_service = MultiLanguageService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class LocalizedContentCreate(BaseModel):
    content_type: str
    base_content: Dict[str, str]
    target_language: str

class LocalizedPitchRequest(BaseModel):
    base_pitch: str
    target_language: str
    industry: str = None

# Translation Endpoints
@router.post("/translate", response_model=TranslationResponse, summary="Translate Text")
async def translate_text(request: TranslationRequest):
    """Translate text with cultural adaptation"""
    try:
        response = await multi_language_service.translate_text(request)
        return response
    except Exception as e:
        logger.error(f"Failed to translate text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/detect-language", summary="Detect Language")
async def detect_language(text: str):
    """Detect the language of text"""
    try:
        result = await multi_language_service.detect_language(text)
        return result
    except Exception as e:
        logger.error(f"Failed to detect language: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Localized Content Endpoints
@router.post("/localized-content", response_model=LocalizedContent, summary="Create Localized Content")
async def create_localized_content(request: LocalizedContentCreate):
    """Create localized content for a specific language"""
    try:
        content = await multi_language_service.create_localized_content(
            request.content_type,
            request.base_content,
            request.target_language
        )
        return content
    except Exception as e:
        logger.error(f"Failed to create localized content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/localized-pitch", summary="Generate Localized Pitch")
async def generate_localized_pitch(request: LocalizedPitchRequest):
    """Generate a localized sales pitch"""
    try:
        pitch = await multi_language_service.generate_localized_pitch(
            request.base_pitch,
            request.target_language,
            request.industry
        )
        return pitch
    except Exception as e:
        logger.error(f"Failed to generate localized pitch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Language Configuration Endpoints
@router.get("/languages", response_model=List[LanguageConfig], summary="Get Supported Languages")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        languages = await multi_language_service.get_supported_languages()
        return languages
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/languages/{language_code}", response_model=LanguageConfig, summary="Get Language Config")
async def get_language_config(language_code: str):
    """Get configuration for a specific language"""
    try:
        languages = await multi_language_service.get_supported_languages()
        language = next((lang for lang in languages if lang.language_code == language_code), None)
        
        if not language:
            raise HTTPException(status_code=404, detail="Language not found")
        
        return language
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get language config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Cultural Insights Endpoints
@router.get("/cultural-insights/{country}", response_model=CulturalInsight, summary="Get Cultural Insights")
async def get_cultural_insights(country: str):
    """Get cultural insights for a specific country"""
    try:
        insights = await multi_language_service.get_cultural_insights(country)
        return insights
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get cultural insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@router.get("/analytics", summary="Get Localization Analytics")
async def get_localization_analytics(date_range: str = "30d"):
    """Get analytics for localization usage"""
    try:
        analytics = await multi_language_service.get_localization_analytics(date_range)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get localization analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="Multi-Language Support Health Check")
async def health_check():
    """Check the health of the multi-language support service"""
    try:
        return {
            "status": "healthy",
            "service": "Multi-Language Support",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "Text Translation",
                "Language Detection",
                "Cultural Adaptation",
                "Localized Content Creation",
                "Cultural Insights"
            ],
            "supported_languages": 10
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
