from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.multi_language_service import MultiLanguageService

router = APIRouter(prefix="/multi-language", tags=["Multi-Language JackieCampaign Creation"])

@router.post("/create-campaign")
async def create_multi_language_campaign(campaign_id: str, target_languages: List[str], source_content: Dict[str, Any]):
    try:
        service = MultiLanguageService()
        await service.initialize()
        return await service.create_multi_language_campaign(campaign_id, target_languages, source_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate-content")
async def translate_campaign_content(campaign_id: str, content: str, target_language: str):
    try:
        service = MultiLanguageService()
        await service.initialize()
        return await service.translate_campaign_content(campaign_id, content, target_language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adapt-culturally")
async def adapt_content_culturally(campaign_id: str, content: str, target_culture: str):
    try:
        service = MultiLanguageService()
        await service.initialize()
        return await service.adapt_content_culturally(campaign_id, content, target_culture)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_multi_language_analytics(timeframe: str = "30d"):
    try:
        service = MultiLanguageService()
        await service.initialize()
        return await service.get_multi_language_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
