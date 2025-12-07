from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.geo_targeted_service import GeoTargetedService

router = APIRouter(prefix="/geo-targeted", tags=["Geo-Targeted Ad Planner"])

@router.post("/geo-targeted-ad")
def create_geo_targeted_ad(ad_brief: Dict[str, Any], target_locations: List[str], 
                          db: Session = Depends(get_db)):
    service = GeoTargetedService(db)
    return service.create_geo_targeted_ad(ad_brief, target_locations)

@router.post("/local-market")
async def analyze_local_market(location: str, market_data: Dict[str, Any], 
                        db: Session = Depends(get_db)):
    service = GeoTargetedService(db)
    return await service.analyze_local_market(location, market_data)

@router.get("/analytics")
def get_geo_targeted_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = GeoTargetedService(db)
    return service.get_geo_targeted_analytics(timeframe)
