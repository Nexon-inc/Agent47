from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, BackgroundTasks
import httpx
import json
import asyncio
from enum import Enum

from ..models import (
    ProactiveNotification, NotificationRule, NotificationTemplate,
    CustomerProfile, SupportTicket, CustomerInteraction, SupportAgent
)
from ..schemas.proactive_notifications import (
    CreateNotificationRuleRequest, UpdateNotificationRuleRequest,
    CreateNotificationTemplateRequest, UpdateNotificationTemplateRequest,
    SendProactiveNotificationRequest, NotificationRuleResponse,
    NotificationTemplateResponse, ProactiveNotificationResponse,
    NotificationAnalyticsResponse
)
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
# NLPUtils removed - not used


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProactiveNotificationsService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_notification_rule(
        self, 
        db: Session, 
        request: CreateNotificationRuleRequest
    ) -> NotificationRuleResponse:
        """Create a new notification rule"""
        try:
            # Validate rule conditions
            if not self._validate_rule_conditions(request.conditions):
                raise HTTPException(status_code=400, detail="Invalid rule conditions")
            
            # Create notification rule
            rule = NotificationRule(
                name=request.name,
                description=request.description,
                conditions=request.conditions,
                actions=request.actions,
                is_active=request.is_active,
                priority=request.priority,
                schedule=request.schedule,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(rule)
            db.commit()
            db.refresh(rule)
            
            # Log rule creation
            await self._log_notification_event(
                "rule_created", 
                {"rule_id": rule.id, "rule_name": rule.name}
            )
            
            return NotificationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                actions=rule.actions,
                is_active=rule.is_active,
                priority=rule.priority,
                schedule=rule.schedule,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create notification rule: {str(e)}")
    
    async def get_notification_rule(
        self, 
        db: Session, 
        rule_id: int
    ) -> NotificationRuleResponse:
        """Get a notification rule by ID"""
        rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Notification rule not found")
        
        return NotificationRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            conditions=rule.conditions,
            actions=rule.actions,
            is_active=rule.is_active,
            priority=rule.priority,
            schedule=rule.schedule,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
    
    async def list_notification_rules(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[NotificationRuleResponse]:
        """List notification rules with optional filtering"""
        query = db.query(NotificationRule)
        
        if is_active is not None:
            query = query.filter(NotificationRule.is_active == is_active)
        
        rules = query.offset(skip).limit(limit).all()
        
        return [
            NotificationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                actions=rule.actions,
                is_active=rule.is_active,
                priority=rule.priority,
                schedule=rule.schedule,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            ) for rule in rules
        ]
    
    async def update_notification_rule(
        self, 
        db: Session, 
        rule_id: int, 
        request: UpdateNotificationRuleRequest
    ) -> NotificationRuleResponse:
        """Update a notification rule"""
        rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Notification rule not found")
        
        try:
            # Update fields
            if request.name is not None:
                rule.name = request.name
            if request.description is not None:
                rule.description = request.description
            if request.conditions is not None:
                if not self._validate_rule_conditions(request.conditions):
                    raise HTTPException(status_code=400, detail="Invalid rule conditions")
                rule.conditions = request.conditions
            if request.actions is not None:
                rule.actions = request.actions
            if request.is_active is not None:
                rule.is_active = request.is_active
            if request.priority is not None:
                rule.priority = request.priority
            if request.schedule is not None:
                rule.schedule = request.schedule
            
            rule.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(rule)
            
            # Log rule update
            await self._log_notification_event(
                "rule_updated", 
                {"rule_id": rule.id, "rule_name": rule.name}
            )
            
            return NotificationRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                conditions=rule.conditions,
                actions=rule.actions,
                is_active=rule.is_active,
                priority=rule.priority,
                schedule=rule.schedule,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update notification rule: {str(e)}")
    
    async def delete_notification_rule(
        self, 
        db: Session, 
        rule_id: int
    ) -> Dict[str, str]:
        """Delete a notification rule"""
        rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Notification rule not found")
        
        try:
            db.delete(rule)
            db.commit()
            
            # Log rule deletion
            await self._log_notification_event(
                "rule_deleted", 
                {"rule_id": rule_id, "rule_name": rule.name}
            )
            
            return {"message": "Notification rule deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete notification rule: {str(e)}")
    
    async def create_notification_template(
        self, 
        db: Session, 
        request: CreateNotificationTemplateRequest
    ) -> NotificationTemplateResponse:
        """Create a new notification template"""
        try:
            template = NotificationTemplate(
                name=request.name,
                description=request.description,
                content=request.content,
                variables=request.variables,
                channel=request.channel,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            return NotificationTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                channel=template.channel,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create notification template: {str(e)}")
    
    async def get_notification_template(
        self, 
        db: Session, 
        template_id: int
    ) -> NotificationTemplateResponse:
        """Get a notification template by ID"""
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Notification template not found")
        
        return NotificationTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            content=template.content,
            variables=template.variables,
            channel=template.channel,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    async def list_notification_templates(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        channel: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[NotificationTemplateResponse]:
        """List notification templates with optional filtering"""
        query = db.query(NotificationTemplate)
        
        if channel:
            query = query.filter(NotificationTemplate.channel == channel)
        if is_active is not None:
            query = query.filter(NotificationTemplate.is_active == is_active)
        
        templates = query.offset(skip).limit(limit).all()
        
        return [
            NotificationTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                channel=template.channel,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            ) for template in templates
        ]
    
    async def update_notification_template(
        self, 
        db: Session, 
        template_id: int, 
        request: UpdateNotificationTemplateRequest
    ) -> NotificationTemplateResponse:
        """Update a notification template"""
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Notification template not found")
        
        try:
            if request.name is not None:
                template.name = request.name
            if request.description is not None:
                template.description = request.description
            if request.content is not None:
                template.content = request.content
            if request.variables is not None:
                template.variables = request.variables
            if request.channel is not None:
                template.channel = request.channel
            if request.is_active is not None:
                template.is_active = request.is_active
            
            template.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(template)
            
            return NotificationTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                content=template.content,
                variables=template.variables,
                channel=template.channel,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update notification template: {str(e)}")
    
    async def delete_notification_template(
        self, 
        db: Session, 
        template_id: int
    ) -> Dict[str, str]:
        """Delete a notification template"""
        template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Notification template not found")
        
        try:
            db.delete(template)
            db.commit()
            return {"message": "Notification template deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete notification template: {str(e)}")
    
    async def send_proactive_notification(
        self, 
        db: Session, 
        request: SendProactiveNotificationRequest
    ) -> ProactiveNotificationResponse:
        """Send a proactive notification"""
        try:
            # Get template if specified
            template = None
            if request.template_id:
                template = db.query(NotificationTemplate).filter(
                    NotificationTemplate.id == request.template_id
                ).first()
                if not template:
                    raise HTTPException(status_code=404, detail="Notification template not found")
            
            # Prepare notification content
            content = request.content
            if template:
                content = self._render_template(template.content, request.variables or {})
            
            # Create notification record
            notification = ProactiveNotification(
                customer_id=request.customer_id,
                channel=request.channel,
                content=content,
                variables=request.variables or {},
                priority=request.priority,
                scheduled_at=request.scheduled_at,
                sent_at=None,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send notification immediately if not scheduled
            if not request.scheduled_at or request.scheduled_at <= datetime.utcnow():
                await self._send_notification(notification, db)
            
            return ProactiveNotificationResponse(
                id=notification.id,
                customer_id=notification.customer_id,
                channel=notification.channel,
                content=notification.content,
                variables=notification.variables,
                priority=notification.priority,
                scheduled_at=notification.scheduled_at,
                sent_at=notification.sent_at,
                status=notification.status,
                created_at=notification.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to send proactive notification: {str(e)}")
    
    async def detect_and_prevent_issues(
        self, 
        db: Session, 
        customer_id: int
    ) -> List[Dict[str, Any]]:
        """Detect potential issues and prevent them through proactive notifications"""
        try:
            # Get customer profile and recent interactions
            customer = db.query(CustomerProfile).filter(CustomerProfile.id == customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Analyze customer behavior patterns
            recent_tickets = db.query(SupportTicket).filter(
                SupportTicket.customer_id == customer_id,
                SupportTicket.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            recent_interactions = db.query(CustomerInteraction).filter(
                CustomerInteraction.customer_id == customer_id,
                CustomerInteraction.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            # Detect potential issues
            issues = []
            
            # Check for increasing ticket frequency
            if len(recent_tickets) > 5:
                issues.append({
                    "type": "high_ticket_volume",
                    "severity": "medium",
                    "description": "Customer has submitted multiple tickets recently",
                    "recommendation": "Send proactive support message"
                })
            
            # Check for negative sentiment trends
            negative_interactions = [i for i in recent_interactions if i.sentiment == "negative"]
            if len(negative_interactions) > 2:
                issues.append({
                    "type": "negative_sentiment",
                    "severity": "high",
                    "description": "Customer showing negative sentiment",
                    "recommendation": "Escalate to human agent"
                })
            
            # Check for churn risk
            if customer.trust_score < 0.3:
                issues.append({
                    "type": "churn_risk",
                    "severity": "high",
                    "description": "Customer at risk of churning",
                    "recommendation": "Send retention campaign"
                })
            
            # Check for usage patterns
            if customer.last_interaction_at and \
               (datetime.utcnow() - customer.last_interaction_at).days > 14:
                issues.append({
                    "type": "inactivity",
                    "severity": "medium",
                    "description": "Customer has been inactive",
                    "recommendation": "Send re-engagement message"
                })
            
            return issues
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to detect issues: {str(e)}")
    
    async def automated_outreach(
        self, 
        db: Session, 
        campaign_type: str,
        target_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform automated outreach campaigns"""
        try:
            # Build customer query based on criteria
            query = db.query(CustomerProfile)
            
            if target_criteria.get("min_trust_score"):
                query = query.filter(CustomerProfile.trust_score >= target_criteria["min_trust_score"])
            
            if target_criteria.get("max_trust_score"):
                query = query.filter(CustomerProfile.trust_score <= target_criteria["max_trust_score"])
            
            if target_criteria.get("last_interaction_days"):
                cutoff_date = datetime.utcnow() - timedelta(days=target_criteria["last_interaction_days"])
                query = query.filter(CustomerProfile.last_interaction_at <= cutoff_date)
            
            if target_criteria.get("has_open_tickets"):
                query = query.filter(CustomerProfile.open_tickets_count > 0)
            
            # Get target customers
            target_customers = query.all()
            
            # Get campaign template
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.name == f"{campaign_type}_campaign"
            ).first()
            
            if not template:
                raise HTTPException(status_code=404, detail=f"Campaign template not found: {campaign_type}")
            
            # Send notifications to target customers
            sent_count = 0
            failed_count = 0
            
            for customer in target_customers:
                try:
                    # Prepare variables
                    variables = {
                        "customer_name": customer.name,
                        "customer_email": customer.email,
                        "trust_score": customer.trust_score,
                        "last_interaction": customer.last_interaction_at.isoformat() if customer.last_interaction_at else "Never"
                    }
                    
                    # Create notification
                    notification = ProactiveNotification(
                        customer_id=customer.id,
                        channel=template.channel,
                        content=template.content,
                        variables=variables,
                        priority="medium",
                        scheduled_at=datetime.utcnow(),
                        sent_at=None,
                        status="pending",
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(notification)
                    db.commit()
                    
                    # Send immediately
                    await self._send_notification(notification, db)
                    sent_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    db.rollback()
                    continue
            
            return {
                "campaign_type": campaign_type,
                "target_customers": len(target_customers),
                "sent_count": sent_count,
                "failed_count": failed_count,
                "success_rate": sent_count / len(target_customers) if target_customers else 0
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to perform automated outreach: {str(e)}")
    
    async def engagement_campaigns(
        self, 
        db: Session, 
        campaign_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run engagement campaigns to improve customer satisfaction"""
        try:
            campaign_type = campaign_config.get("type", "general")
            trigger_conditions = campaign_config.get("trigger_conditions", {})
            message_template = campaign_config.get("message_template", {})
            
            # Find customers matching trigger conditions
            query = db.query(CustomerProfile)
            
            if trigger_conditions.get("low_engagement"):
                query = query.filter(CustomerProfile.engagement_score < 0.5)
            
            if trigger_conditions.get("recent_purchase"):
                days = trigger_conditions.get("purchase_days", 7)
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                # Filter customers with recent purchases
                # Join with purchase/order table for accurate data
                query = query.join(CustomerInteraction).filter(
                    and_(
                        CustomerInteraction.created_at >= cutoff_date,
                        CustomerInteraction.interaction_type == "purchase"
                    )
                )
            
            if trigger_conditions.get("birthday_this_month"):
                # Filter customers with birthdays this month
                current_month = datetime.utcnow().month
                # Filter by birthday month stored in customer profile
                query = query.filter(extract('month', CustomerProfile.birth_date) == current_month)
            
            target_customers = query.limit(campaign_config.get("max_customers", 100)).all()
            
            # Send engagement messages
            sent_count = 0
            for customer in target_customers:
                try:
                    # Prepare personalized message
                    variables = {
                        "customer_name": customer.name,
                        "engagement_score": customer.engagement_score,
                        "trust_score": customer.trust_score
                    }
                    
                    content = self._render_template(message_template.get("content", ""), variables)
                    
                    # Create notification
                    notification = ProactiveNotification(
                        customer_id=customer.id,
                        channel=message_template.get("channel", "email"),
                        content=content,
                        variables=variables,
                        priority="low",
                        scheduled_at=datetime.utcnow(),
                        sent_at=None,
                        status="pending",
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(notification)
                    db.commit()
                    
                    # Send immediately
                    await self._send_notification(notification, db)
                    sent_count += 1
                    
                except Exception as e:
                    db.rollback()
                    continue
            
            return {
                "campaign_type": campaign_type,
                "target_customers": len(target_customers),
                "sent_count": sent_count,
                "success_rate": sent_count / len(target_customers) if target_customers else 0
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to run engagement campaign: {str(e)}")
    
    async def get_notification_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> NotificationAnalyticsResponse:
        """Get analytics for proactive notifications"""
        try:
            # Get notifications in date range
            notifications = db.query(ProactiveNotification).filter(
                and_(
                    ProactiveNotification.created_at >= start_date,
                    ProactiveNotification.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_notifications = len(notifications)
            sent_notifications = len([n for n in notifications if n.status == "sent"])
            failed_notifications = len([n for n in notifications if n.status == "failed"])
            pending_notifications = len([n for n in notifications if n.status == "pending"])
            
            # Channel breakdown
            channel_stats = {}
            for notification in notifications:
                channel = notification.channel
                if channel not in channel_stats:
                    channel_stats[channel] = {"total": 0, "sent": 0, "failed": 0}
                channel_stats[channel]["total"] += 1
                if notification.status == "sent":
                    channel_stats[channel]["sent"] += 1
                elif notification.status == "failed":
                    channel_stats[channel]["failed"] += 1
            
            # Priority breakdown
            priority_stats = {}
            for notification in notifications:
                priority = notification.priority
                if priority not in priority_stats:
                    priority_stats[priority] = {"total": 0, "sent": 0, "failed": 0}
                priority_stats[priority]["total"] += 1
                if notification.status == "sent":
                    priority_stats[priority]["sent"] += 1
                elif notification.status == "failed":
                    priority_stats[priority]["failed"] += 1
            
            # Daily trends
            daily_stats = {}
            for notification in notifications:
                date_key = notification.created_at.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"total": 0, "sent": 0, "failed": 0}
                daily_stats[date_key]["total"] += 1
                if notification.status == "sent":
                    daily_stats[date_key]["sent"] += 1
                elif notification.status == "failed":
                    daily_stats[date_key]["failed"] += 1
            
            return NotificationAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_notifications=total_notifications,
                sent_notifications=sent_notifications,
                failed_notifications=failed_notifications,
                pending_notifications=pending_notifications,
                success_rate=sent_notifications / total_notifications if total_notifications > 0 else 0,
                channel_breakdown=channel_stats,
                priority_breakdown=priority_stats,
                daily_trends=daily_stats
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get notification analytics: {str(e)}")
    
    async def smart_scheduling(
        self, 
        db: Session, 
        customer_id: int,
        notification_type: str
    ) -> datetime:
        """Determine optimal time to send notification to customer"""
        try:
            # Get customer's interaction history
            interactions = db.query(CustomerInteraction).filter(
                CustomerInteraction.customer_id == customer_id
            ).order_by(CustomerInteraction.created_at.desc()).limit(100).all()
            
            if not interactions:
                # Default to business hours if no history
                return self._get_default_schedule_time()
            
            # Analyze interaction patterns
            hour_counts = {}
            day_counts = {}
            
            for interaction in interactions:
                hour = interaction.created_at.hour
                day = interaction.created_at.weekday()
                
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
            
            # Find peak activity hours
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            peak_day = max(day_counts.items(), key=lambda x: x[1])[0]
            
            # Calculate optimal time (peak hour on peak day)
            now = datetime.utcnow()
            target_time = now.replace(hour=peak_hour, minute=0, second=0, microsecond=0)
            
            # Adjust to next occurrence of peak day
            days_ahead = (peak_day - target_time.weekday()) % 7
            if days_ahead == 0 and target_time <= now:
                days_ahead = 7
            
            target_time += timedelta(days=days_ahead)
            
            return target_time
            
        except Exception as e:
            # Fallback to default scheduling
            return self._get_default_schedule_time()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of proactive notifications system"""
        try:
            # Check database connectivity
            db = next(get_db())
            rule_count = db.query(NotificationRule).count()
            template_count = db.query(NotificationTemplate).count()
            pending_notifications = db.query(ProactiveNotification).filter(
                ProactiveNotification.status == "pending"
            ).count()
            
            # Check integration health
            integration_status = await self.integration_manager.check_health()
            
            # Check notification channels
            channel_status = {}
            for channel in [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK]:
                try:
                    # Test channel connectivity
                    channel_status[channel] = "healthy"
                except Exception:
                    channel_status[channel] = "unhealthy"
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "rules_count": rule_count,
                    "templates_count": template_count,
                    "pending_notifications": pending_notifications
                },
                "integrations": integration_status,
                "channels": channel_status,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def _validate_rule_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Validate notification rule conditions"""
        try:
            required_fields = ["field", "operator", "value"]
            
            if not isinstance(conditions, dict):
                return False
            
            # Check if it's a single condition or list of conditions
            if "field" in conditions:
                # Single condition
                for field in required_fields:
                    if field not in conditions:
                        return False
            elif "conditions" in conditions:
                # Multiple conditions with logical operator
                if "operator" not in conditions:
                    return False
                if not isinstance(conditions["conditions"], list):
                    return False
                for condition in conditions["conditions"]:
                    if not self._validate_rule_conditions(condition):
                        return False
            else:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            content = template_content
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            return content
        except Exception:
            return template_content
    
    async def _send_notification(self, notification: ProactiveNotification, db: Session):
        """Send notification through appropriate channel"""
        try:
            # Update status to sending
            notification.status = "sending"
            db.commit()
            
            # Send based on channel
            if notification.channel == NotificationChannel.EMAIL:
                await self._send_email_notification(notification)
            elif notification.channel == NotificationChannel.SMS:
                await self._send_sms_notification(notification)
            elif notification.channel == NotificationChannel.SLACK:
                await self._send_slack_notification(notification)
            elif notification.channel == NotificationChannel.PUSH:
                await self._send_push_notification(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                await self._send_in_app_notification(notification)
            
            # Update status to sent
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            db.commit()
            
            # Log successful send
            await self._log_notification_event("notification_sent", {
                "notification_id": notification.id,
                "channel": notification.channel,
                "customer_id": notification.customer_id
            })
            
        except Exception as e:
            # Update status to failed
            notification.status = "failed"
            db.commit()
            
            # Log failed send
            await self._log_notification_event("notification_failed", {
                "notification_id": notification.id,
                "channel": notification.channel,
                "customer_id": notification.customer_id,
                "error": str(e)
            })
            
            raise e
    
    async def _send_email_notification(self, notification: ProactiveNotification):
        """Send email notification"""
        # Integration with email service (SendGrid, AWS SES, etc.)
        email_data = {
            "to": notification.customer_id,  # Would be email in real implementation
            "subject": "Proactive Support Notification",
            "content": notification.content,
            "variables": notification.variables
        }
        
        # Use integration manager to send email
        await self.integration_manager.send_email(email_data)
    
    async def _send_sms_notification(self, notification: ProactiveNotification):
        """Send SMS notification"""
        # Integration with SMS service (Twilio, AWS SNS, etc.)
        sms_data = {
            "to": notification.customer_id,  # Would be phone number in real implementation
            "message": notification.content,
            "variables": notification.variables
        }
        
        # Use integration manager to send SMS
        await self.integration_manager.send_sms(sms_data)
    
    async def _send_slack_notification(self, notification: ProactiveNotification):
        """Send Slack notification"""
        # Integration with Slack API
        slack_data = {
            "channel": "#support-notifications",
            "text": notification.content,
            "variables": notification.variables
        }
        
        # Use integration manager to send Slack message
        await self.integration_manager.send_slack_message(slack_data)
    
    async def _send_push_notification(self, notification: ProactiveNotification):
        """Send push notification"""
        # Integration with push notification service
        push_data = {
            "user_id": notification.customer_id,
            "title": "Proactive Support",
            "body": notification.content,
            "data": notification.variables
        }
        
        # Use integration manager to send push notification
        await self.integration_manager.send_push_notification(push_data)
    
    async def _send_webhook_notification(self, notification: ProactiveNotification):
        """Send webhook notification"""
        # Send to configured webhook URL
        webhook_data = {
            "notification_id": notification.id,
            "customer_id": notification.customer_id,
            "content": notification.content,
            "variables": notification.variables,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Use integration manager to send webhook
        await self.integration_manager.send_webhook(webhook_data)
    
    async def _send_in_app_notification(self, notification: ProactiveNotification):
        """Send in-app notification"""
        # Store notification for in-app display
        in_app_data = {
            "user_id": notification.customer_id,
            "title": "Proactive Support",
            "message": notification.content,
            "data": notification.variables,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Use integration manager to store in-app notification
        await self.integration_manager.store_in_app_notification(in_app_data)
    
    def _get_default_schedule_time(self) -> datetime:
        """Get default schedule time (business hours)"""
        now = datetime.utcnow()
        # Schedule for next business day at 10 AM
        target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # If it's weekend, move to Monday
        if target_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            days_ahead = 7 - target_time.weekday()
            target_time += timedelta(days=days_ahead)
        elif target_time <= now:
            # If time has passed today, move to tomorrow
            target_time += timedelta(days=1)
        
        return target_time
    
    async def _log_notification_event(self, event_type: str, data: Dict[str, Any]):
        """Log notification events for analytics"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Use analytics manager to log event
            await self.analytics_manager.log_event("proactive_notifications", log_data)
            
        except Exception:
            # Silently fail logging
            pass
