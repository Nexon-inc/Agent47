import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import CampaignEvent, CalendarView, JackieTimelineEvent, ScheduleConflict

class CampaignCalendarService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_calendar_event(self, event_data: Dict[str, Any], campaign_id: str) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        
        event = CampaignEvent(
            id=event_id, campaign_id=campaign_id, event_title=event_data.get("title", ""),
            event_description=event_data.get("description", ""), event_type=event_data.get("type", "general"),
            start_date=event_data.get("start_date"), end_date=event_data.get("end_date"),
            event_data=json.dumps(event_data.get("event_data", {})), created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
        
        return {"event_id": event_id, "campaign_id": campaign_id, "title": event_data.get("title", "")}
    
    def bulk_create_events(self, events_data: List[Dict[str, Any]], campaign_id: str) -> Dict[str, Any]:
        created_events = []
        
        for event_data in events_data:
            try:
                result = self.create_calendar_event(event_data, campaign_id)
                created_events.append(result)
            except Exception as e:
                created_events.append({"error": str(e), "event_data": event_data})
        
        return {"campaign_id": campaign_id, "created_events": created_events}
    
    def get_calendar_view(self, view_type: str, date_range: Dict[str, str],
                         campaign_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        view_id = str(uuid.uuid4())
        
        query = self.db.query(CampaignEvent)
        if campaign_ids:
            query = query.filter(CampaignEvent.campaign_id.in_(campaign_ids))
        
        events = query.filter(
            CampaignEvent.start_date >= date_range.get("start"),
            CampaignEvent.start_date <= date_range.get("end")
        ).all()
        
        calendar_view = CalendarView(
            id=view_id, view_type=view_type, date_range=json.dumps(date_range),
            campaign_ids=json.dumps(campaign_ids or []), events_count=len(events),
            created_at=datetime.utcnow()
        )
        self.db.add(calendar_view)
        self.db.commit()
        
        return {
            "view_id": view_id, "view_type": view_type, "events_count": len(events),
            "events": [{"id": e.id, "title": e.event_title, "start_date": e.start_date} for e in events]
        }
    
    def get_campaign_timeline(self, campaign_id: str, timeline_type: str = "detailed") -> Dict[str, Any]:
        events = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id
        ).order_by(CampaignEvent.start_date).all()
        
        timeline = []
        for event in events:
            timeline.append({
                "event_id": event.id, "title": event.event_title,
                "type": event.event_type, "start_date": event.start_date,
                "end_date": event.end_date
            })
        
        return {"campaign_id": campaign_id, "timeline_type": timeline_type, "timeline": timeline}
    
    def sync_with_campaigns(self, campaign_ids: List[str]) -> Dict[str, Any]:
        sync_result = self.nlp_processor.sync_calendar_with_campaigns(f"JackieCampaign IDs: {campaign_ids}")
        
        return {
            "campaign_ids": campaign_ids, "sync_status": "completed",
            "synced_events": sync_result.get("synced_events", 0)
        }
    
    def check_conflicts(self, event_data: Dict[str, Any], campaign_id: str) -> Dict[str, Any]:
        start_date = event_data.get("start_date")
        end_date = event_data.get("end_date")
        
        conflicts = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.start_date < end_date,
            CampaignEvent.end_date > start_date
        ).all()
        
        conflict_record = ScheduleConflict(
            id=str(uuid.uuid4()), campaign_id=campaign_id,
            conflict_data=json.dumps(event_data), conflicts_found=len(conflicts),
            created_at=datetime.utcnow()
        )
        self.db.add(conflict_record)
        self.db.commit()
        
        return {
            "campaign_id": campaign_id, "conflicts_found": len(conflicts),
            "conflicting_events": [{"id": c.id, "title": c.event_title} for c in conflicts]
        }
    
    def check_availability(self, date_range: Dict[str, str], campaign_id: str) -> Dict[str, Any]:
        start_date = date_range.get("start")
        end_date = date_range.get("end")
        
        existing_events = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.start_date < end_date,
            CampaignEvent.end_date > start_date
        ).count()
        
        return {
            "campaign_id": campaign_id, "date_range": date_range,
            "available": existing_events == 0, "conflicting_events": existing_events
        }
    
    def optimize_schedule(self, campaign_id: str, optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        events = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id
        ).all()
        
        optimization_result = self.nlp_processor.optimize_campaign_schedule(
            f"JackieCampaign ID: {campaign_id}, Goals: {optimization_goals}"
        )
        
        return {
            "campaign_id": campaign_id, "optimization_goals": optimization_goals,
            "optimized_schedule": optimization_result.get("optimized_schedule", []),
            "recommendations": optimization_result.get("recommendations", [])
        }
    
    def get_schedule_suggestions(self, campaign_id: str, suggestion_type: str) -> Dict[str, Any]:
        suggestion_result = self.nlp_processor.get_schedule_suggestions(
            f"JackieCampaign ID: {campaign_id}, Type: {suggestion_type}"
        )
        
        return {
            "campaign_id": campaign_id, "suggestion_type": suggestion_type,
            "suggestions": suggestion_result.get("suggestions", [])
        }
    
    def get_calendar_analytics(self, campaign_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        total_events = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.created_at >= cutoff_date
        ).count()
        
        event_types = self.db.query(CampaignEvent.event_type).filter(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.created_at >= cutoff_date
        ).group_by(CampaignEvent.event_type).all()
        
        return {
            "campaign_id": campaign_id, "timeframe": timeframe,
            "total_events": total_events, "event_types": [e[0] for e in event_types]
        }
    
    def import_calendar(self, calendar_data: Dict[str, Any], campaign_id: str) -> Dict[str, Any]:
        import_result = self.nlp_processor.import_calendar_data(
            f"Calendar Data: {calendar_data}, JackieCampaign ID: {campaign_id}"
        )
        
        return {
            "campaign_id": campaign_id, "import_status": "completed",
            "imported_events": import_result.get("imported_events", 0)
        }
    
    def export_calendar(self, campaign_id: str, export_format: str = "json") -> Dict[str, Any]:
        events = self.db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign_id
        ).all()
        
        export_data = {
            "campaign_id": campaign_id, "export_format": export_format,
            "events": [{"id": e.id, "title": e.event_title, "start_date": e.start_date} for e in events],
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return export_data
