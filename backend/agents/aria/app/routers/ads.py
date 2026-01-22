from fastapi import APIRouter, Depends
from pydantic import BaseModel
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..services.ads_service import AdsService
from ..deps import require_posting_allowed


router = APIRouter(prefix="/aria/ads", tags=["aria:ads"])


class AriaCampaign(BaseModel):
    platform: str
    name: str
    daily_budget_cents: int
    objective: str
    access_token: str


@router.post("/campaigns")
async def create_campaign(payload: AriaCampaign, current_user: User = Depends(require_posting_allowed)):
    svc = AdsService()
    if payload.platform.lower() == "instagram":
        return await svc.create_ig_campaign(payload.access_token, payload.name, payload.daily_budget_cents, payload.objective)
    if payload.platform.lower() == "linkedin":
        return await svc.create_linkedin_campaign(payload.access_token, payload.name, payload.daily_budget_cents, payload.objective)
    return {"success": False, "error": "unsupported_platform"}


