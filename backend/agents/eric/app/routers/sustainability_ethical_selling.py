from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from ..services.sustainability_ethical_selling_service import SustainabilityEthicalSellingService
from ..database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ethical-selling", tags=["Sustainability & Ethical Selling"])

# Initialize service
sustainability_service = SustainabilityEthicalSellingService()

@router.post("/guidelines")
async def generate_ethical_guidelines(
    industry: str = Query(..., description="Industry type (e.g., technology, healthcare, finance)"),
    company_size: str = Query(..., description="Company size (e.g., startup, small, medium, large)"),
    region: str = Query(..., description="Geographic region (e.g., US, EU, Asia)")
):
    """Generate ethical selling guidelines for the organization"""
    try:
        result = await sustainability_service.generate_ethical_guidelines(industry, company_size, region)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Ethical guidelines generated successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error generating ethical guidelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sustainability-score/{rep_id}")
async def calculate_sustainability_score(
    rep_id: int,
    period_days: int = Query(30, description="Period in days to calculate score for")
):
    """Calculate sustainability score for a sales representative"""
    try:
        result = await sustainability_service.calculate_sustainability_score(rep_id, period_days)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Sustainability score calculated successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error calculating sustainability score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance/track")
async def track_compliance(
    rep_id: int = Query(..., description="Sales representative ID"),
    activity_type: str = Query(..., description="Type of sales activity"),
    activity_data: Dict[str, Any] = Body(..., description="Activity data for compliance check")
):
    """Track compliance with ethical selling practices"""
    try:
        result = await sustainability_service.track_compliance(rep_id, activity_type, activity_data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Compliance tracked successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error tracking compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{rep_id}")
async def get_ethical_recommendations(
    rep_id: int,
    context: str = Query("general", description="Context for recommendations (e.g., general, email, call, meeting)")
):
    """Get personalized ethical selling recommendations"""
    try:
        result = await sustainability_service.get_ethical_recommendations(rep_id, context)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Ethical recommendations retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting ethical recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_sustainability_analytics(
    team_id: Optional[int] = Query(None, description="Team ID (optional, if not provided returns all teams)"),
    period_days: int = Query(30, description="Period in days for analytics")
):
    """Get comprehensive sustainability analytics"""
    try:
        result = await sustainability_service.get_sustainability_analytics(team_id, period_days)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
            
        return {
            "status": "success",
            "message": "Sustainability analytics retrieved successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting sustainability analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for sustainability and ethical selling service"""
    try:
        result = await sustainability_service.health_check()
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
