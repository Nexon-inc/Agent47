from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from ..services.ab_testing_service import ABTestingService


router = APIRouter(prefix="/aria/ab", tags=["aria:ab"])


class VariantMetrics(BaseModel):
    variant_id: int
    metrics: Dict[str, Any]


@router.post("/record")
async def record_metrics(payload: VariantMetrics, current_user: User = Depends(get_current_user)):
    svc = ABTestingService()
    return {"success": await svc.record_variant_metrics(payload.variant_id, payload.metrics)}


class WinnerPick(BaseModel):
    variants: List[Dict[str, Any]]


@router.post("/winner")
async def pick_winner(payload: WinnerPick, current_user: User = Depends(get_current_user)):
    svc = ABTestingService()
    return svc.pick_winner(payload.variants)


