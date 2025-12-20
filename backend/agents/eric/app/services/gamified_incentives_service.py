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
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep
)

logger = logging.getLogger(__name__)

class GamifiedIncentivesService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize gamified incentives service"""
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
            logger.info("Gamified incentives service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gamified incentives service: {e}")
            raise
        
        self.achievement_types = {
            "deals_closed": {
                "name": "Deal Closer",
                "description": "Close deals successfully",
                "points": 100,
                "levels": [
                    {"count": 5, "name": "Bronze Closer", "points": 500},
                    {"count": 15, "name": "Silver Closer", "points": 1500},
                    {"count": 30, "name": "Gold Closer", "points": 3000},
                    {"count": 50, "name": "Platinum Closer", "points": 5000}
                ]
            },
            "leads_generated": {
                "name": "Lead Generator",
                "description": "Generate high-quality leads",
                "points": 50,
                "levels": [
                    {"count": 10, "name": "Bronze Generator", "points": 500},
                    {"count": 25, "name": "Silver Generator", "points": 1250},
                    {"count": 50, "name": "Gold Generator", "points": 2500},
                    {"count": 100, "name": "Platinum Generator", "points": 5000}
                ]
            },
            "revenue_generated": {
                "name": "Revenue Champion",
                "description": "Generate significant revenue",
                "points": 200,
                "levels": [
                    {"count": 10000, "name": "Bronze Champion", "points": 1000},
                    {"count": 50000, "name": "Silver Champion", "points": 5000},
                    {"count": 100000, "name": "Gold Champion", "points": 10000},
                    {"count": 250000, "name": "Platinum Champion", "points": 25000}
                ]
            },
            "response_time": {
                "name": "Speed Demon",
                "description": "Respond to leads quickly",
                "points": 25,
                "levels": [
                    {"count": 5, "name": "Bronze Speed", "points": 125},
                    {"count": 15, "name": "Silver Speed", "points": 375},
                    {"count": 30, "name": "Gold Speed", "points": 750},
                    {"count": 50, "name": "Platinum Speed", "points": 1250}
                ]
            },
            "customer_satisfaction": {
                "name": "Customer Advocate",
                "description": "Maintain high customer satisfaction",
                "points": 75,
                "levels": [
                    {"count": 5, "name": "Bronze Advocate", "points": 375},
                    {"count": 15, "name": "Silver Advocate", "points": 1125},
                    {"count": 30, "name": "Gold Advocate", "points": 2250},
                    {"count": 50, "name": "Platinum Advocate", "points": 3750}
                ]
            }
        }

    async def create_sales_challenge(self, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sales challenge for the team"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                challenge = {
                    "challenge_id": f"challenge_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "title": challenge_data["title"],
                    "description": challenge_data["description"],
                    "challenge_type": challenge_data["challenge_type"],
                    "target_value": challenge_data["target_value"],
                    "start_date": challenge_data["start_date"],
                    "end_date": challenge_data["end_date"],
                    "reward_points": challenge_data["reward_points"],
                    "reward_description": challenge_data["reward_description"],
                    "participants": challenge_data.get("participants", []),
                    "brand_id": challenge_data["brand_id"],
                    "created_by": challenge_data["created_by"],
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                challenge_key = f"challenge:{challenge['challenge_id']}"
                await self.redis_manager.set(
                    challenge_key,
                    json.dumps(challenge, default=str),
                    expire=86400 * 30
                )
                
                await self._publish_challenge_event("challenge_created", challenge)
                
                return {
                    "success": True,
                    "challenge": challenge
                }
                
        except Exception as e:
            logger.error(f"Failed to create sales challenge: {e}")
            return {"success": False, "error": str(e)}

    async def get_leaderboard(self, brand_id: int, period: str = "month") -> Dict[str, Any]:
        """Get sales team leaderboard"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = await self._get_period_start_date(period)
                
                sales_reps = await session.execute(
                    select(SalesRep).where(SalesRep.brand_id == brand_id)
                )
                sales_reps = sales_reps.scalars().all()
                
                leaderboard_data = []
                
                for rep in sales_reps:
                    rep_stats = await self._calculate_rep_stats(session, rep.id, start_date)
                    rep_achievements = await self._get_rep_achievements(rep.id)
                    rep_points = await self._calculate_total_points(rep_stats, rep_achievements)
                    
                    leaderboard_data.append({
                        "rep_id": rep.id,
                        "rep_name": f"{rep.first_name} {rep.last_name}",
                        "email": rep.email,
                        "total_points": rep_points,
                        "stats": rep_stats,
                        "achievements": rep_achievements,
                        "rank": 0
                    })
                
                leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
                
                for i, rep in enumerate(leaderboard_data):
                    rep["rank"] = i + 1
                
                return {
                    "success": True,
                    "leaderboard": leaderboard_data,
                    "period": period,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_rep_stats(self, session: AsyncSession, rep_id: int, start_date: datetime) -> Dict[str, Any]:
        """Calculate statistics for a sales representative"""
        try:
            deals = await session.execute(
                select(Deal).where(
                    Deal.assigned_to == rep_id,
                    Deal.created_at >= start_date
                )
            )
            deals = deals.scalars().all()
            
            leads = await session.execute(
                select(Lead).where(
                    Lead.assigned_to == rep_id,
                    Lead.created_at >= start_date
                )
            )
            leads = leads.scalars().all()
            
            activities = await session.execute(
                select(SalesActivity).where(
                    SalesActivity.assigned_to == rep_id,
                    SalesActivity.created_at >= start_date
                )
            )
            activities = activities.scalars().all()
            
            stats = {
                "deals_closed": len([deal for deal in deals if deal.status == "closed_won"]),
                "deals_lost": len([deal for deal in deals if deal.status == "closed_lost"]),
                "total_deals": len(deals),
                "leads_generated": len(leads),
                "leads_qualified": len([lead for lead in leads if lead.lead_status == "qualified"]),
                "revenue_generated": sum([deal.value for deal in deals if deal.status == "closed_won"]),
                "activities_completed": len([activity for activity in activities if activity.status == "completed"]),
                "avg_response_time": await self._calculate_avg_response_time(session, rep_id, start_date),
                "customer_satisfaction": await self._calculate_customer_satisfaction(session, rep_id, start_date)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate rep stats: {e}")
            return {}

    async def _calculate_avg_response_time(self, session: AsyncSession, rep_id: int, start_date: datetime) -> float:
        """Calculate average response time for a sales rep"""
        try:
            interactions = await session.execute(
                select(LeadInteraction).where(
                    LeadInteraction.assigned_to == rep_id,
                    LeadInteraction.created_at >= start_date,
                    LeadInteraction.response_time.isnot(None)
                )
            )
            interactions = interactions.scalars().all()
            
            if not interactions:
                return 0.0
            
            total_response_time = sum(interaction.response_time for interaction in interactions)
            return total_response_time / len(interactions)
            
        except Exception as e:
            logger.error(f"Failed to calculate avg response time: {e}")
            return 0.0

    async def _calculate_customer_satisfaction(self, session: AsyncSession, rep_id: int, start_date: datetime) -> float:
        """Calculate customer satisfaction score for a sales rep"""
        try:
            deals = await session.execute(
                select(Deal).where(
                    Deal.assigned_to == rep_id,
                    Deal.created_at >= start_date,
                    Deal.satisfaction_score.isnot(None)
                )
            )
            deals = deals.scalars().all()
            
            if not deals:
                return 0.0
            
            total_satisfaction = sum(deal.satisfaction_score for deal in deals)
            return total_satisfaction / len(deals)
            
        except Exception as e:
            logger.error(f"Failed to calculate customer satisfaction: {e}")
            return 0.0

    async def _get_rep_achievements(self, rep_id: int) -> List[Dict[str, Any]]:
        """Get achievements for a sales representative"""
        try:
            achievements_key = f"achievements:{rep_id}"
            achievements_data = await self.redis_manager.get(achievements_key)
            
            if achievements_data:
                return json.loads(achievements_data)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get rep achievements: {e}")
            return []

    async def _calculate_total_points(self, stats: Dict[str, Any], achievements: List[Dict[str, Any]]) -> int:
        """Calculate total points for a sales representative"""
        try:
            total_points = 0
            
            for achievement in achievements:
                total_points += achievement.get("points", 0)
            
            for stat_type, value in stats.items():
                if stat_type in self.achievement_types:
                    achievement_config = self.achievement_types[stat_type]
                    base_points = achievement_config["points"]
                    
                    if stat_type == "deals_closed":
                        total_points += value * base_points
                    elif stat_type == "leads_generated":
                        total_points += value * base_points
                    elif stat_type == "revenue_generated":
                        total_points += (value / 1000) * base_points
                    elif stat_type == "response_time":
                        if value < 300:  # Less than 5 minutes
                            total_points += base_points
                    elif stat_type == "customer_satisfaction":
                        if value >= 4.5:  # High satisfaction
                            total_points += base_points
            
            return total_points
            
        except Exception as e:
            logger.error(f"Failed to calculate total points: {e}")
            return 0

    async def award_points(self, rep_id: int, points: int, reason: str, achievement_type: str = None) -> Dict[str, Any]:
        """Award points to a sales representative"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                rep = await session.execute(
                    select(SalesRep).where(SalesRep.id == rep_id)
                )
                rep = rep.scalar_one_or_none()
                
                if not rep:
                    return {"success": False, "error": "Sales representative not found"}
                
                award_data = {
                    "award_id": f"award_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "rep_id": rep_id,
                    "rep_name": f"{rep.first_name} {rep.last_name}",
                    "points": points,
                    "reason": reason,
                    "achievement_type": achievement_type,
                    "awarded_at": datetime.utcnow().isoformat()
                }
                
                award_key = f"award:{award_data['award_id']}"
                await self.redis_manager.set(
                    award_key,
                    json.dumps(award_data, default=str),
                    expire=86400 * 30
                )
                
                await self._update_rep_points(rep_id, points)
                await self._check_achievements(rep_id, achievement_type)
                await self._publish_award_event(award_data)
                
                return {
                    "success": True,
                    "award": award_data
                }
                
        except Exception as e:
            logger.error(f"Failed to award points: {e}")
            return {"success": False, "error": str(e)}

    async def _update_rep_points(self, rep_id: int, points: int) -> None:
        """Update total points for a sales representative"""
        try:
            points_key = f"points:{rep_id}"
            current_points = await self.redis_manager.get(points_key)
            
            if current_points:
                total_points = int(current_points) + points
            else:
                total_points = points
            
            await self.redis_manager.set(points_key, str(total_points), expire=86400 * 30)
            
        except Exception as e:
            logger.error(f"Failed to update rep points: {e}")

    async def _check_achievements(self, rep_id: int, achievement_type: str) -> None:
        """Check and award achievements based on performance"""
        try:
            if not achievement_type or achievement_type not in self.achievement_types:
                return
            
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = datetime.utcnow() - timedelta(days=30)
                stats = await self._calculate_rep_stats(session, rep_id, start_date)
                
                achievement_config = self.achievement_types[achievement_type]
                current_value = stats.get(achievement_type, 0)
                
                for level in achievement_config["levels"]:
                    if current_value >= level["count"]:
                        await self._award_achievement(rep_id, achievement_type, level)
                        
        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")

    async def _award_achievement(self, rep_id: int, achievement_type: str, level: Dict[str, Any]) -> None:
        """Award an achievement to a sales representative"""
        try:
            achievement_data = {
                "achievement_id": f"achievement_{rep_id}_{achievement_type}_{level['count']}",
                "rep_id": rep_id,
                "achievement_type": achievement_type,
                "level_name": level["name"],
                "points": level["points"],
                "awarded_at": datetime.utcnow().isoformat()
            }
            
            achievements_key = f"achievements:{rep_id}"
            current_achievements = await self.redis_manager.get(achievements_key)
            
            if current_achievements:
                achievements = json.loads(current_achievements)
            else:
                achievements = []
            
            achievements.append(achievement_data)
            
            await self.redis_manager.set(
                achievements_key,
                json.dumps(achievements, default=str),
                expire=86400 * 30
            )
            
            await self._publish_achievement_event(achievement_data)
            
        except Exception as e:
            logger.error(f"Failed to award achievement: {e}")

    async def get_team_challenges(self, brand_id: int) -> Dict[str, Any]:
        """Get active team challenges"""
        try:
            challenges = []
            
            challenge_keys = await self.redis_manager.keys("challenge:*")
            
            for key in challenge_keys:
                challenge_data = await self.redis_manager.get(key)
                if challenge_data:
                    challenge = json.loads(challenge_data)
                    if challenge["brand_id"] == brand_id and challenge["status"] == "active":
                        challenges.append(challenge)
            
            return {
                "success": True,
                "challenges": challenges
            }
            
        except Exception as e:
            logger.error(f"Failed to get team challenges: {e}")
            return {"success": False, "error": str(e)}

    async def get_rep_performance(self, rep_id: int, period: str = "month") -> Dict[str, Any]:
        """Get detailed performance for a sales representative"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = await self._get_period_start_date(period)
                
                stats = await self._calculate_rep_stats(session, rep_id, start_date)
                achievements = await self._get_rep_achievements(rep_id)
                total_points = await self._calculate_total_points(stats, achievements)
                
                rep = await session.execute(
                    select(SalesRep).where(SalesRep.id == rep_id)
                )
                rep = rep.scalar_one_or_none()
                
                if not rep:
                    return {"success": False, "error": "Sales representative not found"}
                
                performance_data = {
                    "rep_id": rep_id,
                    "rep_name": f"{rep.first_name} {rep.last_name}",
                    "email": rep.email,
                    "period": period,
                    "total_points": total_points,
                    "stats": stats,
                    "achievements": achievements,
                    "recent_activity": await self._get_recent_activity(session, rep_id),
                    "performance_trends": await self._get_performance_trends(session, rep_id, period)
                }
                
                return {
                    "success": True,
                    "performance": performance_data
                }
                
        except Exception as e:
            logger.error(f"Failed to get rep performance: {e}")
            return {"success": False, "error": str(e)}

    async def _get_recent_activity(self, session: AsyncSession, rep_id: int) -> List[Dict[str, Any]]:
        """Get recent activity for a sales representative"""
        try:
            activities = await session.execute(
                select(SalesActivity).where(
                    SalesActivity.assigned_to == rep_id
                ).order_by(desc(SalesActivity.created_at)).limit(10)
            )
            activities = activities.scalars().all()
            
            recent_activity = []
            for activity in activities:
                recent_activity.append({
                    "activity_id": activity.id,
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "status": activity.status,
                    "created_at": activity.created_at.isoformat()
                })
            
            return recent_activity
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []

    async def _get_performance_trends(self, session: AsyncSession, rep_id: int, period: str) -> Dict[str, Any]:
        """Get performance trends for a sales representative"""
        try:
            start_date = await self._get_period_start_date(period)
            
            weekly_stats = []
            current_date = start_date
            
            while current_date <= datetime.utcnow():
                week_start = current_date
                week_end = current_date + timedelta(days=7)
                
                week_stats = await self._calculate_rep_stats(session, rep_id, week_start)
                weekly_stats.append({
                    "week": week_start.strftime("%Y-%m-%d"),
                    "stats": week_stats
                })
                
                current_date = week_end
            
            return {
                "weekly_trends": weekly_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {}

    async def _get_period_start_date(self, period: str) -> datetime:
        """Get start date for a given period"""
        current_date = datetime.utcnow()
        
        if period == "week":
            return current_date - timedelta(days=7)
        elif period == "month":
            return current_date - timedelta(days=30)
        elif period == "quarter":
            return current_date - timedelta(days=90)
        elif period == "year":
            return current_date - timedelta(days=365)
        else:
            return current_date - timedelta(days=30)

    async def _publish_challenge_event(self, event_type: str, challenge_data: Dict[str, Any]) -> None:
        """Publish challenge event to Kafka"""
        try:
            event_data = {
                "event_type": event_type,
                "challenge_id": challenge_data["challenge_id"],
                "brand_id": challenge_data["brand_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_manager.publish("eric.gamification", event_data)
        except Exception as e:
            logger.error(f"Failed to publish challenge event: {e}")

    async def _publish_award_event(self, award_data: Dict[str, Any]) -> None:
        """Publish award event to Kafka"""
        try:
            event_data = {
                "event_type": "points_awarded",
                "rep_id": award_data["rep_id"],
                "points": award_data["points"],
                "reason": award_data["reason"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_manager.publish("eric.gamification", event_data)
        except Exception as e:
            logger.error(f"Failed to publish award event: {e}")

    async def _publish_achievement_event(self, achievement_data: Dict[str, Any]) -> None:
        """Publish achievement event to Kafka"""
        try:
            event_data = {
                "event_type": "achievement_unlocked",
                "rep_id": achievement_data["rep_id"],
                "achievement_type": achievement_data["achievement_type"],
                "level_name": achievement_data["level_name"],
                "points": achievement_data["points"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_manager.publish("eric.gamification", event_data)
        except Exception as e:
            logger.error(f"Failed to publish achievement event: {e}")

    async def _generate_challenge(self, rep_id: str, challenge_type: str, target_value: float) -> Dict[str, Any]:
        """Generate a personalized sales challenge"""
        try:
            async with get_eric_database() as db:
                # Get sales rep information
                rep_query = select(SalesRep).where(SalesRep.id == rep_id)
                rep_result = await db.execute(rep_query)
                rep = rep_result.scalar_one_or_none()
                
                if not rep:
                    return {
                        "challenge_id": f"challenge_{rep_id}_{datetime.utcnow().timestamp()}",
                        "rep_id": rep_id,
                        "challenge_type": challenge_type,
                        "target_value": target_value,
                        "status": "error",
                        "message": "Sales rep not found"
                    }
                
                # Generate challenge based on type
                challenge_name = ""
                description = ""
                reward = ""
                duration_days = 30
                
                if challenge_type == "revenue":
                    challenge_name = f"Revenue Champion Challenge"
                    description = f"Generate ${target_value:,.0f} in new revenue within {duration_days} days"
                    reward = "Recognition on leaderboard + $500 bonus"
                elif challenge_type == "deals":
                    challenge_name = f"Deal Closer Challenge"
                    description = f"Close {int(target_value)} deals within {duration_days} days"
                    reward = "Deal Closer badge + $300 bonus"
                elif challenge_type == "prospects":
                    challenge_name = f"Prospecting Master Challenge"
                    description = f"Generate {int(target_value)} qualified prospects within {duration_days} days"
                    reward = "Prospecting Master badge + $200 bonus"
                else:
                    challenge_name = f"Sales Excellence Challenge"
                    description = f"Achieve {target_value}% improvement in key metrics within {duration_days} days"
                    reward = "Excellence badge + $400 bonus"
                
                # Calculate difficulty level
                if target_value > 100000:
                    difficulty = "expert"
                elif target_value > 50000:
                    difficulty = "advanced"
                elif target_value > 10000:
                    difficulty = "intermediate"
                else:
                    difficulty = "beginner"
                
                # Generate milestones
                milestones = []
                if challenge_type == "revenue":
                    milestones = [
                        {"milestone": "25% Complete", "target": target_value * 0.25, "reward": "Progress badge"},
                        {"milestone": "50% Complete", "target": target_value * 0.5, "reward": "Halfway badge"},
                        {"milestone": "75% Complete", "target": target_value * 0.75, "reward": "Almost there badge"},
                        {"milestone": "100% Complete", "target": target_value, "reward": reward}
                    ]
                else:
                    milestones = [
                        {"milestone": "25% Complete", "target": target_value * 0.25, "reward": "Progress badge"},
                        {"milestone": "50% Complete", "target": target_value * 0.5, "reward": "Halfway badge"},
                        {"milestone": "75% Complete", "target": target_value * 0.75, "reward": "Almost there badge"},
                        {"milestone": "100% Complete", "target": target_value, "reward": reward}
                    ]
                
                challenge_id = f"challenge_{rep_id}_{datetime.utcnow().timestamp()}"
                
                return {
                    "challenge_id": challenge_id,
                    "rep_id": rep_id,
                    "rep_name": f"{rep.first_name} {rep.last_name}",
                    "challenge_name": challenge_name,
                    "challenge_type": challenge_type,
                    "description": description,
                    "target_value": target_value,
                    "current_value": 0,
                    "difficulty": difficulty,
                    "duration_days": duration_days,
                    "start_date": datetime.utcnow(),
                    "end_date": datetime.utcnow() + timedelta(days=duration_days),
                    "milestones": milestones,
                    "reward": reward,
                    "status": "active",
                    "progress_percentage": 0,
                    "created_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating challenge: {e}")
            return {
                "challenge_id": f"challenge_{rep_id}_{datetime.utcnow().timestamp()}",
                "rep_id": rep_id,
                "challenge_type": challenge_type,
                "target_value": target_value,
                "status": "error",
                "message": "Error generating challenge",
                "challenge_name": "Error Challenge",
                "description": "Unable to generate challenge",
                "difficulty": "unknown",
                "duration_days": 0,
                "reward": "No reward",
                "milestones": []
            }
