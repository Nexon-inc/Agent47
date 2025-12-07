from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.proactive_notifications_service import ProactiveNotificationsService
from ..models import ProactiveNotification, NotificationRule, NotificationTemplate, CustomerProfile
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateNotificationRuleRequest(BaseModel):
    rule_name: str = Field(..., description="Rule name")
    rule_type: str = Field(..., description="Rule type (issue_prevention, maintenance, update, reminder)")
    trigger_conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    notification_template_id: int = Field(..., description="Template ID to use")
    channels: List[str] = Field(..., description="Notification channels (email, sms, push, in_app)")
    priority: str = Field("medium", description="Notification priority")
    is_active: bool = Field(True, description="Rule active status")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration")

class UpdateNotificationRuleRequest(BaseModel):
    rule_name: Optional[str] = Field(None, description="Rule name")
    rule_type: Optional[str] = Field(None, description="Rule type")
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="Trigger conditions")
    notification_template_id: Optional[int] = Field(None, description="Template ID")
    channels: Optional[List[str]] = Field(None, description="Notification channels")
    priority: Optional[str] = Field(None, description="Notification priority")
    is_active: Optional[bool] = Field(None, description="Rule active status")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration")

class CreateNotificationTemplateRequest(BaseModel):
    template_name: str = Field(..., description="Template name")
    template_type: str = Field(..., description="Template type (issue_prevention, maintenance, update, reminder)")
    subject: str = Field(..., description="Email subject or notification title")
    content: str = Field(..., description="Template content")
    variables: List[str] = Field([], description="Template variables")
    channels: List[str] = Field(..., description="Supported channels")
    is_active: bool = Field(True, description="Template active status")

class UpdateNotificationTemplateRequest(BaseModel):
    template_name: Optional[str] = Field(None, description="Template name")
    template_type: Optional[str] = Field(None, description="Template type")
    subject: Optional[str] = Field(None, description="Email subject or notification title")
    content: Optional[str] = Field(None, description="Template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    channels: Optional[List[str]] = Field(None, description="Supported channels")
    is_active: Optional[bool] = Field(None, description="Template active status")

class SendProactiveNotificationRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    template_id: int = Field(..., description="Template ID")
    channels: List[str] = Field(..., description="Channels to send to")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data for template")
    priority: str = Field("medium", description="Notification priority")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled send time")

class NotificationRuleResponse(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    trigger_conditions: Dict[str, Any]
    notification_template_id: int
    channels: List[str]
    priority: str
    is_active: bool
    schedule: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NotificationTemplateResponse(BaseModel):
    id: int
    template_name: str
    template_type: str
    subject: str
    content: str
    variables: List[str]
    channels: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProactiveNotificationResponse(BaseModel):
    id: int
    customer_id: str
    template_id: int
    channels: List[str]
    context_data: Optional[Dict[str, Any]]
    priority: str
    status: str
    sent_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationAnalyticsResponse(BaseModel):
    total_notifications: int
    sent_notifications: int
    failed_notifications: int
    pending_notifications: int
    delivery_rate: float
    engagement_rate: float
    top_channels: List[Dict[str, Any]]
    top_templates: List[Dict[str, Any]]
    customer_satisfaction: float

# Dependency
async def get_proactive_notifications_service(db: AsyncSession = Depends(get_db)) -> ProactiveNotificationsService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return ProactiveNotificationsService(db, integration_manager, event_bus)

# Notification Rules Management
@router.post("/rules", response_model=NotificationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_rule(
    request: CreateNotificationRuleRequest,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Create a new notification rule"""
    try:
        rule = await service.create_notification_rule(
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            trigger_conditions=request.trigger_conditions,
            notification_template_id=request.notification_template_id,
            channels=request.channels,
            priority=request.priority,
            is_active=request.is_active,
            schedule=request.schedule
        )
        return NotificationRuleResponse.from_orm(rule)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/rules", response_model=List[NotificationRuleResponse])
async def get_notification_rules(
    rule_type: Optional[str] = None,
    active_only: bool = True,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get notification rules with optional filtering"""
    try:
        rules = await service.get_notification_rules(
            rule_type=rule_type,
            active_only=active_only
        )
        return [NotificationRuleResponse.from_orm(rule) for rule in rules]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    rule_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get a specific notification rule by ID"""
    try:
        rule = await service.get_notification_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification rule not found")
        return NotificationRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_notification_rule(
    rule_id: int,
    request: UpdateNotificationRuleRequest,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Update a notification rule"""
    try:
        rule = await service.update_notification_rule(
            rule_id=rule_id,
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            trigger_conditions=request.trigger_conditions,
            notification_template_id=request.notification_template_id,
            channels=request.channels,
            priority=request.priority,
            is_active=request.is_active,
            schedule=request.schedule
        )
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification rule not found")
        return NotificationRuleResponse.from_orm(rule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_rule(
    rule_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Delete a notification rule"""
    try:
        success = await service.delete_notification_rule(rule_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification rule not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Notification Templates Management
@router.post("/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_template(
    request: CreateNotificationTemplateRequest,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Create a new notification template"""
    try:
        template = await service.create_notification_template(
            template_name=request.template_name,
            template_type=request.template_type,
            subject=request.subject,
            content=request.content,
            variables=request.variables,
            channels=request.channels,
            is_active=request.is_active
        )
        return NotificationTemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def get_notification_templates(
    template_type: Optional[str] = None,
    active_only: bool = True,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get notification templates with optional filtering"""
    try:
        templates = await service.get_notification_templates(
            template_type=template_type,
            active_only=active_only
        )
        return [NotificationTemplateResponse.from_orm(template) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_notification_template(
    template_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get a specific notification template by ID"""
    try:
        template = await service.get_notification_template(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification template not found")
        return NotificationTemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_id: int,
    request: UpdateNotificationTemplateRequest,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Update a notification template"""
    try:
        template = await service.update_notification_template(
            template_id=template_id,
            template_name=request.template_name,
            template_type=request.template_type,
            subject=request.subject,
            content=request.content,
            variables=request.variables,
            channels=request.channels,
            is_active=request.is_active
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification template not found")
        return NotificationTemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_template(
    template_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Delete a notification template"""
    try:
        success = await service.delete_notification_template(template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Proactive Notification Management
@router.post("/send", response_model=ProactiveNotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_proactive_notification(
    request: SendProactiveNotificationRequest,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Send a proactive notification"""
    try:
        notification = await service.send_proactive_notification(
            customer_id=request.customer_id,
            template_id=request.template_id,
            channels=request.channels,
            context_data=request.context_data,
            priority=request.priority,
            scheduled_at=request.scheduled_at
        )
        return ProactiveNotificationResponse.from_orm(notification)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/notifications", response_model=List[ProactiveNotificationResponse])
async def get_proactive_notifications(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get proactive notifications with optional filtering"""
    try:
        notifications = await service.get_proactive_notifications(
            customer_id=customer_id,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date
        )
        return [ProactiveNotificationResponse.from_orm(notification) for notification in notifications]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/notifications/{notification_id}", response_model=ProactiveNotificationResponse)
async def get_proactive_notification(
    notification_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get a specific proactive notification by ID"""
    try:
        notification = await service.get_proactive_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proactive notification not found")
        return ProactiveNotificationResponse.from_orm(notification)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/notifications/{notification_id}/cancel", response_model=ProactiveNotificationResponse)
async def cancel_proactive_notification(
    notification_id: int,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Cancel a scheduled proactive notification"""
    try:
        notification = await service.cancel_proactive_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proactive notification not found")
        return ProactiveNotificationResponse.from_orm(notification)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Proactive Issue Detection and Prevention
@router.post("/detect-issues")
async def detect_potential_issues(
    customer_id: Optional[str] = None,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Detect potential issues for proactive notification"""
    try:
        issues = await service.detect_potential_issues(customer_id)
        return issues
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/prevent-issues")
async def prevent_issues(
    customer_id: str,
    issue_type: str,
    prevention_strategy: str,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Implement issue prevention strategy"""
    try:
        result = await service.prevent_issues(
            customer_id=customer_id,
            issue_type=issue_type,
            prevention_strategy=prevention_strategy
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Automated Outreach and Engagement
@router.post("/automated-outreach")
async def trigger_automated_outreach(
    customer_segment: str,
    outreach_type: str,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Trigger automated outreach campaign"""
    try:
        result = await service.trigger_automated_outreach(
            customer_segment=customer_segment,
            outreach_type=outreach_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/engagement-campaign")
async def create_engagement_campaign(
    campaign_name: str,
    target_audience: Dict[str, Any],
    campaign_type: str,
    schedule: Dict[str, Any],
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Create an engagement campaign"""
    try:
        campaign = await service.create_engagement_campaign(
            campaign_name=campaign_name,
            target_audience=target_audience,
            campaign_type=campaign_type,
            schedule=schedule
        )
        return campaign
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Analytics and Reporting
@router.get("/analytics", response_model=NotificationAnalyticsResponse)
async def get_notification_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get notification analytics"""
    try:
        analytics = await service.get_notification_analytics(
            start_date=start_date,
            end_date=end_date
        )
        return NotificationAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/effectiveness")
async def get_notification_effectiveness(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get notification effectiveness metrics"""
    try:
        effectiveness = await service.get_notification_effectiveness(
            start_date=start_date,
            end_date=end_date
        )
        return effectiveness
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/customer-engagement")
async def get_customer_engagement_metrics(
    customer_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Get customer engagement metrics"""
    try:
        engagement = await service.get_customer_engagement_metrics(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        return engagement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Smart Scheduling and Optimization
@router.post("/optimize-schedule")
async def optimize_notification_schedule(
    customer_id: str,
    notification_type: str,
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Optimize notification schedule for a customer"""
    try:
        optimized_schedule = await service.optimize_notification_schedule(
            customer_id=customer_id,
            notification_type=notification_type
        )
        return optimized_schedule
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/batch-schedule")
async def schedule_batch_notifications(
    customer_ids: List[str],
    template_id: int,
    schedule_config: Dict[str, Any],
    service: ProactiveNotificationsService = Depends(get_proactive_notifications_service)
):
    """Schedule batch notifications"""
    try:
        result = await service.schedule_batch_notifications(
            customer_ids=customer_ids,
            template_id=template_id,
            schedule_config=schedule_config
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Proactive Support Notifications"""
    return {
        "status": "healthy",
        "service": "Proactive Support Notifications",
        "features": [
            "notification_rules_management",
            "notification_templates",
            "proactive_notifications",
            "issue_detection_prevention",
            "automated_outreach",
            "engagement_campaigns",
            "notification_analytics",
            "smart_scheduling",
            "batch_notifications"
        ],
        "message": "Proactive Support Notifications service is running and ready!"
    }
