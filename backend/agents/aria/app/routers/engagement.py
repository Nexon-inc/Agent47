from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.engagement_service import EngagementService


router = APIRouter(prefix="/aria/engagement", tags=["aria:engagement"])


class AutoReplyRequest(BaseModel):
    platform: str
    text: str
    sentiment_hint: str = "auto"


@router.post("/auto-reply")
async def auto_reply(payload: AutoReplyRequest, current_user: User = Depends(get_current_user)):
    svc = EngagementService()
    return await svc.auto_reply(current_user.id, payload.platform, payload.text, payload.sentiment_hint)


