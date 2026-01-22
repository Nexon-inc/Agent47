from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import math
from statistics import mean, median
from core.ai import get_ai_service_manager, AIServiceManager
from core.database.connection import get_supabase
from core.integrations.integration_manager import get_integration_manager
from ..models import AriaAnalyticsSnapshot, AriaEngagementEvent, AriaTrendSignal
from core.config import settings


class AdvancedAnalyticsService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()
        self.integration_manager = await get_integration_manager()

    async def generate_sentiment_heatmap(self, user_id: int, platform: str, date_range: str = "30d") -> Dict[str, Any]:
        """Generate audience sentiment heatmap visualization data"""
        if not self.ai_service_manager:
            await self.initialize()

        # Calculate date range
        end_date = datetime.utcnow()
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        elif date_range == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)

        # Get engagement data for sentiment analysis
        engagement_data = await self._get_engagement_data(user_id, platform, start_date, end_date)
        
        # Analyze sentiment patterns
        sentiment_heatmap = await self._analyze_sentiment_patterns(engagement_data, platform)
        
        # Generate time-based sentiment trends
        time_sentiment = await self._generate_time_sentiment_data(engagement_data, start_date, end_date)
        
        # Create heatmap visualization data
        heatmap_data = self._create_heatmap_visualization(sentiment_heatmap, time_sentiment)
        
        return {
            "success": True,
            "platform": platform,
            "date_range": date_range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "heatmap_data": heatmap_data,
            "sentiment_summary": {
                "total_engagements": len(engagement_data),
                "positive_sentiment": sentiment_heatmap.get("positive", 0),
                "neutral_sentiment": sentiment_heatmap.get("neutral", 0),
                "negative_sentiment": sentiment_heatmap.get("negative", 0),
                "overall_sentiment_score": sentiment_heatmap.get("overall_score", 0.0)
            }
        }

    async def _get_engagement_data(self, user_id: int, platform: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get engagement data for sentiment analysis"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, and_
            from ..models import AriaEngagementEvent
            
            query = select(AriaEngagementEvent).where(
                and_(
                    AriaEngagementEvent.user_id == user_id,
                    AriaEngagementEvent.platform == platform,
                    AriaEngagementEvent.occurred_at >= start_date,
                    AriaEngagementEvent.occurred_at <= end_date
                )
            )
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            engagement_data = []
            for event in events:
                engagement_data.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "text": event.text,
                    "sentiment": event.sentiment,
                    "occurred_at": event.occurred_at,
                    "metadata": event.metadata
                })
            
            return engagement_data

    async def _analyze_sentiment_patterns(self, engagement_data: List[Dict[str, Any]], platform: str) -> Dict[str, Any]:
        """Analyze sentiment patterns in engagement data"""
        if not engagement_data:
            return {"positive": 0, "neutral": 0, "negative": 0, "overall_score": 0.0}

        # Use existing sentiment data if available
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        sentiment_scores = []
        
        for engagement in engagement_data:
            sentiment = engagement.get("sentiment", "neutral")
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            
            # Convert sentiment to numeric score for analysis
            if sentiment == "positive":
                sentiment_scores.append(1.0)
            elif sentiment == "neutral":
                sentiment_scores.append(0.0)
            elif sentiment == "negative":
                sentiment_scores.append(-1.0)

        # Calculate overall sentiment score
        overall_score = mean(sentiment_scores) if sentiment_scores else 0.0
        
        # Analyze text sentiment for entries without sentiment data
        text_entries = [e for e in engagement_data if e.get("text") and not e.get("sentiment")]
        if text_entries and self.nlp:
            for entry in text_entries[:10]:  # Limit to 10 for performance
                try:
                    sentiment_result = await self._analyze_text_sentiment(entry["text"])
                    if sentiment_result:
                        sentiment_counts[sentiment_result] += 1
                        if sentiment_result == "positive":
                            sentiment_scores.append(1.0)
                        elif sentiment_result == "negative":
                            sentiment_scores.append(-1.0)
                        else:
                            sentiment_scores.append(0.0)
                except Exception:
                    pass

        # Recalculate overall score
        overall_score = mean(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            "positive": sentiment_counts["positive"],
            "neutral": sentiment_counts["neutral"],
            "negative": sentiment_counts["negative"],
            "overall_score": round(overall_score, 3)
        }

    async def _analyze_text_sentiment(self, text: str) -> Optional[str]:
        """Analyze text sentiment using AI"""
        if not text or len(text) < 3:
            return None

        prompt = f"""
        Analyze the sentiment of this text and return only one word: positive, neutral, or negative.
        
        Text: "{text}"
        
        Consider the tone, emotion, and context. Return only the sentiment word.
        """

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=10,
                temperature=0.1
            )
            
            if response.success:
                sentiment = response.text_content.strip().lower()
                if sentiment in ["positive", "neutral", "negative"]:
                    return sentiment
            return "neutral"
        except Exception:
            return "neutral"

    async def _generate_time_sentiment_data(self, engagement_data: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate time-based sentiment data for heatmap"""
        if not engagement_data:
            return []

        # Group by day
        daily_sentiment = {}
        current_date = start_date
        
        while current_date <= end_date:
            date_key = current_date.date().isoformat()
            daily_sentiment[date_key] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
            current_date += timedelta(days=1)

        # Populate daily sentiment
        for engagement in engagement_data:
            date_key = engagement["occurred_at"].date().isoformat()
            if date_key in daily_sentiment:
                sentiment = engagement.get("sentiment", "neutral")
                if sentiment in daily_sentiment[date_key]:
                    daily_sentiment[date_key][sentiment] += 1
                daily_sentiment[date_key]["total"] += 1

        # Convert to list format for visualization
        time_data = []
        for date, data in daily_sentiment.items():
            if data["total"] > 0:
                time_data.append({
                    "date": date,
                    "positive": data["positive"],
                    "neutral": data["neutral"],
                    "negative": data["negative"],
                    "total": data["total"],
                    "dominant_sentiment": max(data, key=lambda k: data[k] if k != "total" else 0)
                })

        return time_data

    def _create_heatmap_visualization(self, sentiment_data: Dict[str, Any], time_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create heatmap visualization data structure"""
        # Create color intensity mapping
        max_count = max(sentiment_data.values()) if sentiment_data else 1
        
        heatmap_data = {
            "sentiment_distribution": {
                "positive": {
                    "count": sentiment_data.get("positive", 0),
                    "percentage": round((sentiment_data.get("positive", 0) / max(1, sum(sentiment_data.values()))) * 100, 1),
                    "intensity": min(1.0, sentiment_data.get("positive", 0) / max(1, max_count))
                },
                "neutral": {
                    "count": sentiment_data.get("neutral", 0),
                    "percentage": round((sentiment_data.get("neutral", 0) / max(1, sum(sentiment_data.values()))) * 100, 1),
                    "intensity": min(1.0, sentiment_data.get("neutral", 0) / max(1, max_count))
                },
                "negative": {
                    "count": sentiment_data.get("negative", 0),
                    "percentage": round((sentiment_data.get("negative", 0) / max(1, sum(sentiment_data.values()))) * 100, 1),
                    "intensity": min(1.0, sentiment_data.get("negative", 0) / max(1, max_count))
                }
            },
            "time_series": time_data,
            "color_scheme": {
                "positive": "#4CAF50",  # Green
                "neutral": "#FFC107",   # Yellow
                "negative": "#F44336"   # Red
            }
        }
        
        return heatmap_data

    async def cross_platform_story_sync(self, user_id: int, story_content: Dict[str, Any], target_platforms: List[str]) -> Dict[str, Any]:
        """Sync Stories/Reels across multiple platforms with platform-specific adaptations"""
        if not self.ai_service_manager:
            await self.initialize()

        synced_stories = {}
        
        for platform in target_platforms:
            adapted_story = await self._adapt_story_for_platform(story_content, platform)
            if adapted_story:
                synced_stories[platform] = adapted_story

        # Create cross-platform story campaign
        campaign_id = await self._create_story_campaign(user_id, synced_stories)
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "synced_stories": synced_stories,
            "platforms_synced": list(synced_stories.keys()),
            "total_stories": len(synced_stories)
        }

    async def _adapt_story_for_platform(self, story_content: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        """Adapt story content for specific platform requirements"""
        platform_specs = self._get_platform_story_specs(platform)
        if not platform_specs:
            return None

        # Adapt text content
        adapted_text = await self._adapt_story_text(
            story_content.get("text", ""),
            platform_specs["text_limit"],
            platform_specs["tone"]
        )

        # Adapt media specifications
        adapted_media = self._adapt_story_media(
            story_content.get("media", {}),
            platform_specs["media_specs"]
        )

        # Adapt hashtags
        adapted_hashtags = await self._adapt_story_hashtags(
            story_content.get("hashtags", []),
            platform_specs["hashtag_limit"]
        )

        return {
            "platform": platform,
            "text": adapted_text,
            "media": adapted_media,
            "hashtags": adapted_hashtags,
            "specs": platform_specs,
            "adapted_at": datetime.utcnow().isoformat()
        }

    def _get_platform_story_specs(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get platform-specific story specifications"""
        specs = {
            "instagram": {
                "text_limit": 2200,
                "tone": "visual, engaging, trendy",
                "hashtag_limit": 30,
                "media_specs": {
                    "aspect_ratio": "9:16",
                    "resolution": "1080x1920",
                    "duration": "15s",
                    "format": "mp4"
                }
            },
            "tiktok": {
                "text_limit": 150,
                "tone": "trendy, youthful, viral",
                "hashtag_limit": 20,
                "media_specs": {
                    "aspect_ratio": "9:16",
                    "resolution": "1080x1920",
                    "duration": "15s-60s",
                    "format": "mp4"
                }
            },
            "snapchat": {
                "text_limit": 250,
                "tone": "casual, fun, ephemeral",
                "hashtag_limit": 10,
                "media_specs": {
                    "aspect_ratio": "9:16",
                    "resolution": "1080x1920",
                    "duration": "10s",
                    "format": "mp4"
                }
            },
            "youtube_shorts": {
                "text_limit": 100,
                "tone": "informative, engaging, searchable",
                "hashtag_limit": 15,
                "media_specs": {
                    "aspect_ratio": "9:16",
                    "resolution": "1080x1920",
                    "duration": "15s-60s",
                    "format": "mp4"
                }
            }
        }
        
        return specs.get(platform)

    async def _adapt_story_text(self, text: str, limit: int, tone: str) -> str:
        """Adapt story text for platform and tone"""
        if not text:
            return ""

        prompt = f"""
        Adapt this story text for {tone} tone and {limit} character limit:
        
        Original text: "{text}"
        
        Requirements:
        - Tone: {tone}
        - Max characters: {limit}
        - Keep the core message
        - Make it engaging for the platform
        - Use appropriate emojis if needed
        
        Return only the adapted text.
        """

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            adapted = response.text_content if response.success else text
            
            # Ensure character limit
            if len(adapted) > limit:
                adapted = adapted[:limit-3] + "..."
            
            return adapted
        except Exception:
            return text[:limit] if len(text) > limit else text

    def _adapt_story_media(self, media: Dict[str, Any], specs: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt media specifications for platform"""
        adapted_media = media.copy()
        
        # Update specifications
        adapted_media["target_aspect_ratio"] = specs.get("aspect_ratio", "9:16")
        adapted_media["target_resolution"] = specs.get("resolution", "1080x1920")
        adapted_media["target_duration"] = specs.get("duration", "15s")
        adapted_media["target_format"] = specs.get("format", "mp4")
        
        return adapted_media

    async def _adapt_story_hashtags(self, hashtags: List[str], limit: int) -> List[str]:
        """Adapt hashtags for platform limit"""
        if not hashtags:
            return []
        
        if len(hashtags) <= limit:
            return hashtags
        
        # Use AI to select the most relevant hashtags
        prompt = f"""
        Select the top {limit} most relevant hashtags from this list:
        
        Hashtags: {', '.join(hashtags)}
        
        Return only a JSON array of selected hashtags.
        """

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "hashtag selection"}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=100,
                temperature=0.3
            )
            
            if response.success:
                selected = json.loads(response.text_content)
                return selected[:limit] if isinstance(selected, list) else hashtags[:limit]
            return hashtags[:limit]
        except Exception:
            return hashtags[:limit]

    async def _create_story_campaign(self, user_id: int, synced_stories: Dict[str, Any]) -> int:
        """Create a cross-platform story campaign"""
        db = await get_supabase()
        async with db.get_session() as session:
            from ..models import AriaCampaign
            
            campaign = AriaCampaign(
                user_id=user_id,
                name=f"Cross-Platform Story AriaCampaign {datetime.utcnow().strftime('%Y-%m-%d')}",
                objective="engagement",
                budget_cents=0,  # Stories are typically free
                status="active",
                metrics={
                    "type": "cross_platform_story",
                    "platforms": list(synced_stories.keys()),
                    "stories": synced_stories,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            session.add(campaign)
            await session.commit()
            
            return campaign.id

    async def find_influencer_collaborations(self, user_id: int, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Find potential influencer collaboration opportunities"""
        if not self.ai_service_manager:
            await self.initialize()

        # Get trend signals for influencer discovery
        trend_signals = await self._get_relevant_trends(user_id, criteria.get("topics", []))
        
        # Analyze potential influencers
        influencer_opportunities = await self._analyze_influencer_opportunities(trend_signals, criteria)
        
        # Generate collaboration suggestions
        collaboration_suggestions = await self._generate_collaboration_suggestions(influencer_opportunities, criteria)
        
        return {
            "success": True,
            "criteria": criteria,
            "trend_signals": len(trend_signals),
            "influencer_opportunities": influencer_opportunities,
            "collaboration_suggestions": collaboration_suggestions,
            "total_opportunities": len(influencer_opportunities)
        }

    async def _get_relevant_trends(self, user_id: int, topics: List[str]) -> List[Dict[str, Any]]:
        """Get relevant trend signals for influencer discovery"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, or_
            from ..models import AriaTrendSignal
            
            if not topics:
                # Get all recent trends
                query = select(AriaTrendSignal).where(
                    AriaTrendSignal.user_id == user_id
                ).order_by(AriaTrendSignal.captured_at.desc()).limit(50)
            else:
                # Get trends matching specific topics
                conditions = [AriaTrendSignal.topic.ilike(f"%{topic}%") for topic in topics]
                query = select(AriaTrendSignal).where(
                    AriaTrendSignal.user_id == user_id,
                    or_(*conditions)
                ).order_by(AriaTrendSignal.captured_at.desc()).limit(50)
            
            result = await session.execute(query)
            signals = result.scalars().all()
            
            return [
                {
                    "id": signal.id,
                    "topic": signal.topic,
                    "keywords": signal.keywords,
                    "source": signal.source,
                    "score": signal.score,
                    "captured_at": signal.captured_at.isoformat() if signal.captured_at else None
                }
                for signal in signals
            ]

    async def _analyze_influencer_opportunities(self, trend_signals: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze trend signals for influencer collaboration opportunities"""
        opportunities = []
        
        for signal in trend_signals:
            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(signal, criteria)
            
            if opportunity_score > criteria.get("min_score", 0.5):
                opportunity = {
                    "trend_topic": signal["topic"],
                    "keywords": signal["keywords"],
                    "source": signal["source"],
                    "opportunity_score": opportunity_score,
                    "collaboration_type": self._suggest_collaboration_type(signal, criteria),
                    "estimated_reach": self._estimate_potential_reach(signal, criteria),
                    "timing": self._suggest_timing(signal)
                }
                opportunities.append(opportunity)
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        return opportunities[:criteria.get("max_opportunities", 10)]

    def _calculate_opportunity_score(self, signal: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate collaboration opportunity score (0-1)"""
        score = 0.0
        
        # Trend relevance score
        score += min(1.0, signal["score"] / 100.0) * 0.4
        
        # Topic alignment score
        if criteria.get("topics"):
            topic_match = any(topic.lower() in signal["topic"].lower() for topic in criteria["topics"])
            score += 0.3 if topic_match else 0.0
        
        # Freshness score (newer trends get higher scores)
        if signal.get("captured_at"):
            days_old = (datetime.utcnow() - datetime.fromisoformat(signal["captured_at"])).days
            freshness_score = max(0.0, 1.0 - (days_old / 30.0))  # 30 days max
            score += freshness_score * 0.3
        
        return min(1.0, score)

    def _suggest_collaboration_type(self, signal: Dict[str, Any], criteria: Dict[str, Any]) -> str:
        """Suggest collaboration type based on trend and criteria"""
        collaboration_types = [
            "guest_post",
            "cross_promotion",
            "joint_live_stream",
            "content_swap",
            "hashtag_challenge",
            "product_review",
            "behind_scenes",
            "exclusive_interview"
        ]
        
        # Simple logic based on trend source and score
        if signal["source"] == "instagram":
            return "guest_post"
        elif signal["source"] == "tiktok":
            return "hashtag_challenge"
        elif signal["score"] > 0.8:
            return "joint_live_stream"
        else:
            return "cross_promotion"

    def _estimate_potential_reach(self, signal: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate potential reach for collaboration"""
        base_reach = criteria.get("current_followers", 1000)
        trend_multiplier = 1.0 + (signal["score"] / 100.0)
        
        estimated_reach = {
            "minimum": int(base_reach * trend_multiplier * 0.5),
            "expected": int(base_reach * trend_multiplier),
            "maximum": int(base_reach * trend_multiplier * 2.0),
            "confidence": "medium" if signal["score"] > 0.5 else "low"
        }
        
        return estimated_reach

    def _suggest_timing(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal timing for collaboration"""
        # Simple timing logic based on trend freshness
        if signal.get("captured_at"):
            days_old = (datetime.utcnow() - datetime.fromisoformat(signal["captured_at"])).days
            
            if days_old <= 3:
                urgency = "high"
                recommended_timing = "within 48 hours"
            elif days_old <= 7:
                urgency = "medium"
                recommended_timing = "within 1 week"
            else:
                urgency = "low"
                recommended_timing = "within 2 weeks"
        else:
            urgency = "medium"
            recommended_timing = "within 1 week"
        
        return {
            "urgency": urgency,
            "recommended_timing": recommended_timing,
            "trend_age_days": signal.get("captured_at") and (datetime.utcnow() - datetime.fromisoformat(signal["captured_at"])).days or 0
        }

    async def _generate_collaboration_suggestions(self, opportunities: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific collaboration suggestions"""
        suggestions = []
        
        for opportunity in opportunities:
            suggestion = await self._create_collaboration_suggestion(opportunity, criteria)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions

    async def _create_collaboration_suggestion(self, opportunity: Dict[str, Any], criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a specific collaboration suggestion"""
        try:
            prompt = f"""
            Create a collaboration suggestion for this influencer opportunity:
            
            Trend Topic: {opportunity['trend_topic']}
            Collaboration Type: {opportunity['collaboration_type']}
            Opportunity Score: {opportunity['opportunity_score']}
            
            Generate a brief, actionable suggestion including:
            - Collaboration idea
            - Expected benefits
            - Next steps
            - Timeline
            
            Return as JSON with keys: idea, benefits, next_steps, timeline
            """

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "collaboration suggestion"}
            ]
            
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            suggestion_data = json.loads(response.text_content) if response.success else {}
            
            return {
                "trend_topic": opportunity["trend_topic"],
                "collaboration_type": opportunity["collaboration_type"],
                "opportunity_score": opportunity["opportunity_score"],
                "suggestion": suggestion_data,
                "estimated_reach": opportunity["estimated_reach"],
                "timing": opportunity["timing"]
            }
            
        except Exception:
            # Fallback suggestion
            return {
                "trend_topic": opportunity["trend_topic"],
                "collaboration_type": opportunity["collaboration_type"],
                "opportunity_score": opportunity["opportunity_score"],
                "suggestion": {
                    "idea": f"Create a {opportunity['collaboration_type']} around {opportunity['trend_topic']}",
                    "benefits": "Increase reach and engagement",
                    "next_steps": "Research potential collaborators",
                    "timeline": opportunity["timing"]["recommended_timing"]
                },
                "estimated_reach": opportunity["estimated_reach"],
                "timing": opportunity["timing"]
            }
