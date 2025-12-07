from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.voice_video_marketing_service import VoiceVideoMarketingService

router = APIRouter(prefix="/voice-video-marketing", tags=["Voice & Video Marketing"])
from pydantic import BaseModel


class CreateVoiceoverRequest(BaseModel):
    text: str
    voice_type: str
    language: str
    speed: float = 1.0
    tone: str = "neutral"


class CreateVideoRequest(BaseModel):
    title: str
    description: Optional[str] = None
    video_type: str
    duration: int
    content_elements: List[Dict[str, Any]]
    voiceover_id: Optional[str] = None


class VideoTemplateRequest(BaseModel):
    template_type: str
    customization_data: Dict[str, Any]
    brand_elements: Optional[Dict[str, Any]] = None


class VoiceoverResponse(BaseModel):
    id: str
    text: str
    voice_type: str
    language: str
    audio_url: str
    duration: float
    created_at: datetime


class VideoResponse(BaseModel):
    id: str
    title: str
    video_type: str
    duration: int
    video_url: str
    thumbnail_url: str
    status: str
    created_at: datetime

@router.post("/voiceovers", response_model=VoiceoverResponse)
async def create_voiceover(
    request: CreateVoiceoverRequest,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.create_voiceover(
            request.text,
            request.voice_type,
            request.language,
            request.speed,
            request.tone
        )
        return VoiceoverResponse(
            id=result["id"],
            text=result["text"],
            voice_type=result["voice_type"],
            language=result["language"],
            audio_url=result["audio_url"],
            duration=result["duration"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voiceovers/{voiceover_id}", response_model=VoiceoverResponse)
async def get_voiceover(voiceover_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.get_voiceover(voiceover_id)
        if not result:
            raise HTTPException(status_code=404, detail="Voiceover not found")
        return VoiceoverResponse(
            id=result["id"],
            text=result["text"],
            voice_type=result["voice_type"],
            language=result["language"],
            audio_url=result["audio_url"],
            duration=result["duration"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voiceovers", response_model=List[VoiceoverResponse])
async def list_voiceovers(
    voice_type: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        results = service.list_voiceovers(voice_type, language, limit, offset)
        return [
            VoiceoverResponse(
                id=result["id"],
                text=result["text"],
                voice_type=result["voice_type"],
                language=result["language"],
                audio_url=result["audio_url"],
                duration=result["duration"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/videos", response_model=VideoResponse)
async def create_video(
    request: CreateVideoRequest,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.create_video(
            request.title,
            request.description,
            request.video_type,
            request.duration,
            request.content_elements,
            request.voiceover_id
        )
        return VideoResponse(
            id=result["id"],
            title=result["title"],
            video_type=result["video_type"],
            duration=result["duration"],
            video_url=result["video_url"],
            thumbnail_url=result["thumbnail_url"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.get_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Video not found")
        return VideoResponse(
            id=result["id"],
            title=result["title"],
            video_type=result["video_type"],
            duration=result["duration"],
            video_url=result["video_url"],
            thumbnail_url=result["thumbnail_url"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos", response_model=List[VideoResponse])
async def list_videos(
    video_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        results = service.list_videos(video_type, status, limit, offset)
        return [
            VideoResponse(
                id=result["id"],
                title=result["title"],
                video_type=result["video_type"],
                duration=result["duration"],
                video_url=result["video_url"],
                thumbnail_url=result["thumbnail_url"],
                status=result["status"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/videos/{video_id}/render")
async def render_video(video_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.render_video(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video rendering started", "status": result["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}/status")
async def get_video_status(video_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        status = service.get_video_status(video_id)
        if not status:
            raise HTTPException(status_code=404, detail="Video not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def create_video_template(
    request: VideoTemplateRequest,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.create_video_template(
            request.template_type,
            request.customization_data,
            request.brand_elements
        )
        return {
            "message": "Video template created successfully",
            "template_id": result["template_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_video_templates(
    template_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        templates = service.list_video_templates(template_type, limit, offset)
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}")
async def get_video_template(template_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        template = service.get_video_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audio/analyze")
async def analyze_audio(
    audio_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.analyze_audio(audio_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/video/analyze")
async def analyze_video(
    video_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.analyze_video(video_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices/available")
async def get_available_voices(db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        voices = service.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages/supported")
async def get_supported_languages(db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        languages = service.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content/optimize")
async def optimize_content(
    content_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.optimize_content(content_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_voice_video_analytics_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        overview = service.get_voice_video_analytics_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/performance")
async def get_content_performance(
    content_type: Optional[str] = None,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        performance = service.get_content_performance(content_type, timeframe)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/brand-voice/setup")
async def setup_brand_voice(
    brand_voice_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.setup_brand_voice(brand_voice_data)
        return {
            "message": "Brand voice setup successfully",
            "brand_voice_id": result["brand_voice_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brand-voice")
async def get_brand_voice(db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        brand_voice = service.get_brand_voice()
        return brand_voice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/accessibility/generate")
async def generate_accessible_content(
    content_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.generate_accessible_content(content_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/localization/translate")
async def translate_content(
    translation_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.translate_content(translation_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/formats/supported")
async def get_supported_formats(db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        formats = service.get_supported_formats()
        return {"formats": formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/process")
async def process_batch_content(
    batch_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = VoiceVideoMarketingService(db)
    try:
        result = service.process_batch_content(batch_data)
        return {
            "message": "Batch processing initiated",
            "batch_id": result["batch_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    service = VoiceVideoMarketingService(db)
    try:
        status = service.get_batch_status(batch_id)
        if not status:
            raise HTTPException(status_code=404, detail="Batch not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
