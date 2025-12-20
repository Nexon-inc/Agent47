from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..services.scheduling_service import SchedulingService
from ..deps import require_posting_allowed


router = APIRouter(prefix="/aria/schedules", tags=["aria:schedules"])


class ScheduleCreateRequest(BaseModel):
    idempotency_key: str = Field(min_length=8)
    platform_targets: List[str]
    scheduled_at: str
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    media_refs: Optional[List[Dict[str, Any]]] = None
    campaign_id: Optional[int] = None
    account_group_id: Optional[int] = None
    timezone: Optional[str] = "UTC"


class ScheduleUpdateRequest(BaseModel):
    scheduled_at: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    media_refs: Optional[List[Dict[str, Any]]] = None


@router.post("", status_code=201)
async def create_schedule(payload: ScheduleCreateRequest, current_user: User = Depends(require_posting_allowed)):
    service = SchedulingService()
    await service.initialize()
    result = await service.create_scheduled_post(current_user.id, payload.dict())
    return result


@router.get("")
async def list_schedules(
    from_: Optional[str] = None,
    to: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    service = SchedulingService()
    await service.initialize()
    params = {"from": from_, "to": to, "status": status}
    return await service.list_user_schedules(current_user.id, params)


@router.patch("/{scheduled_post_id}")
async def update_schedule(scheduled_post_id: int, updates: ScheduleUpdateRequest, current_user: User = Depends(get_current_user)):
    service = SchedulingService()
    await service.initialize()
    updated = await service.update_schedule(current_user.id, scheduled_post_id, {k: v for k, v in updates.dict().items() if v is not None})
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated


