from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ..database import get_joe_database
from core.event_bus.kafka_manager import get_event_bus
from core.cache.redis_manager import get_redis
from ..services.multi_language_research_service import MultiLanguageResearchService

router = APIRouter()

class MultiLanguageResearchRequest(BaseModel):
    query: str = Field(..., description="Research query to translate and analyze")
    target_languages: List[str] = Field(..., description="Target languages for research")
    industry: str = Field(..., description="Industry context for research")

class CulturalContextRequest(BaseModel):
    language: str = Field(..., description="JoeLanguage to analyze")
    industry: str = Field(..., description="Industry context")
    region: str = Field(default=None, description="Specific region")

class TranslationRequest(BaseModel):
    content: str = Field(..., description="Content to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")

class LocalizedReportRequest(BaseModel):
    research_data: Dict[str, Any] = Field(..., description="Research data to localize")
    target_language: str = Field(..., description="Target language for report")

@router.post("/conduct-research")
async def conduct_multi_language_research(
    request: MultiLanguageResearchRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Conduct research in multiple languages with cultural context"""
    try:
        service = MultiLanguageResearchService(db, event_bus, redis)
        result = await service.conduct_multi_language_research(
            query=request.query,
            target_languages=request.target_languages,
            industry=request.industry
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Conducted multi-language research for {len(request.target_languages)} languages in {request.industry}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-language research failed: {str(e)}")

@router.post("/analyze-cultural-context")
async def analyze_cultural_context(
    request: CulturalContextRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze cultural context for specific language and industry"""
    try:
        service = MultiLanguageResearchService(db, event_bus, redis)
        result = await service.analyze_cultural_context(
            language=request.language,
            industry=request.industry,
            region=request.region
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed cultural context for {request.language} in {request.industry}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cultural context analysis failed: {str(e)}")

@router.post("/translate-content")
async def translate_research_content(
    request: TranslationRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Translate research content while preserving context and meaning"""
    try:
        service = MultiLanguageResearchService(db, event_bus, redis)
        result = await service.translate_research_content(
            content=request.content,
            source_language=request.source_language,
            target_language=request.target_language
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Translated content from {request.source_language} to {request.target_language}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content translation failed: {str(e)}")

@router.post("/generate-localized-report")
async def generate_localized_reports(
    request: LocalizedReportRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Generate localized research reports for specific languages"""
    try:
        service = MultiLanguageResearchService(db, event_bus, redis)
        result = await service.generate_localized_reports(
            research_data=request.research_data,
            target_language=request.target_language
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Generated localized report in {request.target_language}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Localized report generation failed: {str(e)}")
