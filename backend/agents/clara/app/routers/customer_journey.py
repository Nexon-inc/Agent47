from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_db
from ..services.customer_journey_service import CustomerJourneyService
from ..models import CustomerJourney, JourneyEvent, JourneyStage, CustomerProfile
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateJourneyRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    brand_id: Optional[int] = Field(None, description="Brand ID")
    initial_channel: str = Field(..., description="Initial contact channel")
    initial_intent: str = Field(..., description="Initial customer intent")
    source: Optional[str] = Field(None, description="Journey source (website, app, social, etc.)")
    campaign: Optional[str] = Field(None, description="Marketing campaign if applicable")
    utm_parameters: Optional[Dict[str, str]] = Field(None, description="UTM parameters")

class UpdateJourneyRequest(BaseModel):
    current_stage: Optional[str] = Field(None, description="Current journey stage")
    status: Optional[str] = Field(None, description="Journey status")
    priority: Optional[str] = Field(None, description="Journey priority")
    assigned_agent: Optional[str] = Field(None, description="Assigned agent ID")
    tags: Optional[List[str]] = Field(None, description="Journey tags")

class CreateEventRequest(BaseModel):
    journey_id: int = Field(..., description="Journey ID")
    event_type: str = Field(..., description="Event type (interaction, milestone, conversion, etc.)")
    channel: str = Field(..., description="Channel where event occurred")
    description: str = Field(..., description="Event description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Event metadata")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")

class CreateStageRequest(BaseModel):
    journey_id: int = Field(..., description="Journey ID")
    stage_name: str = Field(..., description="Stage name")
    stage_type: str = Field(..., description="Stage type (awareness, consideration, decision, etc.)")
    description: Optional[str] = Field(None, description="Stage description")
    expected_duration: Optional[int] = Field(None, description="Expected duration in hours")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Stage completion criteria")

class JourneyResponse(BaseModel):
    id: int
    customer_id: str
    brand_id: Optional[int]
    initial_channel: str
    initial_intent: str
    current_stage: str
    status: str
    priority: str
    source: Optional[str]
    campaign: Optional[str]
    utm_parameters: Optional[Dict[str, str]]
    assigned_agent: Optional[str]
    tags: List[str]
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    journey_id: int
    event_type: str
    channel: str
    description: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class StageResponse(BaseModel):
    id: int
    journey_id: int
    stage_name: str
    stage_type: str
    description: Optional[str]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    expected_duration: Optional[int]
    actual_duration: Optional[int]
    criteria: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class JourneyAnalyticsResponse(BaseModel):
    journey_id: int
    customer_id: str
    total_events: int
    total_stages: int
    current_stage: str
    time_in_current_stage: float
    total_journey_time: float
    conversion_rate: float
    engagement_score: float
    channel_preferences: List[Dict[str, Any]]
    touchpoints: List[Dict[str, Any]]

class JourneyMapResponse(BaseModel):
    customer_id: str
    journey_id: int
    stages: List[StageResponse]
    events: List[EventResponse]
    touchpoints: List[Dict[str, Any]]
    conversion_points: List[Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]

# Dependency
async def get_customer_journey_service(db: AsyncSession = Depends(get_db)) -> CustomerJourneyService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return CustomerJourneyService(db, integration_manager, event_bus)

# Journey Management Endpoints
@router.post("/journeys", response_model=JourneyResponse, status_code=status.HTTP_201_CREATED)
async def create_journey(
    request: CreateJourneyRequest,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Create a new customer journey"""
    try:
        journey = await service.create_journey(
            customer_id=request.customer_id,
            brand_id=request.brand_id,
            initial_channel=request.initial_channel,
            initial_intent=request.initial_intent,
            source=request.source,
            campaign=request.campaign,
            utm_parameters=request.utm_parameters
        )
        return JourneyResponse.from_orm(journey)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/journeys", response_model=List[JourneyResponse])
async def get_journeys(
    customer_id: Optional[str] = None,
    brand_id: Optional[int] = None,
    status: Optional[str] = None,
    active_only: bool = True,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get customer journeys with optional filtering"""
    try:
        journeys = await service.get_journeys(
            customer_id=customer_id,
            brand_id=brand_id,
            status=status,
            active_only=active_only
        )
        return [JourneyResponse.from_orm(journey) for journey in journeys]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/journeys/{journey_id}", response_model=JourneyResponse)
async def get_journey(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get a specific journey by ID"""
    try:
        journey = await service.get_journey(journey_id)
        if not journey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
        return JourneyResponse.from_orm(journey)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/journeys/{journey_id}", response_model=JourneyResponse)
async def update_journey(
    journey_id: int,
    request: UpdateJourneyRequest,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Update a customer journey"""
    try:
        journey = await service.update_journey(
            journey_id=journey_id,
            current_stage=request.current_stage,
            status=request.status,
            priority=request.priority,
            assigned_agent=request.assigned_agent,
            tags=request.tags
        )
        if not journey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
        return JourneyResponse.from_orm(journey)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/journeys/{journey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journey(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Delete a customer journey"""
    try:
        success = await service.delete_journey(journey_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Event Management Endpoints
@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: CreateEventRequest,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Create a new journey event"""
    try:
        event = await service.create_event(
            journey_id=request.journey_id,
            event_type=request.event_type,
            channel=request.channel,
            description=request.description,
            metadata=request.metadata,
            timestamp=request.timestamp
        )
        return EventResponse.from_orm(event)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/journeys/{journey_id}/events", response_model=List[EventResponse])
async def get_journey_events(
    journey_id: int,
    event_type: Optional[str] = None,
    channel: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get events for a specific journey"""
    try:
        events = await service.get_journey_events(
            journey_id=journey_id,
            event_type=event_type,
            channel=channel,
            start_date=start_date,
            end_date=end_date
        )
        return [EventResponse.from_orm(event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get a specific event by ID"""
    try:
        event = await service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return EventResponse.from_orm(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    request: CreateEventRequest,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Update a journey event"""
    try:
        event = await service.update_event(
            event_id=event_id,
            event_type=request.event_type,
            channel=request.channel,
            description=request.description,
            metadata=request.metadata,
            timestamp=request.timestamp
        )
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return EventResponse.from_orm(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Delete a journey event"""
    try:
        success = await service.delete_event(event_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Stage Management Endpoints
@router.post("/stages", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    request: CreateStageRequest,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Create a new journey stage"""
    try:
        stage = await service.create_stage(
            journey_id=request.journey_id,
            stage_name=request.stage_name,
            stage_type=request.stage_type,
            description=request.description,
            expected_duration=request.expected_duration,
            criteria=request.criteria
        )
        return StageResponse.from_orm(stage)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/journeys/{journey_id}/stages", response_model=List[StageResponse])
async def get_journey_stages(
    journey_id: int,
    stage_type: Optional[str] = None,
    status: Optional[str] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get stages for a specific journey"""
    try:
        stages = await service.get_journey_stages(
            journey_id=journey_id,
            stage_type=stage_type,
            status=status
        )
        return [StageResponse.from_orm(stage) for stage in stages]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/stages/{stage_id}", response_model=StageResponse)
async def get_stage(
    stage_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get a specific stage by ID"""
    try:
        stage = await service.get_stage(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
        return StageResponse.from_orm(stage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/stages/{stage_id}/complete", response_model=StageResponse)
async def complete_stage(
    stage_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Mark a stage as completed"""
    try:
        stage = await service.complete_stage(stage_id)
        if not stage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
        return StageResponse.from_orm(stage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Delete a journey stage"""
    try:
        success = await service.delete_stage(stage_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Journey Analytics and Insights
@router.get("/journeys/{journey_id}/analytics", response_model=JourneyAnalyticsResponse)
async def get_journey_analytics(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get analytics for a specific journey"""
    try:
        analytics = await service.get_journey_analytics(journey_id)
        if not analytics:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
        return JourneyAnalyticsResponse(**analytics)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/journeys/{journey_id}/map", response_model=JourneyMapResponse)
async def get_journey_map(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get a visual map of the customer journey"""
    try:
        journey_map = await service.get_journey_map(journey_id)
        if not journey_map:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
        return JourneyMapResponse(**journey_map)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/customers/{customer_id}/journey-history")
async def get_customer_journey_history(
    customer_id: str,
    limit: int = 10,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get journey history for a customer"""
    try:
        history = await service.get_customer_journey_history(customer_id, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Journey Tracking and Automation
@router.post("/track-interaction")
async def track_interaction(
    customer_id: str,
    channel: str,
    interaction_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Track a customer interaction and update journey"""
    try:
        result = await service.track_interaction(
            customer_id=customer_id,
            channel=channel,
            interaction_type=interaction_type,
            content=content,
            metadata=metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/journeys/{journey_id}/advance-stage")
async def advance_journey_stage(
    journey_id: int,
    next_stage: str,
    reason: Optional[str] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Advance a journey to the next stage"""
    try:
        result = await service.advance_journey_stage(
            journey_id=journey_id,
            next_stage=next_stage,
            reason=reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/journeys/{journey_id}/predict-next-action")
async def predict_next_action(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Predict the next likely customer action"""
    try:
        prediction = await service.predict_next_action(journey_id)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Journey Optimization and Recommendations
@router.get("/journeys/{journey_id}/recommendations")
async def get_journey_recommendations(
    journey_id: int,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get personalized recommendations for the journey"""
    try:
        recommendations = await service.get_journey_recommendations(journey_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/journey-patterns")
async def analyze_journey_patterns(
    brand_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Analyze journey patterns across customers"""
    try:
        patterns = await service.analyze_journey_patterns(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date
        )
        return patterns
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/conversion-funnels")
async def get_conversion_funnels(
    brand_id: Optional[int] = None,
    funnel_type: str = "general",
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Get conversion funnel analytics"""
    try:
        funnels = await service.get_conversion_funnels(
            brand_id=brand_id,
            funnel_type=funnel_type
        )
        return funnels
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Journey Export and Reporting
@router.post("/journeys/{journey_id}/export")
async def export_journey_data(
    journey_id: int,
    format: str = "json",
    include_events: bool = True,
    include_stages: bool = True,
    include_analytics: bool = True,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Export journey data in specified format"""
    try:
        export_data = await service.export_journey_data(
            journey_id=journey_id,
            format=format,
            include_events=include_events,
            include_stages=include_stages,
            include_analytics=include_analytics
        )
        return export_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/reports/journey-summary")
async def generate_journey_summary_report(
    brand_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: CustomerJourneyService = Depends(get_customer_journey_service)
):
    """Generate a comprehensive journey summary report"""
    try:
        report = await service.generate_journey_summary_report(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Customer Journey Tracking"""
    return {
        "status": "healthy",
        "service": "Customer Journey Tracking",
        "features": [
            "journey_management",
            "event_tracking",
            "stage_management",
            "journey_analytics",
            "journey_mapping",
            "interaction_tracking",
            "predictive_analytics",
            "journey_optimization",
            "conversion_funnels",
            "journey_export"
        ],
        "message": "Customer Journey Tracking service is running and ready!"
    }
