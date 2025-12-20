from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from core.authentication.auth_manager import get_current_user
from core.database.models import User
from ..services.trend_service import TrendService


router = APIRouter(prefix="/aria/trends", tags=["aria:trends"])


class TrendIngest(BaseModel):
    topic: str
    region: str = "us"
    keywords: List[str] = []


@router.post("/brandwatch")
async def ingest_brandwatch(payload: TrendIngest, current_user: User = Depends(get_current_user)):
    svc = TrendService()
    return await svc.ingest_brandwatch_alert(payload.topic, payload.keywords, payload.region)

@router.post("/semrush")
async def ingest_semrush(payload: TrendIngest, current_user: User = Depends(get_current_user)):
    svc = TrendService()
    return await svc.ingest_seo_semrush(payload.topic, payload.region)


