from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from ..services.cross_channel_lead_tracking_service import CrossChannelLeadTrackingService
from ..database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cross-channel-tracking", tags=["Cross-Channel Lead Tracking"])

# Initialize service
tracking_service = CrossChannelLeadTrackingService()

@router.post("/track")
async def track_lead_across_channels(
    lead_id: int = Query(..., description="Lead ID to track"),
    channel_data: Dict[str, Any] = Body(..., description="Channel activity data")
):
    """Track a lead's activity across multiple channels"""
    try:
        result = await tracking_service.track_lead_across_channels(lead_id, channel_data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Lead activity tracked successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error tracking lead activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/journey/{lead_id}")
async def get_lead_channel_journey(
    lead_id: int,
    period_days: int = Query(30, description="Period in days to analyze")
):
    """Get a lead's journey across all channels"""
    try:
        result = await tracking_service.get_lead_channel_journey(lead_id, period_days)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Lead journey retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting lead journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_cross_channel_analytics(
    team_id: Optional[int] = Query(None, description="Team ID (optional)"),
    period_days: int = Query(30, description="Period in days for analytics")
):
    """Get cross-channel analytics for the team or organization"""
    try:
        result = await tracking_service.get_cross_channel_analytics(team_id, period_days)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Cross-channel analytics retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting cross-channel analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities/{lead_id}")
async def identify_channel_opportunities(lead_id: int):
    """Identify opportunities for engaging leads on different channels"""
    try:
        result = await tracking_service.identify_channel_opportunities(lead_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Channel opportunities identified successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error identifying channel opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_channel_data(
    channel_type: str = Query(..., description="Type of channel to sync"),
    sync_data: Dict[str, Any] = Body(..., description="Data to sync from channel")
):
    """Sync data from external channels"""
    try:
        result = await tracking_service.sync_channel_data(channel_type, sync_data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Channel data synced successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error syncing channel data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-report")
async def get_channel_performance_report(
    period_days: int = Query(30, description="Period in days for report")
):
    """Get comprehensive channel performance report"""
    try:
        result = await tracking_service.get_channel_performance_report(period_days)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Channel performance report generated successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting channel performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for cross-channel lead tracking service"""
    try:
        result = await tracking_service.health_check()
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
