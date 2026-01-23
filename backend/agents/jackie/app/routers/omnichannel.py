from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.omnichannel_service import OmnichannelService
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/omnichannel", tags=["Omnichannel Marketing"])

class CreateOmnichannelCampaignRequest(BaseModel):
    name: str
    description: Optional[str] = None
    channels: List[str]
    content: Dict[str, Any]
    schedule: Dict[str, Any]
    target_audience: List[str]


class ChannelOptimizationRequest(BaseModel):
    campaign_id: int
    channel: str
    optimization_type: str
    parameters: Dict[str, Any]


class CrossChannelAnalyticsRequest(BaseModel):
    campaign_ids: List[int]
    metrics: List[str] = []
    timeframe: str = "30d"


class OmnichannelCampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    channels: List[str]
    status: str
    created_at: datetime

@router.post("/campaigns", response_model=OmnichannelCampaignResponse)
async def create_omnichannel_campaign(
    request: CreateOmnichannelCampaignRequest,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.create_omnichannel_campaign(
            request.name,
            request.description,
            request.channels,
            request.content,
            request.schedule,
            request.target_audience
        )
        return OmnichannelCampaignResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            channels=result["channels"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}", response_model=OmnichannelCampaignResponse)
async def get_omnichannel_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        result = service.get_omnichannel_campaign(campaign_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return OmnichannelCampaignResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            channels=result["channels"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns", response_model=List[OmnichannelCampaignResponse])
async def list_omnichannel_campaigns(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        results = service.list_omnichannel_campaigns(status, channel, limit, offset)
        return [
            OmnichannelCampaignResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                channels=result["channels"],
                status=result["status"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/launch")
async def launch_omnichannel_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        result = service.launch_omnichannel_campaign(campaign_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return {"message": "JackieCampaign launched successfully", "status": result["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/pause")
async def pause_omnichannel_campaign(campaign_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        result = service.pause_omnichannel_campaign(campaign_id)
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return {"message": "JackieCampaign paused successfully", "status": result["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/optimize")
async def optimize_channel(
    request: ChannelOptimizationRequest,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.optimize_channel(
            request.campaign_id,
            request.channel,
            request.optimization_type,
            request.parameters
        )
        if not result:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return {
            "message": "Channel optimization completed",
            "optimization_results": result["optimization_results"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(campaign_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        analytics = service.get_campaign_analytics(campaign_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="JackieCampaign not found")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/cross-channel")
async def get_cross_channel_analytics(
    request: CrossChannelAnalyticsRequest,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        analytics = service.get_cross_channel_analytics(
            request.campaign_ids,
            request.timeframe,
            request.metrics
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_omnichannel_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        overview = service.get_omnichannel_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels")
async def get_supported_channels(db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        channels = service.get_supported_channels()
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels/{channel}/performance")
async def get_channel_performance(
    channel: str,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        performance = service.get_channel_performance(channel, timeframe)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synchronization/sync")
async def sync_cross_channel_data(
    sync_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.sync_cross_channel_data(sync_config)
        return {
            "message": "Cross-channel data synchronization initiated",
            "sync_id": result["sync_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/synchronization/status/{sync_id}")
async def get_sync_status(sync_id: str, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        status = service.get_sync_status(sync_id)
        if not status:
            raise HTTPException(status_code=404, detail="Sync not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalization/rules")
async def create_personalization_rule(
    rule_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.create_personalization_rule(rule_data)
        return {
            "message": "Personalization rule created successfully",
            "rule_id": result["rule_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personalization/rules")
async def list_personalization_rules(
    status: Optional[str] = None,
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        rules = service.list_personalization_rules(status, rule_type)
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coordination/sequence")
async def create_campaign_sequence(
    sequence_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.create_campaign_sequence(sequence_data)
        return {
            "message": "JackieCampaign sequence created successfully",
            "sequence_id": result["sequence_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coordination/sequences")
async def list_campaign_sequences(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        sequences = service.list_campaign_sequences(status, limit, offset)
        return {"sequences": sequences}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coordination/sequences/{sequence_id}/progress")
async def get_sequence_progress(sequence_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        progress = service.get_sequence_progress(sequence_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Sequence not found")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/testing/multivariate")
async def create_multivariate_test(
    test_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = OmnichannelService(db)
    try:
        result = service.create_multivariate_test(test_data)
        return {
            "message": "Multivariate test created successfully",
            "test_id": result["test_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/testing/multivariate/{test_id}/results")
async def get_multivariate_test_results(test_id: int, db: Session = Depends(get_db)):
    service = OmnichannelService(db)
    try:
        results = service.get_multivariate_test_results(test_id)
        if not results:
            raise HTTPException(status_code=404, detail="Test not found")
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
