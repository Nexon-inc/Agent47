from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.enhanced_video_voice_service import EnhancedVideoVoiceService

router = APIRouter(prefix="/enhanced-video-voice", tags=["Enhanced Video & Voice Design Tools"])

@router.post("/create-video-template")
async def create_video_template(template_type: str, template_config: Dict[str, Any], brand_guidelines: Dict[str, Any]):
    try:
        service = EnhancedVideoVoiceService()
        await service.initialize()
        return await service.create_video_template(template_type, template_config, brand_guidelines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-voice-template")
async def create_voice_template(voice_type: str, voice_config: Dict[str, Any], audio_requirements: Dict[str, Any]):
    try:
        service = EnhancedVideoVoiceService()
        await service.initialize()
        return await service.create_voice_template(voice_type, voice_config, audio_requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-animation-asset")
async def create_animation_asset(animation_type: str, animation_config: Dict[str, Any], visual_style: Dict[str, Any]):
    try:
        service = EnhancedVideoVoiceService()
        await service.initialize()
        return await service.create_animation_asset(animation_type, animation_config, visual_style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-design-element")
async def create_design_element(element_type: str, element_config: Dict[str, Any], design_guidelines: Dict[str, Any]):
    try:
        service = EnhancedVideoVoiceService()
        await service.initialize()
        return await service.create_design_element(element_type, element_config, design_guidelines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_enhanced_video_voice_analytics(timeframe: str = "30d"):
    try:
        service = EnhancedVideoVoiceService()
        await service.initialize()
        return await service.get_enhanced_video_voice_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
