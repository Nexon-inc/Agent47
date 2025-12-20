from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from ..database import get_eric_database
# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.analytics.analytics_manager import AnalyticsManager
from core.event_bus.kafka_manager import EventBus as KafkaManager
from core.cache.redis_manager import RedisManager
from ..models import Lead, LeadInteraction, Deal, SalesActivity, SalesRep, CustomerProfile

logger = logging.getLogger(__name__)

class DynamicFollowUpSchedulerService:
    """Service for dynamic follow-up scheduling based on engagement patterns"""
    
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize dynamic follow-up scheduler service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.analytics_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Dynamic follow-up scheduler service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dynamic follow-up scheduler service: {e}")
            raise
        
        # Define follow-up timing rules based on engagement level
        self.follow_up_rules = {
            "high_engagement": {
                "initial_delay": 1,  # hours
                "subsequent_delay": 4,  # hours
                "max_follow_ups": 8,
                "channels": ["email", "phone", "linkedin"]
            },
            "medium_engagement": {
                "initial_delay": 4,  # hours
                "subsequent_delay": 24,  # hours
                "max_follow_ups": 6,
                "channels": ["email", "linkedin"]
            },
            "low_engagement": {
                "initial_delay": 24,  # hours
                "subsequent_delay": 72,  # hours
                "max_follow_ups": 4,
                "channels": ["email"]
            },
            "no_engagement": {
                "initial_delay": 48,  # hours
                "subsequent_delay": 168,  # hours (1 week)
                "max_follow_ups": 3,
                "channels": ["email"]
            }
        }
        
        # Define optimal timing windows
        self.optimal_timing = {
            "monday": {
                "start_hour": 9,
                "end_hour": 17,
                "best_hours": [10, 14, 16]
            },
            "tuesday": {
                "start_hour": 9,
                "end_hour": 17,
                "best_hours": [9, 11, 15]
            },
            "wednesday": {
                "start_hour": 9,
                "end_hour": 17,
                "best_hours": [10, 13, 16]
            },
            "thursday": {
                "start_hour": 9,
                "end_hour": 17,
                "best_hours": [9, 12, 15]
            },
            "friday": {
                "start_hour": 9,
                "end_hour": 16,
                "best_hours": [10, 14]
            },
            "saturday": {
                "start_hour": 10,
                "end_hour": 14,
                "best_hours": [11, 13]
            },
            "sunday": {
                "start_hour": 0,
                "end_hour": 0,
                "best_hours": []
            }
        }
    
    async def schedule_follow_up(
        self,
        lead_id: int,
        engagement_level: Optional[str] = None,
        custom_timing: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Schedule a dynamic follow-up for a lead based on engagement"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get lead information
                lead = await self._get_lead_with_context(session, lead_id)
                if not lead:
                    return {"success": False, "error": "Lead not found"}
                
                # Determine engagement level if not provided
                if not engagement_level:
                    engagement_level = await self._determine_engagement_level(session, lead_id)
                
                # Get follow-up rules
                rules = self.follow_up_rules.get(engagement_level, self.follow_up_rules["low_engagement"])
                
                # Calculate optimal timing
                optimal_time = await self._calculate_optimal_timing(lead, rules, custom_timing)
                
                # Check if we haven't exceeded max follow-ups
                current_follow_ups = await self._get_follow_up_count(session, lead_id)
                if current_follow_ups >= rules["max_follow_ups"]:
                    return {
                        "success": False,
                        "error": f"Maximum follow-ups ({rules['max_follow_ups']}) reached for this lead"
                    }
                
                # Create follow-up schedule
                follow_up_schedule = await self._create_follow_up_schedule(
                    session, lead_id, optimal_time, rules, engagement_level
                )
                
                # Store the schedule
                await self._store_follow_up_schedule(session, follow_up_schedule)
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "follow_up_scheduled",
                    {
                        "lead_id": lead_id,
                        "engagement_level": engagement_level,
                        "scheduled_time": optimal_time.isoformat(),
                        "follow_up_count": current_follow_ups + 1
                    }
                )
                
                return {
                    "success": True,
                    "follow_up_scheduled": True,
                    "lead_id": lead_id,
                    "engagement_level": engagement_level,
                    "scheduled_time": optimal_time.isoformat(),
                    "channels": rules["channels"],
                    "follow_up_count": current_follow_ups + 1,
                    "max_follow_ups": rules["max_follow_ups"]
                }
                
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_follow_up_schedule(
        self,
        lead_id: Optional[int] = None,
        rep_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get follow-up schedules with optional filters"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Build query filters
                filters = []
                if lead_id:
                    filters.append(SalesActivity.lead_id == lead_id)
                if rep_id:
                    filters.append(SalesActivity.rep_id == rep_id)
                if status:
                    filters.append(SalesActivity.metadata.contains({"status": status}))
                
                # Query follow-up activities
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.activity_type == "follow_up_schedule",
                        *filters
                    )
                ).order_by(SalesActivity.created_at.desc())
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Format results
                schedules = []
                for activity in activities:
                    metadata = activity.metadata or {}
                    schedules.append({
                        "id": activity.id,
                        "lead_id": activity.lead_id,
                        "rep_id": activity.rep_id,
                        "scheduled_time": metadata.get("scheduled_time"),
                        "engagement_level": metadata.get("engagement_level"),
                        "channels": metadata.get("channels", []),
                        "status": metadata.get("status", "pending"),
                        "follow_up_count": metadata.get("follow_up_count", 0),
                        "created_at": activity.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "schedules": schedules,
                    "total_schedules": len(schedules)
                }
                
        except Exception as e:
            logger.error(f"Error getting follow-up schedule: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_follow_up_timing(
        self,
        schedule_id: int,
        new_timing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update the timing of a scheduled follow-up"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get the schedule
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.id == schedule_id,
                        SalesActivity.activity_type == "follow_up_schedule"
                    )
                )
                
                activity = await session.execute(query)
                activity = activity.scalar_one_or_none()
                
                if not activity:
                    return {"success": False, "error": "Follow-up schedule not found"}
                
                # Update timing
                metadata = activity.metadata or {}
                metadata.update(new_timing)
                activity.metadata = metadata
                
                await session.commit()
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "follow_up_timing_updated",
                    {
                        "schedule_id": schedule_id,
                        "lead_id": activity.lead_id,
                        "new_timing": new_timing
                    }
                )
                
                return {
                    "success": True,
                    "timing_updated": True,
                    "schedule_id": schedule_id,
                    "updated_timing": new_timing
                }
                
        except Exception as e:
            logger.error(f"Error updating follow-up timing: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_follow_up(
        self,
        schedule_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a scheduled follow-up"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get the schedule
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.id == schedule_id,
                        SalesActivity.activity_type == "follow_up_schedule"
                    )
                )
                
                activity = await session.execute(query)
                activity = activity.scalar_one_or_none()
                
                if not activity:
                    return {"success": False, "error": "Follow-up schedule not found"}
                
                # Update status to cancelled
                metadata = activity.metadata or {}
                metadata["status"] = "cancelled"
                if reason:
                    metadata["cancellation_reason"] = reason
                
                activity.metadata = metadata
                await session.commit()
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "follow_up_cancelled",
                    {
                        "schedule_id": schedule_id,
                        "lead_id": activity.lead_id,
                        "reason": reason
                    }
                )
                
                return {
                    "success": True,
                    "follow_up_cancelled": True,
                    "schedule_id": schedule_id,
                    "reason": reason
                }
                
        except Exception as e:
            logger.error(f"Error cancelling follow-up: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_optimal_timing_insights(
        self,
        lead_id: Optional[int] = None,
        rep_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get insights about optimal timing for follow-ups"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Get follow-up activities
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.activity_type == "follow_up_schedule",
                        SalesActivity.created_at >= start_date
                    )
                )
                
                if lead_id:
                    query = query.where(SalesActivity.lead_id == lead_id)
                if rep_id:
                    query = query.where(SalesActivity.rep_id == rep_id)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Analyze timing patterns
                timing_analysis = await self._analyze_timing_patterns(activities)
                
                # Get response rate by timing
                response_analysis = await self._analyze_response_by_timing(session, activities)
                
                # Generate recommendations
                recommendations = await self._generate_timing_recommendations(
                    timing_analysis, response_analysis
                )
                
                return {
                    "success": True,
                    "timing_analysis": timing_analysis,
                    "response_analysis": response_analysis,
                    "recommendations": recommendations,
                    "analysis_period_days": days
                }
                
        except Exception as e:
            logger.error(f"Error getting optimal timing insights: {e}")
            return {"success": False, "error": str(e)}
    
    async def bulk_schedule_follow_ups(
        self,
        lead_ids: List[int],
        engagement_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule follow-ups for multiple leads"""
        try:
            results = []
            for lead_id in lead_ids:
                result = await self.schedule_follow_up(lead_id, engagement_level)
                results.append({
                    "lead_id": lead_id,
                    "result": result
                })
            
            # Track bulk scheduling analytics
            await self.analytics_manager.log_event(
                "bulk_follow_ups_scheduled",
                {
                    "lead_count": len(lead_ids),
                    "successful_schedules": len([r for r in results if r["result"]["success"]]),
                    "engagement_level": engagement_level
                }
            )
            
            return {
                "success": True,
                "results": results,
                "total_leads": len(lead_ids),
                "successful_schedules": len([r for r in results if r["result"]["success"]])
            }
            
        except Exception as e:
            logger.error(f"Error bulk scheduling follow-ups: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_lead_with_context(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> Optional[Lead]:
        """Get lead with full context"""
        query = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _determine_engagement_level(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> str:
        """Determine engagement level based on recent interactions"""
        try:
            # Get recent interactions (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= start_date
                )
            )
            
            interactions = await session.execute(query)
            interactions = interactions.scalars().all()
            
            if not interactions:
                return "no_engagement"
            
            # Calculate engagement score
            engagement_score = 0
            for interaction in interactions:
                interaction_type = interaction.interaction_type
                if interaction_type in ["email_open", "email_click", "form_submission"]:
                    engagement_score += 10
                elif interaction_type in ["demo_request", "phone_call"]:
                    engagement_score += 20
                elif interaction_type in ["website_visit", "social_media_engagement"]:
                    engagement_score += 5
            
            # Determine level based on score
            if engagement_score >= 50:
                return "high_engagement"
            elif engagement_score >= 20:
                return "medium_engagement"
            elif engagement_score >= 5:
                return "low_engagement"
            else:
                return "no_engagement"
                
        except Exception as e:
            logger.error(f"Error determining engagement level: {e}")
            return "low_engagement"
    
    async def _calculate_optimal_timing(
        self,
        lead: Lead,
        rules: Dict[str, Any],
        custom_timing: Optional[Dict[str, Any]]
    ) -> datetime:
        """Calculate optimal timing for follow-up"""
        try:
            if custom_timing and "scheduled_time" in custom_timing:
                return datetime.fromisoformat(custom_timing["scheduled_time"])
            
            # Get current time
            now = datetime.utcnow()
            
            # Calculate base delay
            base_delay = timedelta(hours=rules["initial_delay"])
            target_time = now + base_delay
            
            # Adjust for optimal timing windows
            optimal_time = await self._adjust_for_optimal_window(target_time)
            
            # Ensure it's not in the past
            if optimal_time <= now:
                optimal_time = now + timedelta(hours=1)
            
            return optimal_time
            
        except Exception as e:
            logger.error(f"Error calculating optimal timing: {e}")
            return datetime.utcnow() + timedelta(hours=24)
    
    async def _adjust_for_optimal_window(self, target_time: datetime) -> datetime:
        """Adjust timing to fall within optimal windows"""
        try:
            day_name = target_time.strftime("%A").lower()
            day_config = self.optimal_timing.get(day_name, self.optimal_timing["monday"])
            
            # If outside business hours, move to next business day
            if target_time.hour < day_config["start_hour"] or target_time.hour >= day_config["end_hour"]:
                # Move to next business day
                next_day = target_time + timedelta(days=1)
                while next_day.weekday() >= 5:  # Weekend
                    next_day += timedelta(days=1)
                
                # Set to start of business hours
                next_day = next_day.replace(
                    hour=day_config["start_hour"],
                    minute=0,
                    second=0,
                    microsecond=0
                )
                return next_day
            
            # If within business hours, try to align with best hours
            if day_config["best_hours"]:
                current_hour = target_time.hour
                best_hour = min(day_config["best_hours"], key=lambda x: abs(x - current_hour))
                
                if abs(best_hour - current_hour) <= 2:  # Within 2 hours of best time
                    return target_time.replace(
                        hour=best_hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
            
            return target_time
            
        except Exception as e:
            logger.error(f"Error adjusting for optimal window: {e}")
            return target_time
    
    async def _get_follow_up_count(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> int:
        """Get current follow-up count for a lead"""
        try:
            query = select(func.count(SalesActivity.id)).where(
                and_(
                    SalesActivity.lead_id == lead_id,
                    SalesActivity.activity_type == "follow_up_schedule"
                )
            )
            
            result = await session.execute(query)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting follow-up count: {e}")
            return 0
    
    async def _create_follow_up_schedule(
        self,
        session: AsyncSession,
        lead_id: int,
        scheduled_time: datetime,
        rules: Dict[str, Any],
        engagement_level: str
    ) -> Dict[str, Any]:
        """Create a follow-up schedule"""
        try:
            current_count = await self._get_follow_up_count(session, lead_id)
            
            return {
                "lead_id": lead_id,
                "scheduled_time": scheduled_time.isoformat(),
                "engagement_level": engagement_level,
                "channels": rules["channels"],
                "follow_up_count": current_count + 1,
                "max_follow_ups": rules["max_follow_ups"],
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating follow-up schedule: {e}")
            return {}
    
    async def _store_follow_up_schedule(
        self,
        session: AsyncSession,
        schedule_data: Dict[str, Any]
    ) -> None:
        """Store follow-up schedule in database"""
        try:
            activity = SalesActivity(
                activity_type="follow_up_schedule",
                lead_id=schedule_data["lead_id"],
                metadata=schedule_data
            )
            
            session.add(activity)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing follow-up schedule: {e}")
    
    async def _analyze_timing_patterns(
        self,
        activities: List[SalesActivity]
    ) -> Dict[str, Any]:
        """Analyze timing patterns from follow-up activities"""
        try:
            timing_stats = {
                "total_follow_ups": len(activities),
                "by_day": {},
                "by_hour": {},
                "by_engagement_level": {}
            }
            
            for activity in activities:
                metadata = activity.metadata or {}
                scheduled_time = metadata.get("scheduled_time")
                
                if scheduled_time:
                    dt = datetime.fromisoformat(scheduled_time)
                    day_name = dt.strftime("%A")
                    hour = dt.hour
                    engagement_level = metadata.get("engagement_level", "unknown")
                    
                    # Count by day
                    if day_name not in timing_stats["by_day"]:
                        timing_stats["by_day"][day_name] = 0
                    timing_stats["by_day"][day_name] += 1
                    
                    # Count by hour
                    if hour not in timing_stats["by_hour"]:
                        timing_stats["by_hour"][hour] = 0
                    timing_stats["by_hour"][hour] += 1
                    
                    # Count by engagement level
                    if engagement_level not in timing_stats["by_engagement_level"]:
                        timing_stats["by_engagement_level"][engagement_level] = 0
                    timing_stats["by_engagement_level"][engagement_level] += 1
            
            return timing_stats
            
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {e}")
            return {}
    
    async def _analyze_response_by_timing(
        self,
        session: AsyncSession,
        activities: List[SalesActivity]
    ) -> Dict[str, Any]:
        """Analyze response rates by timing"""
        try:
            response_analysis = {
                "by_day": {},
                "by_hour": {},
                "by_engagement_level": {}
            }
            
            for activity in activities:
                metadata = activity.metadata or {}
                scheduled_time = metadata.get("scheduled_time")
                engagement_level = metadata.get("engagement_level", "unknown")
                
                if scheduled_time:
                    dt = datetime.fromisoformat(scheduled_time)
                    day_name = dt.strftime("%A")
                    hour = dt.hour
                    
                    # Check if there was a response after this follow-up
                    response_found = await self._check_response_after_follow_up(
                        session, activity.lead_id, dt
                    )
                    
                    # Update day analysis
                    if day_name not in response_analysis["by_day"]:
                        response_analysis["by_day"][day_name] = {"total": 0, "responses": 0}
                    response_analysis["by_day"][day_name]["total"] += 1
                    if response_found:
                        response_analysis["by_day"][day_name]["responses"] += 1
                    
                    # Update hour analysis
                    if hour not in response_analysis["by_hour"]:
                        response_analysis["by_hour"][hour] = {"total": 0, "responses": 0}
                    response_analysis["by_hour"][hour]["total"] += 1
                    if response_found:
                        response_analysis["by_hour"][hour]["responses"] += 1
                    
                    # Update engagement level analysis
                    if engagement_level not in response_analysis["by_engagement_level"]:
                        response_analysis["by_engagement_level"][engagement_level] = {"total": 0, "responses": 0}
                    response_analysis["by_engagement_level"][engagement_level]["total"] += 1
                    if response_found:
                        response_analysis["by_engagement_level"][engagement_level]["responses"] += 1
            
            # Calculate response rates
            for category in response_analysis.values():
                for key, data in category.items():
                    if data["total"] > 0:
                        data["response_rate"] = (data["responses"] / data["total"]) * 100
                    else:
                        data["response_rate"] = 0
            
            return response_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response by timing: {e}")
            return {}
    
    async def _check_response_after_follow_up(
        self,
        session: AsyncSession,
        lead_id: int,
        follow_up_time: datetime
    ) -> bool:
        """Check if there was a response after a follow-up"""
        try:
            # Look for interactions within 48 hours after follow-up
            end_time = follow_up_time + timedelta(hours=48)
            
            query = select(LeadInteraction).where(
                and_(
                    LeadInteraction.lead_id == lead_id,
                    LeadInteraction.timestamp >= follow_up_time,
                    LeadInteraction.timestamp <= end_time,
                    LeadInteraction.interaction_type.in_([
                        "email_reply", "phone_call", "linkedin_message", "form_submission"
                    ])
                )
            )
            
            result = await session.execute(query)
            interactions = result.scalars().all()
            
            return len(interactions) > 0
            
        except Exception as e:
            logger.error(f"Error checking response after follow-up: {e}")
            return False
    
    async def _generate_timing_recommendations(
        self,
        timing_analysis: Dict[str, Any],
        response_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on timing analysis"""
        try:
            recommendations = []
            
            # Analyze best performing days
            if response_analysis.get("by_day"):
                best_day = max(
                    response_analysis["by_day"].items(),
                    key=lambda x: x[1].get("response_rate", 0)
                )
                recommendations.append(f"Focus follow-ups on {best_day[0]} (response rate: {best_day[1].get('response_rate', 0):.1f}%)")
            
            # Analyze best performing hours
            if response_analysis.get("by_hour"):
                best_hour = max(
                    response_analysis["by_hour"].items(),
                    key=lambda x: x[1].get("response_rate", 0)
                )
                recommendations.append(f"Schedule follow-ups around {best_hour[0]}:00 (response rate: {best_hour[1].get('response_rate', 0):.1f}%)")
            
            # Analyze engagement levels
            if response_analysis.get("by_engagement_level"):
                best_engagement = max(
                    response_analysis["by_engagement_level"].items(),
                    key=lambda x: x[1].get("response_rate", 0)
                )
                recommendations.append(f"Prioritize {best_engagement[0]} leads (response rate: {best_engagement[1].get('response_rate', 0):.1f}%)")
            
            # General recommendations
            recommendations.append("Avoid scheduling follow-ups on weekends unless lead shows high engagement")
            recommendations.append("Consider timezone differences when scheduling international leads")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating timing recommendations: {e}")
            return ["Continue monitoring and optimizing follow-up timing"]
