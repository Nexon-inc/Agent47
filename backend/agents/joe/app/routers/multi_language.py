from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.multi_language_service import MultiLanguageService

router = APIRouter(prefix="/multi-language", tags=["Multi-Language Research"])

class TranslationRequest(BaseModel):
    query: str = Field(..., description="Query to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")

class LocalizedInsightsRequest(BaseModel):
    market_region: str = Field(..., description="Market region to analyze")
    language: str = Field(..., description="Language for analysis")

# Dependency
async def get_multi_language_service() -> MultiLanguageService:
    service = MultiLanguageService()
    await service.initialize()
    return service

@router.post("/translate")
async def translate_research_query(
    request: TranslationRequest,
    service: MultiLanguageService = Depends(get_multi_language_service)
):
    """Translate research query between languages"""
    try:
        result = await service.translate_research_query(
            user_id=1,  # TODO: Get from authentication
            query=request.query,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["translation_data"],
                "message": f"Query translated from {request.source_language} to {request.target_language}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate query: {str(e)}"
        )

@router.post("/localized-insights")
async def analyze_localized_insights(
    request: LocalizedInsightsRequest,
    service: MultiLanguageService = Depends(get_multi_language_service)
):
    """Analyze insights specific to a local market"""
    try:
        result = await service.analyze_localized_insights(
            user_id=1,  # TODO: Get from authentication
            market_region=request.market_region,
            language=request.language
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights"],
                "message": f"Retrieved {result['total_insights']} localized insights for {request.market_region}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Localized insights analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze localized insights: {str(e)}"
        )

@router.get("/supported-languages")
async def get_supported_languages(service: MultiLanguageService = Depends(get_multi_language_service)):
    """Get supported languages for research"""
    languages = [
        {
            "code": "en",
            "name": "English",
            "region": "Global",
            "support_level": "Full"
        },
        {
            "code": "es",
            "name": "Spanish",
            "region": "Latin America, Spain",
            "support_level": "Full"
        },
        {
            "code": "fr",
            "name": "French",
            "region": "France, Canada, Africa",
            "support_level": "Full"
        },
        {
            "code": "de",
            "name": "German",
            "region": "Germany, Austria, Switzerland",
            "support_level": "Full"
        },
        {
            "code": "zh",
            "name": "Chinese",
            "region": "China, Taiwan, Singapore",
            "support_level": "Partial"
        },
        {
            "code": "ja",
            "name": "Japanese",
            "region": "Japan",
            "support_level": "Partial"
        }
    ]
    
    return {
        "status": "success",
        "data": languages,
        "message": f"Retrieved {len(languages)} supported languages"
    }
