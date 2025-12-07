from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
from ..services.voice_posts_service import VoicePostsService
from ..deps import get_current_user
from backend.core.database.models import User

router = APIRouter(prefix="/voice-posts", tags=["Voice Posts"])

@router.post("/create")
async def create_voice_post(
    audio_file: UploadFile = File(...),
    post_config: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    voice_posts_service: VoicePostsService = Depends()
):
    """Convert voice recording to a polished social media post"""
    try:
        await voice_posts_service.initialize()
        
        # Read audio file
        audio_data = await audio_file.read()
        audio_format = audio_file.filename.split('.')[-1] if audio_file.filename else 'mp3'
        
        # Default post config if none provided
        if not post_config:
            post_config = {
                "platform": "general",
                "tone": "professional",
                "max_length": 280,
                "max_hashtags": 5
            }
        
        result = await voice_posts_service.create_voice_post(
            current_user.id,
            audio_data,
            audio_format,
            post_config
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def batch_voice_posts(
    audio_files: List[UploadFile] = File(...),
    batch_config: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    voice_posts_service: VoicePostsService = Depends()
):
    """Process multiple voice recordings in batch"""
    try:
        await voice_posts_service.initialize()
        
        audio_files_data = []
        for audio_file in audio_files:
            audio_data = await audio_file.read()
            audio_format = audio_file.filename.split('.')[-1] if audio_file.filename else 'mp3'
            
            audio_files_data.append({
                "file_id": audio_file.filename,
                "audio_data": audio_data,
                "format": audio_format,
                "post_config": batch_config or {}
            })
        
        result = await voice_posts_service.batch_voice_posts(
            current_user.id,
            audio_files_data,
            batch_config or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/template/{template_type}")
async def voice_post_template(
    template_type: str,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    voice_posts_service: VoicePostsService = Depends()
):
    """Create voice post using predefined templates"""
    try:
        await voice_posts_service.initialize()
        
        # Read audio file
        audio_data = await audio_file.read()
        audio_format = audio_file.filename.split('.')[-1] if audio_file.filename else 'mp3'
        
        result = await voice_posts_service.voice_post_template(
            current_user.id,
            template_type,
            audio_data,
            audio_format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_voice_post_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    voice_posts_service: VoicePostsService = Depends()
):
    """Get history of voice-generated posts"""
    try:
        await voice_posts_service.initialize()
        result = await voice_posts_service.get_voice_post_history(current_user.id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_available_templates():
    """Get available voice post templates"""
    return {
        "templates": [
            {
                "type": "product_announcement",
                "description": "Professional product launch announcements",
                "best_for": "LinkedIn, Twitter"
            },
            {
                "type": "behind_scenes",
                "description": "Casual behind-the-scenes content",
                "best_for": "Instagram, TikTok"
            },
            {
                "type": "industry_insight",
                "description": "Professional industry insights",
                "best_for": "LinkedIn"
            },
            {
                "type": "customer_testimonial",
                "description": "Authentic customer stories",
                "best_for": "Instagram, Facebook"
            },
            {
                "type": "event_promotion",
                "description": "Energetic event promotions",
                "best_for": "All platforms"
            }
        ]
    }
