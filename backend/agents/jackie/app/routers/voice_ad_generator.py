from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.voice_ad_generator_service import VoiceAdGeneratorService

router = APIRouter(prefix="/voice-ad-generator", tags=["Voice Ad Generator"])

@router.post("/generate-voice-ad")
def generate_voice_ad(ad_brief: Dict[str, Any], platform: str = "spotify", duration: str = "30s", 
                     db: Session = Depends(get_db)):
    service = VoiceAdGeneratorService(db)
    return service.generate_voice_ad(ad_brief, platform, duration)

@router.post("/voice-script")
def create_voice_script(script_brief: Dict[str, Any], voice_style: str, target_audience: str, 
                       db: Session = Depends(get_db)):
    service = VoiceAdGeneratorService(db)
    return service.create_voice_script(script_brief, voice_style, target_audience)

@router.get("/analytics")
def get_voice_ad_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = VoiceAdGeneratorService(db)
    return service.get_voice_ad_analytics(timeframe)
