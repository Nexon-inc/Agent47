import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.orm import selectinload
from ..database import get_clara_database
from ..models import (
    SupportAgent, SupportTicket, CustomerInteraction, CustomerFeedback,
    TicketStatus, TicketPriority, SupportChannel
)

logger = logging.getLogger(__name__)

class GamifiedPerformanceService:
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize gamified performance service"""
        if self._initialized:
            return
        
        try:
            self._initialized = True
            logger.info("Gamified performance service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gamified performance service: {e}")
            raise
    
    async def get_agent_leaderboard(
        self,
        period: str = "monthly",  # daily, weekly, monthly, yearly
        limit: int = 20,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get agent performance leaderboard"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Calculate date range based on period
                now = datetime.utcnow()
                if period == "daily":
                    start_date = now - timedelta(days=1)
                elif period == "weekly":
                    start_date = now - timedelta(weeks=1)
                elif period == "monthly":
                    start_date = now - timedelta(days=30)
                elif period == "yearly":
                    start_date = now - timedelta(days=365)
                else:
                    start_date = now - timedelta(days=30)
                
                # Build base query for agent performance
                query = select(
                    SupportAgent.id,
                    SupportAgent.user_id,
                    SupportAgent.agent_code,
                    SupportAgent.performance_score,
                    SupportAgent.response_time_avg,
                    SupportAgent.resolution_rate,
                    SupportAgent.customer_satisfaction_avg,
                    SupportAgent.total_tickets_resolved,
                    SupportAgent.total_tickets_escalated
                ).where(SupportAgent.availability_status != "offline")
                
                agents = await session.execute(query)
                agents = agents.all()
                
                # Calculate performance metrics for each agent
                agent_performances = []
                for agent in agents:
                    # Get tickets resolved in period
                    resolved_tickets = await session.execute(
                        select(func.count(SupportTicket.id)).where(
                            and_(
                                SupportTicket.assigned_agent_id == agent.id,
                                SupportTicket.status == TicketStatus.RESOLVED,
                                SupportTicket.resolved_at >= start_date
                            )
                        )
                    )
                    resolved_count = resolved_tickets.scalar() or 0
                    
                    # Get average satisfaction for period
                    satisfaction_scores = await session.execute(
                        select(SupportTicket.satisfaction_score).where(
                            and_(
                                SupportTicket.assigned_agent_id == agent.id,
                                SupportTicket.satisfaction_score.isnot(None),
                                SupportTicket.updated_at >= start_date
                            )
                        )
                    )
                    satisfaction_scores = satisfaction_scores.scalars().all()
                    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
                    
                    # Get response time for period
                    response_times = await session.execute(
                        select(SupportTicket.first_response_time).where(
                            and_(
                                SupportTicket.assigned_agent_id == agent.id,
                                SupportTicket.first_response_time.isnot(None),
                                SupportTicket.created_at >= start_date
                            )
                        )
                    )
                    response_times = response_times.scalars().all()
                    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                    
                    # Calculate performance score
                    performance_score = self._calculate_performance_score(
                        resolved_count=resolved_count,
                        avg_satisfaction=avg_satisfaction,
                        avg_response_time=avg_response_time,
                        escalation_rate=agent.total_tickets_escalated / max(agent.total_tickets_resolved, 1)
                    )
                    
                    agent_performances.append({
                        "agent_id": agent.id,
                        "user_id": agent.user_id,
                        "agent_code": agent.agent_code,
                        "performance_score": round(performance_score, 2),
                        "resolved_tickets": resolved_count,
                        "avg_satisfaction": round(avg_satisfaction, 2),
                        "avg_response_time": round(avg_response_time, 2),
                        "escalation_rate": round((agent.total_tickets_escalated / max(agent.total_tickets_resolved, 1)) * 100, 2)
                    })
                
                # Sort by performance score and apply limit
                agent_performances.sort(key=lambda x: x["performance_score"], reverse=True)
                top_agents = agent_performances[:limit]
                
                # Add rankings and badges
                for i, agent in enumerate(top_agents):
                    agent["rank"] = i + 1
                    agent["badge"] = self._get_agent_badge(agent["performance_score"])
                    agent["tier"] = self._get_agent_tier(agent["performance_score"])
                
                return {
                    "success": True,
                    "leaderboard": {
                        "period": period,
                        "start_date": start_date.isoformat(),
                        "end_date": now.isoformat(),
                        "total_agents": len(agent_performances),
                        "top_agents": top_agents
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get agent leaderboard: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_agent_achievements(
        self,
        agent_id: int,
        period: str = "all_time"
    ) -> Dict[str, Any]:
        """Get agent achievements and milestones"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get agent
                agent = await session.execute(
                    select(SupportAgent).where(SupportAgent.id == agent_id)
                )
                agent = agent.scalar_one_or_none()
                
                if not agent:
                    return {"success": False, "error": "Agent not found"}
                
                # Calculate date range
                now = datetime.utcnow()
                if period == "daily":
                    start_date = now - timedelta(days=1)
                elif period == "weekly":
                    start_date = now - timedelta(weeks=1)
                elif period == "monthly":
                    start_date = now - timedelta(days=30)
                elif period == "yearly":
                    start_date = now - timedelta(days=365)
                else:
                    start_date = None
                
                # Get tickets for period
                ticket_query = select(SupportTicket).where(SupportTicket.assigned_agent_id == agent_id)
                if start_date:
                    ticket_query = ticket_query.where(SupportTicket.created_at >= start_date)
                
                tickets = await session.execute(ticket_query)
                tickets = tickets.scalars().all()
                
                # Calculate achievements
                achievements = []
                
                # Resolution achievements
                resolved_count = len([t for t in tickets if t.status == TicketStatus.RESOLVED])
                if resolved_count >= 100:
                    achievements.append({
                        "type": "resolution_master",
                        "title": "Resolution Master",
                        "description": f"Resolved {resolved_count} tickets",
                        "icon": "🎯",
                        "unlocked": True,
                        "progress": 100
                    })
                elif resolved_count >= 50:
                    achievements.append({
                        "type": "resolution_master",
                        "title": "Resolution Master",
                        "description": f"Resolved {resolved_count}/100 tickets",
                        "icon": "🎯",
                        "unlocked": False,
                        "progress": resolved_count
                    })
                
                # Speed achievements
                fast_resolutions = [t for t in tickets if t.actual_resolution_time and t.actual_resolution_time <= 60]
                if len(fast_resolutions) >= 20:
                    achievements.append({
                        "type": "speed_demon",
                        "title": "Speed Demon",
                        "description": f"Resolved {len(fast_resolutions)} tickets in under 1 hour",
                        "icon": "⚡",
                        "unlocked": True,
                        "progress": 100
                    })
                elif len(fast_resolutions) >= 10:
                    achievements.append({
                        "type": "speed_demon",
                        "title": "Speed Demon",
                        "description": f"Resolved {len(fast_resolutions)}/20 tickets in under 1 hour",
                        "icon": "⚡",
                        "unlocked": False,
                        "progress": len(fast_resolutions)
                    })
                
                # Satisfaction achievements
                high_satisfaction_tickets = [t for t in tickets if t.satisfaction_score and t.satisfaction_score >= 4.5]
                if len(high_satisfaction_tickets) >= 30:
                    achievements.append({
                        "type": "customer_champion",
                        "title": "Customer Champion",
                        "description": f"Received {len(high_satisfaction_tickets)} high satisfaction ratings",
                        "icon": "🏆",
                        "unlocked": True,
                        "progress": 100
                    })
                elif len(high_satisfaction_tickets) >= 15:
                    achievements.append({
                        "type": "customer_champion",
                        "title": "Customer Champion",
                        "description": f"Received {len(high_satisfaction_tickets)}/30 high satisfaction ratings",
                        "icon": "🏆",
                        "unlocked": False,
                        "progress": len(high_satisfaction_tickets)
                    })
                
                # Streak achievements
                if period == "daily":
                    # Check for daily streaks
                    consecutive_days = await self._get_consecutive_active_days(agent_id, session)
                    if consecutive_days >= 30:
                        achievements.append({
                            "type": "dedication",
                            "title": "Dedication Master",
                            "description": f"Active for {consecutive_days} consecutive days",
                            "icon": "🔥",
                            "unlocked": True,
                            "progress": 100
                        })
                    elif consecutive_days >= 7:
                        achievements.append({
                            "type": "dedication",
                            "title": "Dedication Master",
                            "description": f"Active for {consecutive_days}/30 consecutive days",
                            "icon": "🔥",
                            "unlocked": False,
                            "progress": consecutive_days
                        })
                
                # Special achievements
                if agent.performance_score >= 9.0:
                    achievements.append({
                        "type": "excellence",
                        "title": "Excellence Award",
                        "description": "Maintained exceptional performance score",
                        "icon": "⭐",
                        "unlocked": True,
                        "progress": 100
                    })
                
                if agent.total_tickets_resolved >= 1000:
                    achievements.append({
                        "type": "veteran",
                        "title": "Veteran Agent",
                        "description": "Resolved over 1000 tickets",
                        "icon": "👑",
                        "unlocked": True,
                        "progress": 100
                    })
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "period": period,
                    "achievements": achievements,
                    "total_achievements": len(achievements),
                    "unlocked_count": len([a for a in achievements if a["unlocked"]]),
                    "progress_percentage": round((len([a for a in achievements if a["unlocked"]]) / max(len(achievements), 1)) * 100, 1)
                }
                
        except Exception as e:
            logger.error(f"Failed to get agent achievements: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_team_challenges(
        self,
        team_id: Optional[int] = None,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """Get team challenges and goals"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Calculate date range
                now = datetime.utcnow()
                if period == "weekly":
                    start_date = now - timedelta(weeks=1)
                elif period == "monthly":
                    start_date = now - timedelta(days=30)
                elif period == "quarterly":
                    start_date = now - timedelta(days=90)
                else:
                    start_date = now - timedelta(days=30)
                
                # Get all agents (or team agents if team_id specified)
                agent_query = select(SupportAgent).where(SupportAgent.availability_status != "offline")
                if team_id:
                    # This would need team relationship in models
                    pass
                
                agents = await session.execute(agent_query)
                agents = agents.scalars().all()
                
                # Define team challenges
                challenges = [
                    {
                        "id": "resolution_speed",
                        "title": "Speed Challenge",
                        "description": "Resolve tickets faster than last period",
                        "icon": "⚡",
                        "type": "improvement",
                        "metric": "avg_resolution_time",
                        "target": "reduce_by_20_percent",
                        "reward": "Speed Champion Badge"
                    },
                    {
                        "id": "customer_satisfaction",
                        "title": "Satisfaction Challenge",
                        "description": "Maintain high customer satisfaction",
                        "icon": "😊",
                        "type": "maintenance",
                        "metric": "avg_satisfaction",
                        "target": "above_4_5",
                        "reward": "Customer Champion Badge"
                    },
                    {
                        "id": "first_contact_resolution",
                        "title": "FCR Challenge",
                        "description": "Improve first contact resolution rate",
                        "icon": "🎯",
                        "type": "improvement",
                        "metric": "fcr_rate",
                        "target": "above_80_percent",
                        "reward": "Resolution Master Badge"
                    },
                    {
                        "id": "response_time",
                        "title": "Responsiveness Challenge",
                        "description": "Respond to tickets quickly",
                        "icon": "⏰",
                        "type": "improvement",
                        "metric": "avg_response_time",
                        "target": "under_30_minutes",
                        "reward": "Quick Response Badge"
                    }
                ]
                
                # Calculate current performance for each challenge
                for challenge in challenges:
                    if challenge["metric"] == "avg_resolution_time":
                        total_time = 0
                        count = 0
                        for agent in agents:
                            agent_tickets = await session.execute(
                                select(SupportTicket.actual_resolution_time).where(
                                    and_(
                                        SupportTicket.assigned_agent_id == agent.id,
                                        SupportTicket.actual_resolution_time.isnot(None),
                                        SupportTicket.resolved_at >= start_date
                                    )
                                )
                            )
                            agent_times = agent_tickets.scalars().all()
                            if agent_times:
                                total_time += sum(agent_times)
                                count += len(agent_times)
                        
                        challenge["current_value"] = round(total_time / max(count, 1), 2) if count > 0 else 0
                        challenge["target_value"] = "Under 2 hours"
                        challenge["progress"] = min(100, max(0, (120 - challenge["current_value"]) / 120 * 100))
                        
                    elif challenge["metric"] == "avg_satisfaction":
                        total_satisfaction = 0
                        count = 0
                        for agent in agents:
                            agent_satisfaction = await session.execute(
                                select(SupportTicket.satisfaction_score).where(
                                    and_(
                                        SupportTicket.assigned_agent_id == agent.id,
                                        SupportTicket.satisfaction_score.isnot(None),
                                        SupportTicket.updated_at >= start_date
                                    )
                                )
                            )
                            agent_scores = agent_satisfaction.scalars().all()
                            if agent_scores:
                                total_satisfaction += sum(agent_scores)
                                count += len(agent_scores)
                        
                        challenge["current_value"] = round(total_satisfaction / max(count, 1), 2) if count > 0 else 0
                        challenge["target_value"] = "Above 4.5"
                        challenge["progress"] = min(100, max(0, (challenge["current_value"] / 5.0) * 100))
                        
                    elif challenge["metric"] == "fcr_rate":
                        total_tickets = 0
                        fcr_tickets = 0
                        for agent in agents:
                            agent_tickets = await session.execute(
                                select(func.count(SupportTicket.id)).where(
                                    and_(
                                        SupportTicket.assigned_agent_id == agent.id,
                                        SupportTicket.created_at >= start_date
                                    )
                                )
                            )
                            agent_total = agent_tickets.scalar() or 0
                            total_tickets += agent_total
                            
                            agent_fcr = await session.execute(
                                select(func.count(SupportTicket.id)).where(
                                    and_(
                                        SupportTicket.assigned_agent_id == agent.id,
                                        SupportTicket.created_at >= start_date,
                                        SupportTicket.interactions.any(CustomerInteraction.interaction_type == "resolution")
                                    )
                                )
                            )
                            agent_fcr_count = agent_fcr.scalar() or 0
                            fcr_tickets += agent_fcr_count
                        
                        challenge["current_value"] = round((fcr_tickets / max(total_tickets, 1)) * 100, 1) if total_tickets > 0 else 0
                        challenge["target_value"] = "Above 80%"
                        challenge["progress"] = min(100, max(0, challenge["current_value"]))
                        
                    elif challenge["metric"] == "avg_response_time":
                        total_time = 0
                        count = 0
                        for agent in agents:
                            agent_tickets = await session.execute(
                                select(SupportTicket.first_response_time).where(
                                    and_(
                                        SupportTicket.assigned_agent_id == agent.id,
                                        SupportTicket.first_response_time.isnot(None),
                                        SupportTicket.created_at >= start_date
                                    )
                                )
                            )
                            agent_times = agent_tickets.scalars().all()
                            if agent_times:
                                total_time += sum(agent_times)
                                count += len(agent_times)
                        
                        challenge["current_value"] = round(total_time / max(count, 1), 2) if count > 0 else 0
                        challenge["target_value"] = "Under 30 minutes"
                        challenge["progress"] = min(100, max(0, (30 - challenge["current_value"]) / 30 * 100))
                    
                    # Determine completion status
                    if challenge["progress"] >= 100:
                        challenge["status"] = "completed"
                        challenge["completion_date"] = now.isoformat()
                    elif challenge["progress"] >= 75:
                        challenge["status"] = "nearly_complete"
                    elif challenge["progress"] >= 50:
                        challenge["status"] = "in_progress"
                    else:
                        challenge["status"] = "needs_attention"
                
                return {
                    "success": True,
                    "team_id": team_id,
                    "period": period,
                    "start_date": start_date.isoformat(),
                    "end_date": now.isoformat(),
                    "challenges": challenges,
                    "total_challenges": len(challenges),
                    "completed_challenges": len([c for c in challenges if c["status"] == "completed"]),
                    "overall_progress": round(sum(c["progress"] for c in challenges) / len(challenges), 1)
                }
                
        except Exception as e:
            logger.error(f"Failed to get team challenges: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_performance_score(
        self,
        resolved_count: int,
        avg_satisfaction: float,
        avg_response_time: float,
        escalation_rate: float
    ) -> float:
        """Calculate agent performance score"""
        # Base score from resolved tickets
        base_score = min(10.0, resolved_count * 0.1)
        
        # Satisfaction bonus (0-3 points)
        satisfaction_bonus = min(3.0, avg_satisfaction * 0.6)
        
        # Response time bonus (0-2 points)
        response_bonus = max(0, 2.0 - (avg_response_time / 60))  # Bonus for fast response
        
        # Escalation penalty (0-2 points)
        escalation_penalty = min(2.0, escalation_rate * 2.0)
        
        # Calculate final score
        final_score = base_score + satisfaction_bonus + response_bonus - escalation_penalty
        
        return max(0.0, min(10.0, final_score))
    
    def _get_agent_badge(self, performance_score: float) -> str:
        """Get agent badge based on performance score"""
        if performance_score >= 9.5:
            return "🏆 Legend"
        elif performance_score >= 9.0:
            return "⭐ Elite"
        elif performance_score >= 8.0:
            return "🥇 Gold"
        elif performance_score >= 7.0:
            return "🥈 Silver"
        elif performance_score >= 6.0:
            return "🥉 Bronze"
        else:
            return "🌱 Rookie"
    
    def _get_agent_tier(self, performance_score: float) -> str:
        """Get agent tier based on performance score"""
        if performance_score >= 9.0:
            return "expert"
        elif performance_score >= 7.5:
            return "advanced"
        elif performance_score >= 6.0:
            return "intermediate"
        else:
            return "beginner"
    
    async def _get_consecutive_active_days(self, agent_id: int, session: AsyncSession) -> int:
        """Get consecutive days agent has been active"""
        try:
            # Get all tickets for agent
            tickets = await session.execute(
                select(SupportTicket.created_at).where(
                    SupportTicket.assigned_agent_id == agent_id
                ).order_by(SupportTicket.created_at.desc())
            )
            ticket_dates = tickets.scalars().all()
            
            if not ticket_dates:
                return 0
            
            # Get unique dates
            unique_dates = set()
            for ticket in ticket_dates:
                unique_dates.add(ticket.date())
            
            # Sort dates
            sorted_dates = sorted(unique_dates, reverse=True)
            
            # Calculate consecutive days
            consecutive_days = 1
            current_date = sorted_dates[0]
            
            for i in range(1, len(sorted_dates)):
                if (current_date - sorted_dates[i]).days == 1:
                    consecutive_days += 1
                    current_date = sorted_dates[i]
                else:
                    break
            
            return consecutive_days
            
        except Exception as e:
            logger.error(f"Failed to get consecutive active days: {e}")
            return 0
