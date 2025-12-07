from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..services.content_remix_service import ContentRemixService
from ..deps import get_current_user
from backend.core.database.models import User

router = APIRouter(prefix="/content-remix", tags=["Content Remix"])

@router.post("/remix")
async def remix_content(
    original_content: Dict[str, Any],
    target_platforms: List[str],
    current_user: User = Depends(get_current_user),
    content_remix_service: ContentRemixService = Depends()
):
    """Remix content for multiple platforms"""
    try:
        await content_remix_service.initialize()
        result = await content_remix_service.remix_content(
            current_user.id,
            original_content,
            target_platforms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/variants/{scheduled_post_id}")
async def create_remix_variants(
    scheduled_post_id: int,
    remixed_content: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    content_remix_service: ContentRemixService = Depends()
):
    """Create PostVariant records for remixed content"""
    try:
        await content_remix_service.initialize()
        result = await content_remix_service.create_remix_variants(
            current_user.id,
            scheduled_post_id,
            remixed_content
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-rules/{platform}")
async def get_platform_rules(
    platform: str,
    content_remix_service: ContentRemixService = Depends()
):
    """Get platform-specific content rules"""
    try:
        await content_remix_service.initialize()
        # This would expose the platform rules for frontend use
        return {"platform": platform, "rules": "Available rules for content adaptation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
