from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..services.media_service import MediaService


router = APIRouter(prefix="/aria/media", tags=["aria:media"])


class ImageRequest(BaseModel):
    prompt: Optional[str] = None
    context: Optional[str] = None
    width: int = 1024
    height: int = 1024
    auto_generate_prompt: bool = False


@router.post("/images")
async def create_image(
    payload: ImageRequest, 
    current_user: User = Depends(get_current_user)
):
    """Generate an image using Google Gemini
    
    Either provide:
    - prompt: Direct image generation prompt
    - context: Description/context (will be used as prompt or auto-generated if auto_generate_prompt=True)
    """
    svc = MediaService()
    return await svc.generate_image(
        prompt=payload.prompt,
        context=payload.context,
        user_id=current_user.id,
        user_tier=current_user.tier,
        width=payload.width,
        height=payload.height,
        auto_generate_prompt=payload.auto_generate_prompt
    )


