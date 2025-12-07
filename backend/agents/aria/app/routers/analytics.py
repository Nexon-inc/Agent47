from fastapi import APIRouter, Depends
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.analytics_service import AnalyticsService


router = APIRouter(prefix="/aria/analytics", tags=["aria:analytics"])


@router.get("/posts/{post_ref}/summary")
async def get_post_summary(post_ref: str, current_user: User = Depends(get_current_user)):
    svc = AnalyticsService()
    return await svc.get_post_summary(current_user.id, post_ref)


