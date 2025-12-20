from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from core.ai import get_ai_service_manager, AIServiceManager
from core.database.connection import get_supabase
from ..models import ScheduledPost, EngagementEvent
import json


class EngagementBoosterService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()

    async def generate_engagement_prompts(self, user_id: int, post_content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Generate engagement-boosting prompts for a post"""
        if not self.ai_service_manager:
            await self.initialize()

        caption = post_content.get("caption", "")
        media_type = post_content.get("media_type", "text")
        topic = post_content.get("topic", "")
        
        # Generate different types of engagement prompts
        poll_suggestions = await self._generate_poll_suggestions(caption, topic, platform)
        question_suggestions = await self._generate_question_suggestions(caption, topic, platform)
        cta_suggestions = await self._generate_cta_suggestions(caption, topic, platform)
        interactive_suggestions = await self._generate_interactive_suggestions(caption, topic, platform, media_type)
        
        # Calculate engagement potential score
        engagement_score = self._calculate_engagement_potential(
            poll_suggestions, question_suggestions, cta_suggestions, interactive_suggestions
        )

        return {
            "success": True,
            "engagement_score": engagement_score,
            "poll_suggestions": poll_suggestions,
            "question_suggestions": question_suggestions,
            "cta_suggestions": cta_suggestions,
            "interactive_suggestions": interactive_suggestions,
            "platform": platform,
            "total_suggestions": len(poll_suggestions) + len(question_suggestions) + len(cta_suggestions) + len(interactive_suggestions)
        }

    async def _generate_poll_suggestions(self, caption: str, topic: str, platform: str) -> List[Dict[str, Any]]:
        """Generate poll suggestions for the post"""
        if not caption and not topic:
            return []

        prompt = f"""
        Generate 3 engaging poll questions for this {platform} post:
        
        Post content: "{caption}"
        Topic: {topic if topic else 'general'}
        
        Requirements:
        - Make polls relevant to the content
        - Include 2-4 answer options
        - Make them fun and engaging
        - Encourage audience participation
        - Keep questions under 100 characters
        
        Return as JSON array with format:
        [
            {{
                "question": "Poll question?",
                "options": ["Option 1", "Option 2", "Option 3"],
                "engagement_type": "poll",
                "estimated_engagement": "high/medium/low"
            }}
        ]
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "poll generation"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            polls = json.loads(response.text_content) if response.success else []
            if isinstance(polls, list):
                return polls[:3]  # Limit to 3 suggestions
        except:
            pass
        
        # Fallback suggestions
        return [
            {
                "question": "What's your favorite part of this post?",
                "options": ["The content", "The visuals", "The message"],
                "engagement_type": "poll",
                "estimated_engagement": "high"
            }
        ]

    async def _generate_question_suggestions(self, caption: str, topic: str, platform: str) -> List[Dict[str, Any]]:
        """Generate engaging question suggestions"""
        if not caption and not topic:
            return []

        prompt = f"""
        Generate 3 engaging questions to ask your audience on {platform}:
        
        Post content: "{caption}"
        Topic: {topic if topic else 'general'}
        
        Requirements:
        - Questions that encourage comments
        - Make them personal and relatable
        - Encourage sharing experiences
        - Keep questions under 120 characters
        - Make them relevant to the post content
        
        Return as JSON array with format:
        [
            {{
                "question": "What's your experience with this?",
                "engagement_type": "question",
                "estimated_engagement": "high/medium/low",
                "response_prompt": "Share your thoughts below!"
            }}
        ]
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "question generation"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            questions = json.loads(response.text_content) if response.success else []
            if isinstance(questions, list):
                return questions[:3]
        except:
            pass
        
        # Fallback suggestions
        return [
            {
                "question": "What's your take on this?",
                "engagement_type": "question",
                "estimated_engagement": "high",
                "response_prompt": "Share your thoughts below!"
            }
        ]

    async def _generate_cta_suggestions(self, caption: str, topic: str, platform: str) -> List[Dict[str, Any]]:
        """Generate call-to-action suggestions"""
        if not caption and not topic:
            return []

        prompt = f"""
        Generate 3 effective call-to-action (CTA) suggestions for this {platform} post:
        
        Post content: "{caption}"
        Topic: {topic if topic else 'general'}
        
        Requirements:
        - Clear and actionable
        - Encourage specific actions
        - Make them relevant to the content
        - Keep CTAs under 80 characters
        - Vary the types (comment, share, save, etc.)
        
        Return as JSON array with format:
        [
            {{
                "cta_text": "Share this with someone who needs to see it!",
                "action_type": "share",
                "engagement_type": "cta",
                "estimated_engagement": "high/medium/low"
            }}
        ]
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "CTA generation"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            ctas = json.loads(response.text_content) if response.success else []
            if isinstance(ctas, list):
                return ctas[:3]
        except:
            pass
        
        # Fallback suggestions
        return [
            {
                "cta_text": "Double tap if you agree!",
                "action_type": "like",
                "engagement_type": "cta",
                "estimated_engagement": "high"
            }
        ]

    async def _generate_interactive_suggestions(self, caption: str, topic: str, platform: str, media_type: str) -> List[Dict[str, Any]]:
        """Generate interactive element suggestions"""
        if not caption and not topic:
            return []

        prompt = f"""
        Generate 3 interactive element suggestions for this {platform} post:
        
        Post content: "{caption}"
        Topic: {topic if topic else 'general'}
        Media type: {media_type}
        
        Requirements:
        - Make them relevant to the content and media
        - Encourage audience interaction
        - Consider platform limitations
        - Keep suggestions practical and engaging
        - Vary the types of interactions
        
        Return as JSON array with format:
        [
            {{
                "suggestion": "Ask followers to tag someone who needs to see this",
                "interaction_type": "tagging",
                "engagement_type": "interactive",
                "estimated_engagement": "high/medium/low",
                "implementation": "Add to caption: 'Tag someone who needs to see this!'"
            }}
        ]
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "interactive suggestions"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            suggestions = json.loads(response.text_content) if response.success else []
            if isinstance(suggestions, list):
                return suggestions[:3]
        except:
            pass
        
        # Fallback suggestions
        return [
            {
                "suggestion": "Ask followers to tag someone who needs to see this",
                "interaction_type": "tagging",
                "engagement_type": "interactive",
                "estimated_engagement": "high",
                "implementation": "Add to caption: 'Tag someone who needs to see this!'"
            }
        ]

    def _calculate_engagement_potential(self, polls: List[Dict], questions: List[Dict], ctas: List[Dict], interactive: List[Dict]) -> int:
        """Calculate overall engagement potential score (0-100)"""
        score = 0
        
        # Poll engagement (polls typically get high engagement)
        for poll in polls:
            if poll.get("estimated_engagement") == "high":
                score += 25
            elif poll.get("estimated_engagement") == "medium":
                score += 15
            else:
                score += 10
        
        # Question engagement
        for question in questions:
            if question.get("estimated_engagement") == "high":
                score += 20
            elif question.get("estimated_engagement") == "medium":
                score += 12
            else:
                score += 8
        
        # CTA engagement
        for cta in ctas:
            if cta.get("estimated_engagement") == "high":
                score += 15
            elif cta.get("estimated_engagement") == "medium":
                score += 10
            else:
                score += 5
        
        # Interactive engagement
        for suggestion in interactive:
            if suggestion.get("estimated_engagement") == "high":
                score += 20
            elif suggestion.get("estimated_engagement") == "medium":
                score += 12
            else:
                score += 8
        
        # Bonus for variety
        if len(set([p.get("engagement_type") for p in polls + questions + ctas + interactive])) >= 3:
            score += 10
        
        return min(score, 100)  # Cap at 100

    async def apply_engagement_boost(self, user_id: int, post_id: int, boost_type: str, boost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply engagement boost to a scheduled post"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import ScheduledPost
            
            # Get the post
            query = select(ScheduledPost).where(ScheduledPost.id == post_id, ScheduledPost.user_id == user_id)
            result = await session.execute(query)
            post = result.scalar_one_or_none()
            
            if not post:
                return {"success": False, "error": "Post not found"}

            # Apply the engagement boost
            if boost_type == "poll":
                enhanced_caption = await self._add_poll_to_caption(post.caption, boost_data)
            elif boost_type == "question":
                enhanced_caption = await self._add_question_to_caption(post.caption, boost_data)
            elif boost_type == "cta":
                enhanced_caption = await self._add_cta_to_caption(post.caption, boost_data)
            elif boost_type == "interactive":
                enhanced_caption = await self._add_interactive_to_caption(post.caption, boost_data)
            else:
                return {"success": False, "error": "Invalid boost type"}

            # Update the post
            post.caption = enhanced_caption
            post.updated_at = datetime.utcnow()
            
            # Store engagement boost metadata
            if not hasattr(post, 'engagement_boosts'):
                post.engagement_boosts = []
            
            post.engagement_boosts.append({
                "type": boost_type,
                "data": boost_data,
                "applied_at": datetime.utcnow().isoformat()
            })
            
            await session.commit()
            
            return {
                "success": True,
                "post_id": post_id,
                "enhanced_caption": enhanced_caption,
                "boost_type": boost_type,
                "message": f"Engagement boost applied successfully"
            }

    async def _add_poll_to_caption(self, caption: str, poll_data: Dict[str, Any]) -> str:
        """Add poll to caption"""
        if not caption:
            caption = ""
        
        poll_text = f"\n\n📊 {poll_data.get('question', '')}\n"
        options = poll_data.get('options', [])
        
        for i, option in enumerate(options):
            poll_text += f"{chr(65 + i)}. {option}\n"
        
        poll_text += "\nVote in the comments! 👇"
        
        return caption + poll_text

    async def _add_question_to_caption(self, caption: str, question_data: Dict[str, Any]) -> str:
        """Add question to caption"""
        if not caption:
            caption = ""
        
        question_text = f"\n\n❓ {question_data.get('question', '')}\n"
        question_text += f"{question_data.get('response_prompt', 'Share your thoughts below!')}"
        
        return caption + question_text

    async def _add_cta_to_caption(self, caption: str, cta_data: Dict[str, Any]) -> str:
        """Add CTA to caption"""
        if not caption:
            caption = ""
        
        cta_text = f"\n\n{cta_data.get('cta_text', '')}"
        
        return caption + cta_text

    async def _add_interactive_to_caption(self, caption: str, interactive_data: Dict[str, Any]) -> str:
        """Add interactive element to caption"""
        if not caption:
            caption = ""
        
        interactive_text = f"\n\n{interactive_data.get('implementation', '')}"
        
        return caption + interactive_text

    async def get_engagement_analytics(self, user_id: int, post_id: int) -> Dict[str, Any]:
        """Get engagement analytics for a post"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, func
            from ..models import EngagementEvent
            
            # Get engagement events for the post
            query = select(EngagementEvent).where(
                EngagementEvent.user_id == user_id,
                EngagementEvent.post_ref == str(post_id)
            )
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            # Analyze engagement patterns
            engagement_types = {}
            total_engagement = 0
            
            for event in events:
                event_type = event.event_type
                if event_type not in engagement_types:
                    engagement_types[event_type] = 0
                engagement_types[event_type] += 1
                total_engagement += 1
            
            # Calculate engagement rate
            engagement_rate = (total_engagement / max(1, len(events))) * 100 if events else 0
            
            return {
                "success": True,
                "post_id": post_id,
                "total_engagement": total_engagement,
                "engagement_rate": round(engagement_rate, 2),
                "engagement_types": engagement_types,
                "events_count": len(events),
                "last_engagement": events[-1].occurred_at.isoformat() if events else None
            }

    async def get_engagement_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get engagement trends over time"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, func, desc
            from ..models import EngagementEvent
            
            # Get engagement events for the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(EngagementEvent).where(
                EngagementEvent.user_id == user_id,
                EngagementEvent.occurred_at >= cutoff_date
            ).order_by(desc(EngagementEvent.occurred_at))
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            # Group by date
            daily_engagement = {}
            for event in events:
                date_key = event.occurred_at.date().isoformat()
                if date_key not in daily_engagement:
                    daily_engagement[date_key] = 0
                daily_engagement[date_key] += 1
            
            # Calculate trends
            dates = sorted(daily_engagement.keys())
            engagement_counts = [daily_engagement[date] for date in dates]
            
            # Simple trend calculation
            if len(engagement_counts) >= 2:
                trend = "increasing" if engagement_counts[-1] > engagement_counts[0] else "decreasing"
                trend_percentage = ((engagement_counts[-1] - engagement_counts[0]) / max(1, engagement_counts[0])) * 100
            else:
                trend = "stable"
                trend_percentage = 0
            
            return {
                "success": True,
                "period_days": days,
                "total_engagement": sum(engagement_counts),
                "average_daily_engagement": round(sum(engagement_counts) / max(1, len(dates)), 2),
                "trend": trend,
                "trend_percentage": round(trend_percentage, 2),
                "daily_breakdown": daily_engagement,
                "dates": dates,
                "engagement_counts": engagement_counts
            }
