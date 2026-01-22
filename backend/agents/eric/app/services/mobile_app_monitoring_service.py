from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from core.cache.redis_manager import RedisManager
from core.messaging.kafka_manager import KafkaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..database import get_eric_database
from ..models import (
    EricLead, EricLeadInteraction, EricDeal, EricSalesActivity, EricObjection,
    EricSalesCampaign, EricEmailSequence, EricSalesTeam, EricSalesRep
)

logger = logging.getLogger(__name__)

class MobileAppMonitoringService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize mobile app monitoring service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Mobile app monitoring service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mobile app monitoring service: {e}")
            raise

    async def get_mobile_dashboard(self, user_id: int, brand_id: int) -> Dict[str, Any]:
        """Get mobile dashboard with real-time analytics and actionable insights"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                current_time = datetime.utcnow()
                start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                
                leads = await session.execute(
                    select(EricLead).where(
                        EricLead.brand_id == brand_id,
                        EricLead.created_at >= start_of_day
                    )
                )
                leads = leads.scalars().all()
                
                deals = await session.execute(
                    select(EricDeal).where(
                        EricDeal.brand_id == brand_id,
                        EricDeal.created_at >= start_of_day
                    )
                )
                deals = deals.scalars().all()
                
                activities = await session.execute(
                    select(EricSalesActivity).where(
                        EricSalesActivity.brand_id == brand_id,
                        EricSalesActivity.scheduled_at >= current_time,
                        EricSalesActivity.scheduled_at <= current_time + timedelta(hours=24)
                    )
                )
                activities = activities.scalars().all()
                
                dashboard_data = {
                    "today_metrics": {
                        "new_leads": len(leads),
                        "deals_created": len(deals),
                        "deals_won": len([deal for deal in deals if deal.status == "closed_won"]),
                        "deals_lost": len([deal for deal in deals if deal.status == "closed_lost"]),
                        "revenue": sum([deal.value for deal in deals if deal.status == "closed_won"]),
                        "activities_scheduled": len(activities)
                    },
                    "urgent_actions": await self._get_urgent_actions(session, brand_id),
                    "performance_alerts": await self._get_performance_alerts(session, brand_id),
                    "quick_insights": await self._get_quick_insights(session, brand_id),
                    "pending_approvals": await self._get_pending_approvals(session, user_id, brand_id),
                    "real_time_notifications": await self._get_real_time_notifications(session, brand_id)
                }
                
                return {
                    "success": True,
                    "dashboard": dashboard_data,
                    "last_updated": current_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get mobile dashboard: {e}")
            return {"success": False, "error": str(e)}

    async def _get_urgent_actions(self, session: AsyncSession, brand_id: int) -> List[Dict[str, Any]]:
        """Get urgent actions that require immediate attention"""
        try:
            current_time = datetime.utcnow()
            
            overdue_activities = await session.execute(
                select(EricSalesActivity).where(
                    EricSalesActivity.brand_id == brand_id,
                    EricSalesActivity.scheduled_at < current_time,
                    EricSalesActivity.status == "scheduled"
                ).order_by(EricSalesActivity.scheduled_at)
            )
            overdue_activities = overdue_activities.scalars().all()
            
            high_priority_leads = await session.execute(
                select(EricLead).where(
                    EricLead.brand_id == brand_id,
                    EricLead.lead_score >= 0.8,
                    EricLead.lead_status == "new"
                ).order_by(desc(EricLead.lead_score))
            )
            high_priority_leads = high_priority_leads.scalars().all()
            
            urgent_actions = []
            
            for activity in overdue_activities[:5]:
                urgent_actions.append({
                    "action_type": "overdue_activity",
                    "priority": "high",
                    "title": f"Overdue: {activity.activity_type}",
                    "description": activity.description,
                    "due_time": activity.scheduled_at.isoformat(),
                    "action_id": activity.id,
                    "action_url": f"/activities/{activity.id}"
                })
            
            for lead in high_priority_leads[:3]:
                urgent_actions.append({
                    "action_type": "high_priority_lead",
                    "priority": "high",
                    "title": f"High Priority EricLead: {lead.first_name} {lead.last_name}",
                    "description": f"Score: {lead.lead_score}, Company: {lead.company}",
                    "lead_score": lead.lead_score,
                    "action_id": lead.id,
                    "action_url": f"/leads/{lead.id}"
                })
            
            return urgent_actions
            
        except Exception as e:
            logger.error(f"Failed to get urgent actions: {e}")
            return []

    async def _get_performance_alerts(self, session: AsyncSession, brand_id: int) -> List[Dict[str, Any]]:
        """Get performance alerts and warnings"""
        try:
            current_time = datetime.utcnow()
            start_of_week = current_time - timedelta(days=7)
            
            weekly_deals = await session.execute(
                select(EricDeal).where(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_of_week
                )
            )
            weekly_deals = weekly_deals.scalars().all()
            
            weekly_leads = await session.execute(
                select(EricLead).where(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= start_of_week
                )
            )
            weekly_leads = weekly_leads.scalars().all()
            
            alerts = []
            
            if len(weekly_leads) < 10:
                alerts.append({
                    "alert_type": "low_lead_generation",
                    "severity": "medium",
                    "title": "Low EricLead Generation",
                    "description": f"Only {len(weekly_leads)} leads generated this week",
                    "recommendation": "Increase marketing efforts and lead generation activities"
                })
            
            if len(weekly_deals) < 5:
                alerts.append({
                    "alert_type": "low_deal_creation",
                    "severity": "high",
                    "title": "Low EricDeal Creation",
                    "description": f"Only {len(weekly_deals)} deals created this week",
                    "recommendation": "Focus on lead qualification and deal progression"
                })
            
            conversion_rate = len([deal for deal in weekly_deals if deal.status == "closed_won"]) / len(weekly_deals) if weekly_deals else 0
            if conversion_rate < 0.2:
                alerts.append({
                    "alert_type": "low_conversion_rate",
                    "severity": "high",
                    "title": "Low Conversion Rate",
                    "description": f"Conversion rate is {conversion_rate:.1%}",
                    "recommendation": "Review sales process and improve closing techniques"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get performance alerts: {e}")
            return []

    async def _get_quick_insights(self, session: AsyncSession, brand_id: int) -> List[Dict[str, Any]]:
        """Get quick insights and trends"""
        try:
            current_time = datetime.utcnow()
            start_of_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            monthly_leads = await session.execute(
                select(EricLead).where(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= start_of_month
                )
            )
            monthly_leads = monthly_leads.scalars().all()
            
            monthly_deals = await session.execute(
                select(EricDeal).where(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_of_month
                )
            )
            monthly_deals = monthly_deals.scalars().all()
            
            insights = []
            
            top_lead_sources = {}
            for lead in monthly_leads:
                source = lead.lead_source.value
                top_lead_sources[source] = top_lead_sources.get(source, 0) + 1
            
            if top_lead_sources:
                best_source = max(top_lead_sources, key=top_lead_sources.get)
                insights.append({
                    "insight_type": "best_lead_source",
                    "title": "Best EricLead Source",
                    "description": f"{best_source} is generating {top_lead_sources[best_source]} leads this month",
                    "value": top_lead_sources[best_source],
                    "trend": "positive"
                })
            
            avg_deal_value = sum([deal.value for deal in monthly_deals if deal.value]) / len([deal for deal in monthly_deals if deal.value]) if monthly_deals else 0
            if avg_deal_value > 0:
                insights.append({
                    "insight_type": "average_deal_value",
                    "title": "Average EricDeal Value",
                    "description": f"Average deal value is ${avg_deal_value:,.2f}",
                    "value": avg_deal_value,
                    "trend": "stable"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get quick insights: {e}")
            return []

    async def _get_pending_approvals(self, session: AsyncSession, user_id: int, brand_id: int) -> List[Dict[str, Any]]:
        """Get pending approvals for the user"""
        try:
            pending_activities = await session.execute(
                select(EricSalesActivity).where(
                    EricSalesActivity.brand_id == brand_id,
                    EricSalesActivity.status == "pending_approval",
                    EricSalesActivity.assigned_to == user_id
                ).order_by(EricSalesActivity.created_at)
            )
            pending_activities = pending_activities.scalars().all()
            
            approvals = []
            for activity in pending_activities:
                approvals.append({
                    "approval_type": "sales_activity",
                    "title": f"Approve: {activity.activity_type}",
                    "description": activity.description,
                    "activity_id": activity.id,
                    "created_at": activity.created_at.isoformat(),
                    "priority": activity.priority
                })
            
            return approvals
            
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            return []

    async def _get_real_time_notifications(self, session: AsyncSession, brand_id: int) -> List[Dict[str, Any]]:
        """Get real-time notifications"""
        try:
            current_time = datetime.utcnow()
            recent_leads = await session.execute(
                select(EricLead).where(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= current_time - timedelta(hours=1)
                ).order_by(desc(EricLead.created_at))
            )
            recent_leads = recent_leads.scalars().all()
            
            recent_deals = await session.execute(
                select(EricDeal).where(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= current_time - timedelta(hours=1)
                ).order_by(desc(EricDeal.created_at))
            )
            recent_deals = recent_deals.scalars().all()
            
            notifications = []
            
            for lead in recent_leads:
                notifications.append({
                    "notification_type": "new_lead",
                    "title": "New EricLead",
                    "message": f"New lead from {lead.company}: {lead.first_name} {lead.last_name}",
                    "lead_id": lead.id,
                    "timestamp": lead.created_at.isoformat(),
                    "priority": "medium"
                })
            
            for deal in recent_deals:
                if deal.status == "closed_won":
                    notifications.append({
                        "notification_type": "deal_won",
                        "title": "EricDeal Won!",
                        "message": f"EricDeal closed: {deal.title} - ${deal.value:,.2f}",
                        "deal_id": deal.id,
                        "timestamp": deal.created_at.isoformat(),
                        "priority": "high"
                    })
                elif deal.status == "closed_lost":
                    notifications.append({
                        "notification_type": "deal_lost",
                        "title": "EricDeal Lost",
                        "message": f"EricDeal lost: {deal.title}",
                        "deal_id": deal.id,
                        "timestamp": deal.created_at.isoformat(),
                        "priority": "medium"
                    })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get real-time notifications: {e}")
            return []

    async def approve_mobile_action(self, user_id: int, action_id: int, action_type: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a mobile action"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                if action_type == "sales_activity":
                    activity = await session.execute(
                        select(EricSalesActivity).where(EricSalesActivity.id == action_id)
                    )
                    activity = activity.scalar_one_or_none()
                    
                    if not activity:
                        return {"success": False, "error": "Activity not found"}
                    
                    activity.status = "approved"
                    activity.approved_by = user_id
                    activity.approved_at = datetime.utcnow()
                    activity.approval_notes = approval_data.get("notes", "")
                    
                    await session.commit()
                    
                    await self._publish_approval_event(action_type, action_id, user_id, "approved")
                    
                    return {
                        "success": True,
                        "message": "Activity approved successfully",
                        "activity_id": action_id
                    }
                
                elif action_type == "deal_approval":
                    deal = await session.execute(
                        select(EricDeal).where(EricDeal.id == action_id)
                    )
                    deal = deal.scalar_one_or_none()
                    
                    if not deal:
                        return {"success": False, "error": "EricDeal not found"}
                    
                    deal.status = "approved"
                    deal.approved_by = user_id
                    deal.approved_at = datetime.utcnow()
                    
                    await session.commit()
                    
                    await self._publish_approval_event(action_type, action_id, user_id, "approved")
                    
                    return {
                        "success": True,
                        "message": "EricDeal approved successfully",
                        "deal_id": action_id
                    }
                
                else:
                    return {"success": False, "error": "Unsupported action type"}
                
        except Exception as e:
            logger.error(f"Failed to approve mobile action: {e}")
            return {"success": False, "error": str(e)}

    async def reject_mobile_action(self, user_id: int, action_id: int, action_type: str, rejection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a mobile action"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                if action_type == "sales_activity":
                    activity = await session.execute(
                        select(EricSalesActivity).where(EricSalesActivity.id == action_id)
                    )
                    activity = activity.scalar_one_or_none()
                    
                    if not activity:
                        return {"success": False, "error": "Activity not found"}
                    
                    activity.status = "rejected"
                    activity.rejected_by = user_id
                    activity.rejected_at = datetime.utcnow()
                    activity.rejection_reason = rejection_data.get("reason", "")
                    
                    await session.commit()
                    
                    await self._publish_approval_event(action_type, action_id, user_id, "rejected")
                    
                    return {
                        "success": True,
                        "message": "Activity rejected successfully",
                        "activity_id": action_id
                    }
                
                elif action_type == "deal_approval":
                    deal = await session.execute(
                        select(EricDeal).where(EricDeal.id == action_id)
                    )
                    deal = deal.scalar_one_or_none()
                    
                    if not deal:
                        return {"success": False, "error": "EricDeal not found"}
                    
                    deal.status = "rejected"
                    deal.rejected_by = user_id
                    deal.rejected_at = datetime.utcnow()
                    deal.rejection_reason = rejection_data.get("reason", "")
                    
                    await session.commit()
                    
                    await self._publish_approval_event(action_type, action_id, user_id, "rejected")
                    
                    return {
                        "success": True,
                        "message": "EricDeal rejected successfully",
                        "deal_id": action_id
                    }
                
                else:
                    return {"success": False, "error": "Unsupported action type"}
                
        except Exception as e:
            logger.error(f"Failed to reject mobile action: {e}")
            return {"success": False, "error": str(e)}

    async def get_mobile_notifications(self, user_id: int, brand_id: int, limit: int = 20) -> Dict[str, Any]:
        """Get mobile notifications for the user"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                current_time = datetime.utcnow()
                
                notifications = await self._get_real_time_notifications(session, brand_id)
                
                user_specific_notifications = await self._get_user_specific_notifications(session, user_id, brand_id)
                
                all_notifications = notifications + user_specific_notifications
                all_notifications.sort(key=lambda x: x["timestamp"], reverse=True)
                
                return {
                    "success": True,
                    "notifications": all_notifications[:limit],
                    "unread_count": len([n for n in all_notifications if not n.get("read", False)]),
                    "last_updated": current_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get mobile notifications: {e}")
            return {"success": False, "error": str(e)}

    async def _get_user_specific_notifications(self, session: AsyncSession, user_id: int, brand_id: int) -> List[Dict[str, Any]]:
        """Get user-specific notifications"""
        try:
            current_time = datetime.utcnow()
            
            user_activities = await session.execute(
                select(EricSalesActivity).where(
                    EricSalesActivity.brand_id == brand_id,
                    EricSalesActivity.assigned_to == user_id,
                    EricSalesActivity.scheduled_at >= current_time - timedelta(hours=24)
                ).order_by(desc(EricSalesActivity.scheduled_at))
            )
            user_activities = user_activities.scalars().all()
            
            notifications = []
            
            for activity in user_activities:
                if activity.scheduled_at <= current_time + timedelta(hours=1):
                    notifications.append({
                        "notification_type": "upcoming_activity",
                        "title": "Upcoming Activity",
                        "message": f"Activity scheduled: {activity.activity_type}",
                        "activity_id": activity.id,
                        "timestamp": activity.scheduled_at.isoformat(),
                        "priority": "medium"
                    })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user-specific notifications: {e}")
            return []

    async def _publish_approval_event(self, action_type: str, action_id: int, user_id: int, status: str) -> None:
        """Publish approval event to Kafka"""
        try:
            event_data = {
                "event_type": "mobile_action_approval",
                "action_type": action_type,
                "action_id": action_id,
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_manager.publish("eric.mobile_approvals", event_data)
        except Exception as e:
            logger.error(f"Failed to publish approval event: {e}")

    async def update_mobile_preferences(self, user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update mobile app preferences for the user"""
        try:
            preference_key = f"mobile_preferences:{user_id}"
            
            await self.redis_manager.set(
                preference_key,
                json.dumps(preferences),
                expire=86400 * 30
            )
            
            return {
                "success": True,
                "message": "Mobile preferences updated successfully",
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Failed to update mobile preferences: {e}")
            return {"success": False, "error": str(e)}

    async def get_mobile_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get mobile app preferences for the user"""
        try:
            preference_key = f"mobile_preferences:{user_id}"
            
            preferences_data = await self.redis_manager.get(preference_key)
            
            if preferences_data:
                preferences = json.loads(preferences_data)
            else:
                preferences = {
                    "notifications_enabled": True,
                    "push_notifications": True,
                    "email_notifications": True,
                    "dashboard_refresh_interval": 300,
                    "theme": "light",
                    "language": "en"
                }
            
            return {
                "success": True,
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Failed to get mobile preferences: {e}")
            return {"success": False, "error": str(e)}
