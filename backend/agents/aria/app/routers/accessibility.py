from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List
from ..services.accessibility_service import AccessibilityService
from ..deps import get_current_user
from backend.core.database.models import User

router = APIRouter(prefix="/accessibility", tags=["Accessibility"])

@router.post("/generate-video-captions")
async def generate_video_captions(
    video_file: UploadFile = File(...),
    language: str = "en",
    current_user: User = Depends(get_current_user),
    accessibility_service: AccessibilityService = Depends()
):
    """Generate captions for video content"""
    try:
        await accessibility_service.initialize()
        
        # Read video file
        video_data = await video_file.read()
        video_format = video_file.filename.split('.')[-1] if video_file.filename else 'mp4'
        
        result = await accessibility_service.generate_video_captions(
            current_user.id,
            video_data,
            video_format,
            language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-image-alt-text")
async def generate_image_alt_text(
    image_file: UploadFile = File(...),
    context: str = "",
    current_user: User = Depends(get_current_user),
    accessibility_service: AccessibilityService = Depends()
):
    """Generate alt text for images"""
    try:
        await accessibility_service.initialize()
        
        # Read image file
        image_data = await image_file.read()
        image_format = image_file.filename.split('.')[-1] if image_file.filename else 'jpg'
        
        result = await accessibility_service.generate_image_alt_text(
            current_user.id,
            image_data,
            image_format,
            context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-post")
async def enhance_post_accessibility(
    post_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    accessibility_service: AccessibilityService = Depends()
):
    """Enhance a post with accessibility features"""
    try:
        await accessibility_service.initialize()
        result = await accessibility_service.enhance_post_accessibility(
            current_user.id,
            post_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-enhancement")
async def batch_accessibility_enhancement(
    posts: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    accessibility_service: AccessibilityService = Depends()
):
    """Enhance multiple posts with accessibility features"""
    try:
        await accessibility_service.initialize()
        result = await accessibility_service.batch_accessibility_enhancement(
            current_user.id,
            posts
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{post_id}")
async def create_accessibility_report(
    post_id: int,
    current_user: User = Depends(get_current_user),
    accessibility_service: AccessibilityService = Depends()
):
    """Generate accessibility report for a specific post"""
    try:
        await accessibility_service.initialize()
        result = await accessibility_service.create_accessibility_report(
            current_user.id,
            post_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guidelines/{platform}")
async def get_accessibility_guidelines(
    platform: str = "general",
    accessibility_service: AccessibilityService = Depends()
):
    """Get accessibility guidelines for different platforms"""
    try:
        await accessibility_service.initialize()
        result = await accessibility_service.get_accessibility_guidelines(platform)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
