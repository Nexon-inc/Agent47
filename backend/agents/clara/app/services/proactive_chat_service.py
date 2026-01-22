import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, desc
from sqlalchemy.orm import selectinload
from core.ai import get_ai_service_manager, AIServiceManager
from ..database import get_clara_database
from ..models import (
    ClaraSupportTicket, CustomerProfile, ClaraChatSession, ClaraCustomerInteraction,
    TicketCategory, SupportChannel, SentimentType
)

logger = logging.getLogger(__name__)

class ProactiveChatService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize proactive chat service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Proactive chat service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize proactive chat service: {e}")
            raise
    
    async def analyze_customer_behavior(
        self,
        customer_id: int,
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze customer behavior for proactive engagement opportunities"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile = await session.execute(
                    select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    return {"success": False, "error": "Customer profile not found"}
                
                # Calculate analysis period
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=analysis_period_days)
                
                # Get customer's recent activity
                recent_tickets = await session.execute(
                    select(ClaraSupportTicket).where(
                        and_(
                            ClaraSupportTicket.customer_id == customer_id,
                            ClaraSupportTicket.created_at >= start_date
                        )
                    ).order_by(ClaraSupportTicket.created_at.desc())
                )
                recent_tickets = recent_tickets.scalars().all()
                
                # Get recent chat sessions
                recent_chats = await session.execute(
                    select(ClaraChatSession).where(
                        and_(
                            ClaraChatSession.customer_id == customer_id,
                            ClaraChatSession.start_time >= start_date
                        )
                    ).order_by(ClaraChatSession.start_time.desc())
                )
                recent_chats = recent_chats.scalars().all()
                
                # Analyze behavior patterns
                behavior_analysis = {
                    "engagement_level": self._calculate_engagement_level(recent_tickets, recent_chats),
                    "support_frequency": len(recent_tickets),
                    "chat_activity": len(recent_chats),
                    "last_activity": self._get_last_activity(recent_tickets, recent_chats),
                    "satisfaction_trend": self._analyze_satisfaction_trend(recent_tickets),
                    "issue_patterns": self._analyze_issue_patterns(recent_tickets),
                    "channel_preferences": self._analyze_channel_preferences(recent_tickets, recent_chats),
                    "proactive_triggers": []
                }
                
                # Identify proactive engagement triggers
                triggers = await self._identify_proactive_triggers(
                    customer_id, profile, recent_tickets, recent_chats, behavior_analysis
                )
                behavior_analysis["proactive_triggers"] = triggers
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "analysis_period": f"{analysis_period_days} days",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "behavior_analysis": behavior_analysis,
                    "recommendations": self._generate_behavior_recommendations(behavior_analysis)
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze customer behavior: {e}")
            return {"success": False, "error": str(e)}
    
    async def should_initiate_proactive_chat(
        self,
        customer_id: int,
        trigger_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Determine if proactive chat should be initiated"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Check if customer already has an active chat
                active_chat = await session.execute(
                    select(ClaraChatSession).where(
                        and_(
                            ClaraChatSession.customer_id == customer_id,
                            ClaraChatSession.status == "active"
                        )
                    )
                )
                active_chat = active_chat.scalar_one_or_none()
                
                if active_chat:
                    return {
                        "should_initiate": False,
                        "reason": "Customer already has active chat session",
                        "existing_session_id": active_chat.session_id
                    }
                
                # Check if customer has been contacted recently (avoid spam)
                recent_contact = await session.execute(
                    select(ClaraCustomerInteraction).where(
                        and_(
                            ClaraCustomerInteraction.customer_id == customer_id,
                            ClaraCustomerInteraction.interaction_type == "proactive_outreach",
                            ClaraCustomerInteraction.created_at >= datetime.utcnow() - timedelta(hours=24)
                        )
                    )
                )
                recent_contact = recent_contact.scalar_one_or_none()
                
                if recent_contact:
                    return {
                        "should_initiate": False,
                        "reason": "Customer contacted recently (within 24 hours)",
                        "last_contact": recent_contact.created_at.isoformat()
                    }
                
                # Get customer behavior analysis
                behavior_result = await self.analyze_customer_behavior(customer_id, 7)  # Last 7 days
                if not behavior_result["success"]:
                    return {
                        "should_initiate": False,
                        "reason": "Failed to analyze customer behavior",
                        "error": behavior_result.get("error")
                    }
                
                behavior_analysis = behavior_result["behavior_analysis"]
                
                # Check specific triggers
                if trigger_type:
                    # Check if this specific trigger is active
                    trigger_active = any(
                        trigger["type"] == trigger_type and trigger["active"] 
                        for trigger in behavior_analysis["proactive_triggers"]
                    )
                    
                    if not trigger_active:
                        return {
                            "should_initiate": False,
                            "reason": f"Specific trigger '{trigger_type}' is not active",
                            "trigger_status": "inactive"
                        }
                
                # Overall decision based on behavior analysis
                should_initiate = self._evaluate_proactive_decision(behavior_analysis)
                
                return {
                    "should_initiate": should_initiate,
                    "reason": "Behavior analysis indicates proactive engagement opportunity" if should_initiate else "No immediate engagement opportunity",
                    "confidence_score": self._calculate_confidence_score(behavior_analysis),
                    "recommended_approach": self._get_recommended_approach(behavior_analysis),
                    "behavior_analysis": behavior_analysis
                }
                
        except Exception as e:
            logger.error(f"Failed to determine proactive chat initiation: {e}")
            return {"should_initiate": False, "error": str(e)}
    
    async def initiate_proactive_chat(
        self,
        customer_id: int,
        trigger_type: str,
        custom_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate a proactive chat session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Check if we should initiate
                should_initiate = await self.should_initiate_proactive_chat(customer_id, trigger_type)
                if not should_initiate["should_initiate"]:
                    return {
                        "success": False,
                        "error": "Proactive chat initiation not recommended",
                        "details": should_initiate
                    }
                
                # Generate proactive message
                if not custom_message:
                    message = await self._generate_proactive_message(customer_id, trigger_type)
                else:
                    message = custom_message
                
                # Create proactive interaction record
                interaction = ClaraCustomerInteraction(
                    customer_id=customer_id,
                    interaction_type="proactive_outreach",
                    channel=SupportChannel.CHAT,
                    message=message,
                    metadata={
                        "trigger_type": trigger_type,
                        "proactive": True,
                        "custom_message": custom_message is not None,
                        **(metadata or {})
                    }
                )
                session.add(interaction)
                
                # Start chat session
                from ..services.chatbot_service import ClaraChatbotService
                chatbot_service = ClaraChatbotService()
                await chatbot_service.initialize()
                
                chat_result = await chatbot_service.start_chat_session(
                    customer_id=customer_id,
                    channel=SupportChannel.CHAT,
                    initial_message=message,
                    metadata={
                        "proactive": True,
                        "trigger_type": trigger_type,
                        "initiated_by": "system",
                        **(metadata or {})
                    }
                )
                
                if chat_result["success"]:
                    await session.commit()
                    
                    return {
                        "success": True,
                        "chat_session": chat_result["chat_session"],
                        "proactive_message": message,
                        "trigger_type": trigger_type,
                        "interaction_id": interaction.id,
                        "message": "Proactive chat initiated successfully"
                    }
                else:
                    await session.rollback()
                    return chat_result
                
        except Exception as e:
            logger.error(f"Failed to initiate proactive chat: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_proactive_chat_insights(
        self,
        customer_id: int,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get insights about proactive chat effectiveness"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Calculate period
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=period_days)
                
                # Get proactive interactions
                proactive_interactions = await session.execute(
                    select(ClaraCustomerInteraction).where(
                        and_(
                            ClaraCustomerInteraction.customer_id == customer_id,
                            ClaraCustomerInteraction.interaction_type == "proactive_outreach",
                            ClaraCustomerInteraction.created_at >= start_date
                        )
                    ).order_by(ClaraCustomerInteraction.created_at.desc())
                )
                proactive_interactions = proactive_interactions.scalars().all()
                
                # Get resulting chat sessions
                chat_sessions = await session.execute(
                    select(ClaraChatSession).where(
                        and_(
                            ClaraChatSession.customer_id == customer_id,
                            ClaraChatSession.metadata.contains({"proactive": True}),
                            ClaraChatSession.start_time >= start_date
                        )
                    ).order_by(ClaraChatSession.start_time.desc())
                )
                chat_sessions = chat_sessions.scalars().all()
                
                # Analyze effectiveness
                total_proactive = len(proactive_interactions)
                total_chats = len(chat_sessions)
                engagement_rate = (total_chats / max(total_proactive, 1)) * 100
                
                # Calculate response time
                response_times = []
                for interaction in proactive_interactions:
                    # Find corresponding chat session
                    chat_session = next(
                        (chat for chat in chat_sessions 
                         if chat.metadata.get("trigger_type") == interaction.metadata.get("trigger_type")),
                        None
                    )
                    
                    if chat_session:
                        response_time = (chat_session.start_time - interaction.created_at).total_seconds() / 60
                        response_times.append(response_time)
                
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Analyze by trigger type
                trigger_analysis = {}
                for interaction in proactive_interactions:
                    trigger_type = interaction.metadata.get("trigger_type", "unknown")
                    if trigger_type not in trigger_analysis:
                        trigger_analysis[trigger_type] = {
                            "count": 0,
                            "engagements": 0,
                            "avg_response_time": 0
                        }
                    
                    trigger_analysis[trigger_type]["count"] += 1
                    
                    # Check if this led to engagement
                    chat_session = next(
                        (chat for chat in chat_sessions 
                         if chat.metadata.get("trigger_type") == trigger_type),
                        None
                    )
                    
                    if chat_session:
                        trigger_analysis[trigger_type]["engagements"] += 1
                
                # Calculate engagement rates by trigger
                for trigger_type, data in trigger_analysis.items():
                    if data["count"] > 0:
                        data["engagement_rate"] = round((data["engagements"] / data["count"]) * 100, 1)
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "period_days": period_days,
                    "insights": {
                        "total_proactive_interactions": total_proactive,
                        "total_chat_engagements": total_chats,
                        "overall_engagement_rate": round(engagement_rate, 1),
                        "average_response_time_minutes": round(avg_response_time, 1),
                        "trigger_type_analysis": trigger_analysis,
                        "effectiveness_score": self._calculate_effectiveness_score(engagement_rate, avg_response_time)
                    },
                    "recommendations": self._generate_effectiveness_recommendations(engagement_rate, avg_response_time, trigger_analysis)
                }
                
        except Exception as e:
            logger.error(f"Failed to get proactive chat insights: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_engagement_level(
        self,
        tickets: List[ClaraSupportTicket],
        chats: List[ClaraChatSession]
    ) -> str:
        """Calculate customer engagement level"""
        total_interactions = len(tickets) + len(chats)
        
        if total_interactions == 0:
            return "inactive"
        elif total_interactions <= 2:
            return "low"
        elif total_interactions <= 5:
            return "medium"
        elif total_interactions <= 10:
            return "high"
        else:
            return "very_high"
    
    def _get_last_activity(
        self,
        tickets: List[ClaraSupportTicket],
        chats: List[ClaraChatSession]
    ) -> Optional[str]:
        """Get last activity timestamp"""
        all_activities = []
        
        for ticket in tickets:
            all_activities.append(ticket.created_at)
        
        for chat in chats:
            all_activities.append(chat.start_time)
        
        if all_activities:
            latest = max(all_activities)
            return latest.isoformat()
        
        return None
    
    def _analyze_satisfaction_trend(
        self,
        tickets: List[ClaraSupportTicket]
    ) -> Dict[str, Any]:
        """Analyze customer satisfaction trend"""
        satisfaction_scores = [t.sentiment_score for t in tickets if t.sentiment_score is not None]
        
        if not satisfaction_scores:
            return {"trend": "neutral", "average_score": 0.0, "change": 0.0}
        
        avg_score = sum(satisfaction_scores) / len(satisfaction_scores)
        
        # Simple trend calculation (first half vs second half)
        mid_point = len(satisfaction_scores) // 2
        first_half = satisfaction_scores[:mid_point]
        second_half = satisfaction_scores[mid_point:]
        
        if len(first_half) > 0 and len(second_half) > 0:
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            change = second_avg - first_avg
            
            if change > 0.2:
                trend = "improving"
            elif change < -0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
            change = 0.0
        
        return {
            "trend": trend,
            "average_score": round(avg_score, 2),
            "change": round(change, 2)
        }
    
    def _analyze_issue_patterns(
        self,
        tickets: List[ClaraSupportTicket]
    ) -> Dict[str, Any]:
        """Analyze patterns in customer issues"""
        if not tickets:
            return {"patterns": [], "common_issues": []}
        
        # Category distribution
        category_counts = {}
        for ticket in tickets:
            category = ticket.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for ticket in tickets:
            priority = ticket.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Common patterns
        patterns = []
        if len(tickets) >= 3:
            if category_counts.get("technical", 0) >= len(tickets) * 0.5:
                patterns.append("frequent_technical_issues")
            if priority_counts.get("high", 0) + priority_counts.get("critical", 0) >= len(tickets) * 0.3:
                patterns.append("high_priority_issues")
            if len(tickets) >= 5:
                patterns.append("frequent_support_needs")
        
        return {
            "patterns": patterns,
            "category_distribution": category_counts,
            "priority_distribution": priority_counts,
            "total_issues": len(tickets)
        }
    
    def _analyze_channel_preferences(
        self,
        tickets: List[ClaraSupportTicket],
        chats: List[ClaraChatSession]
    ) -> Dict[str, Any]:
        """Analyze customer channel preferences"""
        channel_usage = {}
        
        for ticket in tickets:
            channel = ticket.channel.value
            channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        for chat in chats:
            channel = chat.channel.value
            channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        # Determine preferred channel
        preferred_channel = max(channel_usage.items(), key=lambda x: x[1])[0] if channel_usage else "chat"
        
        return {
            "preferred_channel": preferred_channel,
            "channel_usage": channel_usage,
            "total_interactions": sum(channel_usage.values())
        }
    
    async def _identify_proactive_triggers(
        self,
        customer_id: int,
        profile: CustomerProfile,
        tickets: List[ClaraSupportTicket],
        chats: List[ClaraChatSession],
        behavior_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify proactive engagement triggers"""
        triggers = []
        
        # Trigger 1: Inactive customer
        if behavior_analysis["last_activity"]:
            last_activity = datetime.fromisoformat(behavior_analysis["last_activity"])
            days_inactive = (datetime.utcnow() - last_activity).days
            
            if days_inactive >= 7:
                triggers.append({
                    "type": "inactive_customer",
                    "active": True,
                    "priority": "medium",
                    "description": f"Customer inactive for {days_inactive} days",
                    "recommended_message": "We noticed you haven't been around lately. Is there anything we can help you with?"
                })
        
        # Trigger 2: Low satisfaction trend
        satisfaction_trend = behavior_analysis["satisfaction_trend"]
        if satisfaction_trend["trend"] == "declining" and satisfaction_trend["average_score"] < 0.0:
            triggers.append({
                "type": "declining_satisfaction",
                "active": True,
                "priority": "high",
                "description": "Customer satisfaction is declining",
                "recommended_message": "We want to ensure you're having a great experience. How can we improve our service?"
            })
        
        # Trigger 3: Frequent technical issues
        issue_patterns = behavior_analysis["issue_patterns"]
        if "frequent_technical_issues" in issue_patterns["patterns"]:
            triggers.append({
                "type": "technical_difficulties",
                "active": True,
                "priority": "high",
                "description": "Customer experiencing frequent technical issues",
                "recommended_message": "We see you've had some technical challenges. Let us help you get everything working smoothly!"
            })
        
        # Trigger 4: High priority issues
        if "high_priority_issues" in issue_patterns["patterns"]:
            triggers.append({
                "type": "urgent_support_needs",
                "active": True,
                "priority": "critical",
                "description": "Customer has urgent support needs",
                "recommended_message": "We understand you need immediate assistance. Let's get this resolved right away!"
            })
        
        # Trigger 5: New customer onboarding
        if profile.total_support_tickets <= 2 and profile.loyalty_level == "new":
            triggers.append({
                "type": "new_customer_onboarding",
                "active": True,
                "priority": "medium",
                "description": "New customer who might need onboarding help",
                "recommended_message": "Welcome! We're here to help you get started. Do you have any questions?"
            })
        
        # Trigger 6: Premium customer check-in
        if profile.support_tier == "premium" and behavior_analysis["engagement_level"] == "low":
            triggers.append({
                "type": "premium_customer_engagement",
                "active": True,
                "priority": "medium",
                "description": "Premium customer with low engagement",
                "recommended_message": "As a premium customer, we want to ensure you're getting the most value. How can we help?"
            })
        
        return triggers
    
    def _evaluate_proactive_decision(self, behavior_analysis: Dict[str, Any]) -> bool:
        """Evaluate whether to initiate proactive chat based on behavior analysis"""
        # Check if any high-priority triggers are active
        high_priority_triggers = [
            trigger for trigger in behavior_analysis["proactive_triggers"]
            if trigger["priority"] in ["high", "critical"] and trigger["active"]
        ]
        
        if high_priority_triggers:
            return True
        
        # Check engagement level
        if behavior_analysis["engagement_level"] == "inactive":
            return True
        
        # Check satisfaction trend
        if behavior_analysis["satisfaction_trend"]["trend"] == "declining":
            return True
        
        # Check if customer has been inactive for a while
        if behavior_analysis["last_activity"]:
            last_activity = datetime.fromisoformat(behavior_analysis["last_activity"])
            days_inactive = (datetime.utcnow() - last_activity).days
            if days_inactive >= 14:  # 2 weeks
                return True
        
        return False
    
    def _calculate_confidence_score(self, behavior_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for proactive engagement decision"""
        score = 0.5  # Base score
        
        # Add points for active triggers
        active_triggers = [t for t in behavior_analysis["proactive_triggers"] if t["active"]]
        score += min(len(active_triggers) * 0.1, 0.3)
        
        # Add points for high-priority triggers
        high_priority_count = len([t for t in active_triggers if t["priority"] in ["high", "critical"]])
        score += min(high_priority_count * 0.15, 0.3)
        
        # Add points for engagement level
        engagement_scores = {"inactive": 0.2, "low": 0.1, "medium": 0.05, "high": 0.0, "very_high": 0.0}
        score += engagement_scores.get(behavior_analysis["engagement_level"], 0.0)
        
        # Add points for satisfaction trend
        if behavior_analysis["satisfaction_trend"]["trend"] == "declining":
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_recommended_approach(self, behavior_analysis: Dict[str, Any]) -> str:
        """Get recommended approach for proactive engagement"""
        active_triggers = [t for t in behavior_analysis["proactive_triggers"] if t["active"]]
        
        if not active_triggers:
            return "gentle_check_in"
        
        # Check for urgent triggers
        urgent_triggers = [t for t in active_triggers if t["priority"] == "critical"]
        if urgent_triggers:
            return "immediate_assistance"
        
        # Check for high priority triggers
        high_priority_triggers = [t for t in active_triggers if t["priority"] == "high"]
        if high_priority_triggers:
            return "proactive_support"
        
        # Check engagement level
        if behavior_analysis["engagement_level"] == "inactive":
            return "re_engagement"
        
        return "gentle_check_in"
    
    async def _generate_proactive_message(
        self,
        customer_id: int,
        trigger_type: str
    ) -> str:
        """Generate proactive chat message based on trigger type"""
        try:
            message_prompt = f"""Generate a friendly, proactive chat message for a customer. The message should:

Trigger Type: {trigger_type}

Requirements:
- Be warm and welcoming
- Not be pushy or salesy
- Offer genuine help
- Be personalized and relevant
- Keep it under 100 characters
- Start with a greeting

Generate the message:"""
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI customer support assistant that generates proactive messages."},
                {"role": "user", "content": message_prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
            if ai_response.success:
                return ai_response.text_content.strip()
            else:
                # Fallback messages
                fallback_messages = {
                    "inactive_customer": "Hi there! 👋 We noticed you haven't been around lately. Is there anything we can help you with?",
                    "declining_satisfaction": "Hello! 😊 We want to ensure you're having a great experience. How can we improve our service?",
                    "technical_difficulties": "Hi! 🛠️ We see you've had some technical challenges. Let us help you get everything working smoothly!",
                    "urgent_support_needs": "Hello! 🚨 We understand you need immediate assistance. Let's get this resolved right away!",
                    "new_customer_onboarding": "Welcome! 🎉 We're here to help you get started. Do you have any questions?",
                    "premium_customer_engagement": "Hi there! ⭐ As a premium customer, we want to ensure you're getting the most value. How can we help?"
                }
                
                return fallback_messages.get(trigger_type, "Hi! 👋 Is there anything we can help you with today?")
                
        except Exception as e:
            logger.error(f"Failed to generate proactive message: {e}")
            return "Hi! 👋 Is there anything we can help you with today?"
    
    def _calculate_effectiveness_score(self, engagement_rate: float, avg_response_time: float) -> float:
        """Calculate effectiveness score for proactive chat"""
        # Engagement rate component (0-50 points)
        engagement_score = min(engagement_rate / 100 * 50, 50)
        
        # Response time component (0-50 points)
        # Lower response time is better
        if avg_response_time <= 5:  # 5 minutes or less
            response_score = 50
        elif avg_response_time <= 15:  # 15 minutes or less
            response_score = 40
        elif avg_response_time <= 30:  # 30 minutes or less
            response_score = 30
        elif avg_response_time <= 60:  # 1 hour or less
            response_score = 20
        else:
            response_score = 10
        
        return round(engagement_score + response_score, 1)
    
    def _generate_effectiveness_recommendations(
        self,
        engagement_rate: float,
        avg_response_time: float,
        trigger_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving proactive chat effectiveness"""
        recommendations = []
        
        if engagement_rate < 30:
            recommendations.append("Consider adjusting proactive message timing and frequency")
            recommendations.append("Review and improve proactive message content")
            recommendations.append("Analyze customer segments for better targeting")
        
        if avg_response_time > 30:
            recommendations.append("Optimize proactive chat response time")
            recommendations.append("Consider automated initial responses")
            recommendations.append("Review agent availability and workload")
        
        # Analyze trigger effectiveness
        for trigger_type, data in trigger_analysis.items():
            if data.get("engagement_rate", 0) < 20:
                recommendations.append(f"Review effectiveness of '{trigger_type}' trigger type")
        
        if not recommendations:
            recommendations.append("Proactive chat is performing well - continue current approach")
        
        return recommendations
    
    def _generate_behavior_recommendations(self, behavior_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on behavior analysis"""
        recommendations = []
        
        engagement_level = behavior_analysis["engagement_level"]
        if engagement_level == "inactive":
            recommendations.append("Customer shows no recent activity - consider re-engagement campaign")
        elif engagement_level == "low":
            recommendations.append("Customer has low engagement - offer personalized support")
        
        satisfaction_trend = behavior_analysis["satisfaction_trend"]
        if satisfaction_trend["trend"] == "declining":
            recommendations.append("Customer satisfaction is declining - investigate and address issues")
        
        issue_patterns = behavior_analysis["issue_patterns"]
        if "frequent_technical_issues" in issue_patterns["patterns"]:
            recommendations.append("Customer has frequent technical issues - provide proactive technical support")
        
        if "high_priority_issues" in issue_patterns["patterns"]:
            recommendations.append("Customer has urgent support needs - prioritize and expedite resolution")
        
        return recommendations
