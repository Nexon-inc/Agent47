from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.dynamic_follow_up_scheduler_service import DynamicFollowUpSchedulerService
from ..database import get_eric_database

router = APIRouter()

class ScheduleFollowUpRequest(BaseModel):
    lead_id: int
    engagement_level: Optional[str] = None
    custom_timing: Optional[Dict[str, Any]] = None

class UpdateTimingRequest(BaseModel):
    schedule_id: int
    new_timing: Dict[str, Any]

class CancelFollowUpRequest(BaseModel):
    schedule_id: int
    reason: Optional[str] = None

class BulkScheduleRequest(BaseModel):
    lead_ids: List[int]
    engagement_level: Optional[str] = None

class ScheduleFollowUpResponse(BaseModel):
    success: bool
    follow_up_scheduled: bool
    lead_id: int
    engagement_level: str
    scheduled_time: str
    channels: List[str]
    follow_up_count: int
    max_follow_ups: int
    error: Optional[str] = None

class FollowUpScheduleResponse(BaseModel):
    success: bool
    schedules: List[Dict[str, Any]]
    total_schedules: int
    error: Optional[str] = None

class TimingInsightsResponse(BaseModel):
    success: bool
    timing_analysis: Dict[str, Any]
    response_analysis: Dict[str, Any]
    recommendations: List[str]
    analysis_period_days: int
    error: Optional[str] = None

@router.post("/follow-up/schedule", response_model=ScheduleFollowUpResponse)
async def schedule_follow_up(request: ScheduleFollowUpRequest):
    """Schedule a dynamic follow-up for a lead based on engagement"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.schedule_follow_up(
            request.lead_id,
            request.engagement_level,
            request.custom_timing
        )
        
        if result["success"]:
            return ScheduleFollowUpResponse(
                success=True,
                follow_up_scheduled=result["follow_up_scheduled"],
                lead_id=result["lead_id"],
                engagement_level=result["engagement_level"],
                scheduled_time=result["scheduled_time"],
                channels=result["channels"],
                follow_up_count=result["follow_up_count"],
                max_follow_ups=result["max_follow_ups"]
            )
        else:
            return ScheduleFollowUpResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/schedules", response_model=FollowUpScheduleResponse)
async def get_follow_up_schedules(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get follow-up schedules with optional filters"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.get_follow_up_schedule(lead_id, rep_id, status)
        
        if result["success"]:
            return FollowUpScheduleResponse(
                success=True,
                schedules=result["schedules"],
                total_schedules=result["total_schedules"]
            )
        else:
            return FollowUpScheduleResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/follow-up/update-timing")
async def update_follow_up_timing(request: UpdateTimingRequest):
    """Update the timing of a scheduled follow-up"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.update_follow_up_timing(
            request.schedule_id,
            request.new_timing
        )
        
        if result["success"]:
            return {
                "success": True,
                "timing_updated": result["timing_updated"],
                "schedule_id": result["schedule_id"],
                "updated_timing": result["updated_timing"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/follow-up/cancel")
async def cancel_follow_up(request: CancelFollowUpRequest):
    """Cancel a scheduled follow-up"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.cancel_follow_up(
            request.schedule_id,
            request.reason
        )
        
        if result["success"]:
            return {
                "success": True,
                "follow_up_cancelled": result["follow_up_cancelled"],
                "schedule_id": result["schedule_id"],
                "reason": result["reason"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/timing-insights", response_model=TimingInsightsResponse)
async def get_optimal_timing_insights(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get insights about optimal timing for follow-ups"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.get_optimal_timing_insights(lead_id, rep_id, days)
        
        if result["success"]:
            return TimingInsightsResponse(
                success=True,
                timing_analysis=result["timing_analysis"],
                response_analysis=result["response_analysis"],
                recommendations=result["recommendations"],
                analysis_period_days=result["analysis_period_days"]
            )
        else:
            return TimingInsightsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/follow-up/bulk-schedule")
async def bulk_schedule_follow_ups(request: BulkScheduleRequest):
    """Schedule follow-ups for multiple leads"""
    try:
        service = DynamicFollowUpSchedulerService()
        result = await service.bulk_schedule_follow_ups(
            request.lead_ids,
            request.engagement_level
        )
        
        if result["success"]:
            return {
                "success": True,
                "results": result["results"],
                "total_leads": result["total_leads"],
                "successful_schedules": result["successful_schedules"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/rules")
async def get_follow_up_rules():
    """Get follow-up timing rules and configurations"""
    try:
        service = DynamicFollowUpSchedulerService()
        return {
            "success": True,
            "follow_up_rules": service.follow_up_rules,
            "optimal_timing": service.optimal_timing
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/engagement-levels")
async def get_engagement_levels():
    """Get engagement level definitions and characteristics"""
    try:
        return {
            "success": True,
            "engagement_levels": {
                "high_engagement": {
                    "description": "Leads with frequent and meaningful interactions",
                    "characteristics": [
                        "Multiple email opens and clicks",
                        "Form submissions",
                        "Demo requests",
                        "Phone calls"
                    ],
                    "follow_up_frequency": "1-4 hours",
                    "max_follow_ups": 8
                },
                "medium_engagement": {
                    "description": "Leads with moderate interaction levels",
                    "characteristics": [
                        "Some email engagement",
                        "Website visits",
                        "Social media interactions"
                    ],
                    "follow_up_frequency": "4-24 hours",
                    "max_follow_ups": 6
                },
                "low_engagement": {
                    "description": "Leads with minimal interactions",
                    "characteristics": [
                        "Occasional email opens",
                        "Basic website visits"
                    ],
                    "follow_up_frequency": "24-72 hours",
                    "max_follow_ups": 4
                },
                "no_engagement": {
                    "description": "Leads with no recent interactions",
                    "characteristics": [
                        "No email engagement",
                        "No website visits",
                        "No social interactions"
                    ],
                    "follow_up_frequency": "48-168 hours",
                    "max_follow_ups": 3
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/performance-metrics")
async def get_follow_up_performance_metrics(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get performance metrics for follow-up scheduling"""
    try:
        service = DynamicFollowUpSchedulerService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity, Lead
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get follow-up activities
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "follow_up_schedule",
                    SalesActivity.created_at >= start_date
                )
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Calculate metrics
            total_schedules = len(activities)
            completed_schedules = 0
            cancelled_schedules = 0
            response_count = 0
            
            for activity in activities:
                metadata = activity.metadata or {}
                status = metadata.get("status", "pending")
                
                if status == "completed":
                    completed_schedules += 1
                elif status == "cancelled":
                    cancelled_schedules += 1
                
                # Check for responses
                if await service._check_response_after_follow_up(
                    session, activity.lead_id, activity.created_at
                ):
                    response_count += 1
            
            # Calculate rates
            completion_rate = (completed_schedules / total_schedules * 100) if total_schedules > 0 else 0
            response_rate = (response_count / total_schedules * 100) if total_schedules > 0 else 0
            cancellation_rate = (cancelled_schedules / total_schedules * 100) if total_schedules > 0 else 0
            
            return {
                "success": True,
                "metrics": {
                    "total_schedules": total_schedules,
                    "completed_schedules": completed_schedules,
                    "cancelled_schedules": cancelled_schedules,
                    "response_count": response_count,
                    "completion_rate": round(completion_rate, 2),
                    "response_rate": round(response_rate, 2),
                    "cancellation_rate": round(cancellation_rate, 2),
                    "analysis_period_days": days
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/upcoming")
async def get_upcoming_follow_ups(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    hours: int = Query(24, description="Hours ahead to look")
):
    """Get upcoming follow-ups within the specified time window"""
    try:
        service = DynamicFollowUpSchedulerService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, and_
            from datetime import datetime, timedelta
            
            end_time = datetime.utcnow() + timedelta(hours=hours)
            
            # Get upcoming schedules
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "follow_up_schedule",
                    SalesActivity.metadata["status"].astext == "pending"
                )
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Filter by scheduled time
            upcoming = []
            for activity in activities:
                metadata = activity.metadata or {}
                scheduled_time = metadata.get("scheduled_time")
                
                if scheduled_time:
                    dt = datetime.fromisoformat(scheduled_time)
                    if dt <= end_time:
                        upcoming.append({
                            "id": activity.id,
                            "lead_id": activity.lead_id,
                            "rep_id": activity.rep_id,
                            "scheduled_time": scheduled_time,
                            "engagement_level": metadata.get("engagement_level"),
                            "channels": metadata.get("channels", []),
                            "follow_up_count": metadata.get("follow_up_count", 0)
                        })
            
            # Sort by scheduled time
            upcoming.sort(key=lambda x: x["scheduled_time"])
            
            return {
                "success": True,
                "upcoming_follow_ups": upcoming,
                "total_upcoming": len(upcoming),
                "time_window_hours": hours
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/follow-up/overdue")
async def get_overdue_follow_ups(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID")
):
    """Get overdue follow-ups that should have been sent"""
    try:
        service = DynamicFollowUpSchedulerService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, and_
            from datetime import datetime
            
            now = datetime.utcnow()
            
            # Get overdue schedules
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "follow_up_schedule",
                    SalesActivity.metadata["status"].astext == "pending"
                )
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Filter overdue ones
            overdue = []
            for activity in activities:
                metadata = activity.metadata or {}
                scheduled_time = metadata.get("scheduled_time")
                
                if scheduled_time:
                    dt = datetime.fromisoformat(scheduled_time)
                    if dt < now:
                        overdue.append({
                            "id": activity.id,
                            "lead_id": activity.lead_id,
                            "rep_id": activity.rep_id,
                            "scheduled_time": scheduled_time,
                            "overdue_hours": int((now - dt).total_seconds() / 3600),
                            "engagement_level": metadata.get("engagement_level"),
                            "channels": metadata.get("channels", [])
                        })
            
            # Sort by overdue time (most overdue first)
            overdue.sort(key=lambda x: x["overdue_hours"], reverse=True)
            
            return {
                "success": True,
                "overdue_follow_ups": overdue,
                "total_overdue": len(overdue)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
