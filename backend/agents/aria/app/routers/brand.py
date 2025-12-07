from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.brand_service import BrandService


router = APIRouter(prefix="/aria/brand", tags=["aria:brand"])


class BrandUpdate(BaseModel):
    voice: Optional[Dict[str, Any]] = None
    banned_keywords: Optional[list] = None
    hashtags_bank: Optional[list] = None
    compliance_rules: Optional[Dict[str, Any]] = None
    guidelines_url: Optional[str] = None


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    svc = BrandService()
    bp = await svc.get_or_create_profile(current_user.id)
    return {
        "user_id": bp.user_id,
        "voice": bp.voice,
        "banned_keywords": bp.banned_keywords,
        "hashtags_bank": bp.hashtags_bank,
        "compliance_rules": bp.compliance_rules,
        "guidelines_url": bp.guidelines_url,
    }


@router.patch("/profile")
async def update_profile(payload: BrandUpdate, current_user: User = Depends(get_current_user)):
    svc = BrandService()
    return await svc.update_profile(current_user.id, {k: v for k, v in payload.dict().items() if v is not None})


