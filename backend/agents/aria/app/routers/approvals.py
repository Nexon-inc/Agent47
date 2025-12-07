from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.approval_service import ApprovalService
from ..deps import require_team_allowed


router = APIRouter(prefix="/aria/approvals", tags=["aria:approvals"])


class ApprovalRequest(BaseModel):
    scheduled_post_id: int
    reviewers: List[str]


@router.post("")
async def request_approval(payload: ApprovalRequest, current_user: User = Depends(require_team_allowed)):
    svc = ApprovalService()
    return await svc.request_approval(current_user.id, payload.scheduled_post_id, payload.reviewers)


class ApprovalDecision(BaseModel):
    approval_id: int
    decision: str
    comment: Optional[str] = None


@router.post("/decide")
async def make_decision(payload: ApprovalDecision, current_user: User = Depends(get_current_user)):
    svc = ApprovalService()
    return await svc.decide(payload.approval_id, payload.decision, payload.comment or "")


