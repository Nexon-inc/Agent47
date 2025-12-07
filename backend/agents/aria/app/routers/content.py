from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.content_service import ContentService


router = APIRouter(prefix="/aria/content", tags=["aria:content"])


class CaptionRequest(BaseModel):
    topic: str
    tone: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None


@router.post("/captions")
async def generate_caption(payload: CaptionRequest, current_user: User = Depends(get_current_user)):
    service = ContentService()
    await service.initialize()
    return await service.generate_caption(current_user.id, payload.dict())


class HashtagRequest(BaseModel):
    topic: str
    n: int = 10


@router.post("/hashtags")
async def suggest_hashtags(payload: HashtagRequest, current_user: User = Depends(get_current_user)):
    service = ContentService()
    await service.initialize()
    tags = await service.suggest_hashtags(current_user.id, payload.topic, payload.n)
    return {"hashtags": tags}


