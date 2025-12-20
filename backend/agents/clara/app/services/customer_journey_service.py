from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import CustomerJourney, JourneyEvent, JourneyStage, CustomerInteraction, SupportTicket
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
# NLPUtils removed - not used


class CustomerJourneyService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_customer_journey(
        self, 
        db: Session, 
        customer_id: int,
        journey_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new customer journey"""
        try:
            journey = CustomerJourney(
                customer_id=customer_id,
                journey_type=journey_type,
                description=description,
                current_stage="started",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(journey)
            db.commit()
            db.refresh(journey)
            
            return {
                "id": journey.id,
                "customer_id": journey.customer_id,
                "journey_type": journey.journey_type,
                "description": journey.description,
                "current_stage": journey.current_stage,
                "status": journey.status,
                "created_at": journey.created_at,
                "updated_at": journey.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create customer journey: {str(e)}")
    
    async def get_customer_journey(
        self, 
        db: Session, 
        journey_id: int
    ) -> Dict[str, Any]:
        """Get customer journey by ID"""
        try:
            journey = db.query(CustomerJourney).filter(CustomerJourney.id == journey_id).first()
            if not journey:
                raise HTTPException(status_code=404, detail="Customer journey not found")
            
            return {
                "id": journey.id,
                "customer_id": journey.customer_id,
                "journey_type": journey.journey_type,
                "description": journey.description,
                "current_stage": journey.current_stage,
                "status": journey.status,
                "created_at": journey.created_at,
                "updated_at": journey.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get customer journey: {str(e)}")
    
    async def list_customer_journeys(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[int] = None,
        journey_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List customer journeys"""
        try:
            query = db.query(CustomerJourney)
            
            if customer_id:
                query = query.filter(CustomerJourney.customer_id == customer_id)
            if journey_type:
                query = query.filter(CustomerJourney.journey_type == journey_type)
            if status:
                query = query.filter(CustomerJourney.status == status)
            
            journeys = query.offset(skip).limit(limit).all()
            
            return [
                {
                    "id": journey.id,
                    "customer_id": journey.customer_id,
                    "journey_type": journey.journey_type,
                    "description": journey.description,
                    "current_stage": journey.current_stage,
                    "status": journey.status,
                    "created_at": journey.created_at,
                    "updated_at": journey.updated_at
                } for journey in journeys
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list customer journeys: {str(e)}")
    
    async def update_customer_journey(
        self, 
        db: Session, 
        journey_id: int,
        current_stage: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update customer journey"""
        try:
            journey = db.query(CustomerJourney).filter(CustomerJourney.id == journey_id).first()
            if not journey:
                raise HTTPException(status_code=404, detail="Customer journey not found")
            
            if current_stage is not None:
                journey.current_stage = current_stage
            if status is not None:
                journey.status = status
            if description is not None:
                journey.description = description
            
            journey.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(journey)
            
            return {
                "id": journey.id,
                "customer_id": journey.customer_id,
                "journey_type": journey.journey_type,
                "description": journey.description,
                "current_stage": journey.current_stage,
                "status": journey.status,
                "created_at": journey.created_at,
                "updated_at": journey.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update customer journey: {str(e)}")
    
    async def add_journey_event(
        self, 
        db: Session, 
        journey_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add an event to a customer journey"""
        try:
            event = JourneyEvent(
                journey_id=journey_id,
                event_type=event_type,
                event_data=event_data,
                stage=stage,
                created_at=datetime.utcnow()
            )
            
            db.add(event)
            db.commit()
            db.refresh(event)
            
            return {
                "id": event.id,
                "journey_id": event.journey_id,
                "event_type": event.event_type,
                "event_data": event.event_data,
                "stage": event.stage,
                "created_at": event.created_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to add journey event: {str(e)}")
    
    async def get_journey_events(
        self, 
        db: Session, 
        journey_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events for a customer journey"""
        try:
            events = db.query(JourneyEvent).filter(
                JourneyEvent.journey_id == journey_id
            ).order_by(desc(JourneyEvent.created_at)).offset(skip).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "journey_id": event.journey_id,
                    "event_type": event.event_type,
                    "event_data": event.event_data,
                    "stage": event.stage,
                    "created_at": event.created_at
                } for event in events
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get journey events: {str(e)}")
    
    async def create_journey_stage(
        self, 
        db: Session, 
        stage_name: str,
        stage_type: str,
        description: Optional[str] = None,
        order_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new journey stage"""
        try:
            stage = JourneyStage(
                stage_name=stage_name,
                stage_type=stage_type,
                description=description,
                order_index=order_index,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(stage)
            db.commit()
            db.refresh(stage)
            
            return {
                "id": stage.id,
                "stage_name": stage.stage_name,
                "stage_type": stage.stage_type,
                "description": stage.description,
                "order_index": stage.order_index,
                "is_active": stage.is_active,
                "created_at": stage.created_at,
                "updated_at": stage.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create journey stage: {str(e)}")
    
    async def get_journey_stages(
        self, 
        db: Session, 
        stage_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get journey stages"""
        try:
            query = db.query(JourneyStage)
            
            if stage_type:
                query = query.filter(JourneyStage.stage_type == stage_type)
            if is_active is not None:
                query = query.filter(JourneyStage.is_active == is_active)
            
            stages = query.order_by(JourneyStage.order_index).all()
            
            return [
                {
                    "id": stage.id,
                    "stage_name": stage.stage_name,
                    "stage_type": stage.stage_type,
                    "description": stage.description,
                    "order_index": stage.order_index,
                    "is_active": stage.is_active,
                    "created_at": stage.created_at,
                    "updated_at": stage.updated_at
                } for stage in stages
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get journey stages: {str(e)}")
    
    async def track_customer_interaction(
        self, 
        db: Session, 
        customer_id: int,
        interaction_type: str,
        channel: str,
        content: str,
        sentiment_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Track a customer interaction and update journey"""
        try:
            # Find or create customer journey
            journey = db.query(CustomerJourney).filter(
                and_(
                    CustomerJourney.customer_id == customer_id,
                    CustomerJourney.status == "active"
                )
            ).first()
            
            if not journey:
                journey = CustomerJourney(
                    customer_id=customer_id,
                    journey_type="support_interaction",
                    description="Customer support interaction journey",
                    current_stage="interaction_started",
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(journey)
                db.commit()
                db.refresh(journey)
            
            # Add journey event
            event_data = {
                "interaction_type": interaction_type,
                "channel": channel,
                "content": content,
                "sentiment_score": sentiment_score
            }
            
            event = JourneyEvent(
                journey_id=journey.id,
                event_type="customer_interaction",
                event_data=event_data,
                stage="interaction",
                created_at=datetime.utcnow()
            )
            
            db.add(event)
            db.commit()
            
            return {
                "journey_id": journey.id,
                "event_id": event.id,
                "message": "Customer interaction tracked successfully"
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to track customer interaction: {str(e)}")
    
    async def get_journey_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        journey_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customer journey analytics"""
        try:
            # Build queries
            journeys_query = db.query(CustomerJourney).filter(
                and_(
                    CustomerJourney.created_at >= start_date,
                    CustomerJourney.created_at <= end_date
                )
            )
            
            events_query = db.query(JourneyEvent).filter(
                and_(
                    JourneyEvent.created_at >= start_date,
                    JourneyEvent.created_at <= end_date
                )
            )
            
            if journey_type:
                journeys_query = journeys_query.filter(CustomerJourney.journey_type == journey_type)
            
            journeys = journeys_query.all()
            events = events_query.all()
            
            # Calculate metrics
            total_journeys = len(journeys)
            completed_journeys = len([j for j in journeys if j.status == "completed"])
            active_journeys = len([j for j in journeys if j.status == "active"])
            total_events = len(events)
            
            # Stage breakdown
            stage_breakdown = {}
            for journey in journeys:
                stage = journey.current_stage
                if stage not in stage_breakdown:
                    stage_breakdown[stage] = 0
                stage_breakdown[stage] += 1
            
            # Event type breakdown
            event_type_breakdown = {}
            for event in events:
                event_type = event.event_type
                if event_type not in event_type_breakdown:
                    event_type_breakdown[event_type] = 0
                event_type_breakdown[event_type] += 1
            
            return {
                "period_start": start_date,
                "period_end": end_date,
                "total_journeys": total_journeys,
                "completed_journeys": completed_journeys,
                "active_journeys": active_journeys,
                "completion_rate": completed_journeys / total_journeys if total_journeys > 0 else 0,
                "total_events": total_events,
                "avg_events_per_journey": total_events / total_journeys if total_journeys > 0 else 0,
                "stage_breakdown": stage_breakdown,
                "event_type_breakdown": event_type_breakdown
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get journey analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of customer journey system"""
        try:
            db = next(get_db())
            journey_count = db.query(CustomerJourney).count()
            event_count = db.query(JourneyEvent).count()
            stage_count = db.query(JourneyStage).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "journeys_count": journey_count,
                    "events_count": event_count,
                    "stages_count": stage_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
