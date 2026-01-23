from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json

from ..database import get_db
from ..services.campaign_calendar_service import CampaignCalendarService

router = APIRouter(prefix="/campaign-calendar", tags=["JackieCampaign Calendar Integration"])
from pydantic import BaseModel


class CreateCalendarEventRequest(BaseModel):
    title: str
    event_type: str
    start_date: str
    end_date: str
    campaign_id: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    recurring: Optional[Dict[str, Any]] = None


class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None


class CalendarEventResponse(BaseModel):
    id: str
    title: str
    event_type: str
    start_date: str
    end_date: str
    campaign_id: Optional[str]
    description: Optional[str]
    color: str
    status: str
    created_at: datetime

@router.post("/events", response_model=CalendarEventResponse)
async def create_calendar_event(
    request: CreateCalendarEventRequest,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.create_calendar_event(
            request.title,
            request.event_type,
            request.start_date,
            request.end_date,
            request.campaign_id,
            request.description,
            request.color,
            request.recurring
        )
        return CalendarEventResponse(
            id=result["id"],
            title=result["title"],
            event_type=result["event_type"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            campaign_id=result["campaign_id"],
            description=result["description"],
            color=result["color"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(event_id: str, db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        result = service.get_calendar_event(event_id)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return CalendarEventResponse(
            id=result["id"],
            title=result["title"],
            event_type=result["event_type"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            campaign_id=result["campaign_id"],
            description=result["description"],
            color=result["color"],
            status=result["status"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[CalendarEventResponse])
async def list_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    campaign_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        results = service.list_calendar_events(start_date, end_date, event_type, campaign_id, status, limit, offset)
        return [
            CalendarEventResponse(
                id=result["id"],
                title=result["title"],
                event_type=result["event_type"],
                start_date=result["start_date"],
                end_date=result["end_date"],
                campaign_id=result["campaign_id"],
                description=result["description"],
                color=result["color"],
                status=result["status"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/events/{event_id}")
async def update_calendar_event(
    event_id: str,
    request: UpdateEventRequest,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.update_calendar_event(
            event_id,
            request.title,
            request.start_date,
            request.end_date,
            request.description,
            request.color,
            request.status
        )
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/events/{event_id}")
async def delete_calendar_event(event_id: str, db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        result = service.delete_calendar_event(event_id)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/{event_id}/move")
async def move_calendar_event(
    event_id: str,
    new_start_date: str,
    new_end_date: str,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.move_calendar_event(event_id, new_start_date, new_end_date)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event moved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/{event_id}/duplicate")
async def duplicate_calendar_event(
    event_id: str,
    new_start_date: str,
    new_end_date: str,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.duplicate_calendar_event(event_id, new_start_date, new_end_date)
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")
        return {
            "message": "Event duplicated successfully",
            "new_event_id": result["new_event_id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/bulk-create")
async def bulk_create_events(
    events: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.bulk_create_events(events)
        return {
            "message": f"Created {result['created_count']} events successfully",
            "created_events": result["created_events"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/bulk-update")
async def bulk_update_events(
    event_updates: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.bulk_update_events(event_updates)
        return {
            "message": f"Updated {result['updated_count']} events successfully",
            "updated_events": result["updated_events"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/bulk-delete")
async def bulk_delete_events(
    event_ids: List[str],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.bulk_delete_events(event_ids)
        return {
            "message": f"Deleted {result['deleted_count']} events successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/view")
async def get_calendar_view(
    view_type: str = "month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        calendar_view = service.get_calendar_view(view_type, start_date, end_date, filters)
        return calendar_view
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/timeline")
async def get_calendar_timeline(
    start_date: str,
    end_date: str,
    group_by: str = "day",
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        timeline = service.get_calendar_timeline(start_date, end_date, group_by, filters)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/sync")
async def sync_calendar_with_campaigns(
    sync_type: str = "full",
    campaign_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.sync_calendar_with_campaigns(sync_type, campaign_ids)
        return {
            "message": "Calendar synced successfully",
            "synced_events": result["synced_events"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/conflicts")
async def check_calendar_conflicts(
    start_date: str,
    end_date: str,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        conflicts = service.check_calendar_conflicts(start_date, end_date, event_type)
        return {"conflicts": conflicts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/optimize")
async def optimize_calendar_schedule(
    optimization_goals: List[str],
    constraints: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.optimize_calendar_schedule(optimization_goals, constraints)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/availability")
async def check_calendar_availability(
    start_date: str,
    end_date: str,
    event_type: str,
    duration_minutes: int,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        availability = service.check_calendar_availability(start_date, end_date, event_type, duration_minutes)
        return {"availability": availability}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/suggestions")
async def get_calendar_suggestions(
    event_type: str,
    duration_minutes: int,
    preferences: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        suggestions = service.get_calendar_suggestions(event_type, duration_minutes, preferences)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/analytics")
async def get_calendar_analytics(
    start_date: str,
    end_date: str,
    metrics: List[str],
    group_by: str = "day",
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        analytics = service.get_calendar_analytics(start_date, end_date, metrics, group_by)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/export")
async def export_calendar(
    export_format: str = "ics",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_types: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.export_calendar(export_format, start_date, end_date, event_types)
        return {
            "message": "Calendar exported successfully",
            "download_url": result["download_url"],
            "file_size": result["file_size"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/import")
async def import_calendar(
    file_url: str,
    import_format: str = "ics",
    conflict_resolution: str = "skip",
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.import_calendar(file_url, import_format, conflict_resolution)
        return {
            "message": "Calendar imported successfully",
            "imported_events": result["imported_events"],
            "skipped_events": result["skipped_events"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/settings")
async def get_calendar_settings(db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        settings = service.get_calendar_settings()
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/calendar/settings")
async def update_calendar_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.update_calendar_settings(settings)
        return {"message": "Calendar settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/views")
async def get_available_calendar_views(db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        views = service.get_available_calendar_views()
        return {"views": views}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/views/custom")
async def create_custom_calendar_view(
    view_name: str,
    view_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.create_custom_calendar_view(view_name, view_config)
        return {
            "message": "Custom calendar view created successfully",
            "view_id": result["view_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/views/custom")
async def get_custom_calendar_views(db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        views = service.get_custom_calendar_views()
        return {"views": views}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/calendar/views/{view_id}")
async def delete_custom_calendar_view(view_id: str, db: Session = Depends(get_db)):
    service = CampaignCalendarService(db)
    try:
        result = service.delete_custom_calendar_view(view_id)
        if not result:
            raise HTTPException(status_code=404, detail="View not found")
        return {"message": "Custom calendar view deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/notifications")
async def get_calendar_notifications(
    user_id: str,
    notification_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        notifications = service.get_calendar_notifications(user_id, notification_type, limit, offset)
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/notifications/setup")
async def setup_calendar_notifications(
    user_id: str,
    notification_settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CampaignCalendarService(db)
    try:
        result = service.setup_calendar_notifications(user_id, notification_settings)
        return {"message": "Calendar notifications setup successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
