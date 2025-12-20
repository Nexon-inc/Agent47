from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from core.cache.redis_manager import RedisManager
from core.messaging.kafka_manager import KafkaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.ai import get_ai_service_manager
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep, SalesAnalytics
)

logger = logging.getLogger(__name__)

class SocialProfile(BaseModel):
    platform: str  # linkedin, instagram, twitter, facebook
    profile_id: str
    username: str
    display_name: str
    bio: str = ""
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    engagement_rate: float = 0.0
    last_activity: Optional[datetime] = None
    is_verified: bool = False
    industry: str = ""
    location: str = ""
    company: str = ""
    job_title: str = ""

class SocialPost(BaseModel):
    post_id: str
    platform: str
    content: str
    media_urls: List[str] = []
    hashtags: List[str] = []
    mentions: List[str] = []
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    engagement_rate: float = 0.0
    posted_at: datetime
    is_sponsored: bool = False
    target_audience: List[str] = []

class SocialCampaign(BaseModel):
    campaign_id: str
    name: str
    platform: str
    objective: str  # awareness, engagement, leads, sales
    target_audience: Dict[str, Any]
    content_strategy: Dict[str, Any]
    posting_schedule: Dict[str, Any]
    budget: float = 0.0
    start_date: datetime
    end_date: datetime
    status: str = "draft"  # draft, active, paused, completed
    metrics: Dict[str, Any] = {}
    created_at: datetime

class SocialEngagement(BaseModel):
    engagement_id: str
    platform: str
    post_id: str
    user_id: str
    engagement_type: str  # like, comment, share, follow, message
    content: str = ""
    sentiment: str = "neutral"
    timestamp: datetime
    is_lead: bool = False
    lead_score: float = 0.0

class SocialSellingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # Using AI Service Manager for sentiment analysis and entity extraction - NLPUtils removed
    
    async def initialize(self):
        """Initialize social selling service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Social selling service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize social selling service: {e}")
            raise
        
        # Supported platforms
        self.supported_platforms = {
            "linkedin": {
                "name": "LinkedIn",
                "features": ["posts", "articles", "messages", "connections", "groups"],
                "content_types": ["text", "image", "video", "article", "poll"],
                "engagement_types": ["like", "comment", "share", "follow", "message"],
                "best_practices": [
                    "Post during business hours (9 AM - 5 PM)",
                    "Use professional tone",
                    "Include relevant hashtags",
                    "Engage with industry leaders",
                    "Share valuable insights"
                ]
            },
            "instagram": {
                "name": "Instagram",
                "features": ["posts", "stories", "reels", "dms", "live"],
                "content_types": ["image", "video", "story", "reel", "carousel"],
                "engagement_types": ["like", "comment", "share", "follow", "message"],
                "best_practices": [
                    "Post visually appealing content",
                    "Use relevant hashtags (5-10 per post)",
                    "Engage with followers through stories",
                    "Post during peak hours (2-3 PM, 7-9 PM)",
                    "Use Instagram Stories for behind-the-scenes"
                ]
            },
            "twitter": {
                "name": "Twitter",
                "features": ["tweets", "threads", "dms", "spaces", "lists"],
                "content_types": ["text", "image", "video", "poll", "thread"],
                "engagement_types": ["like", "retweet", "reply", "follow", "message"],
                "best_practices": [
                    "Keep tweets concise and engaging",
                    "Use trending hashtags",
                    "Engage in conversations",
                    "Post multiple times per day",
                    "Retweet relevant industry content"
                ]
            },
            "facebook": {
                "name": "Facebook",
                "features": ["posts", "stories", "groups", "pages", "live"],
                "content_types": ["text", "image", "video", "story", "live"],
                "engagement_types": ["like", "comment", "share", "follow", "message"],
                "best_practices": [
                    "Post engaging content that encourages interaction",
                    "Use Facebook Groups for networking",
                    "Go live for real-time engagement",
                    "Post during evening hours (7-9 PM)",
                    "Use Facebook Stories for updates"
                ]
            }
        }
    
    async def analyze_social_profile(self, platform: str, profile_id: str) -> SocialProfile:
        """Analyze a social media profile for sales opportunities"""
        async with get_eric_database() as session:
            try:
                # Get profile data from platform
                profile_data = await self.platform_manager.get_profile_data(platform, profile_id)
                
                # Analyze profile for sales potential
                lead_score = await self._calculate_lead_score(profile_data)
                engagement_rate = await self._calculate_engagement_rate(profile_data)
                
                # Determine industry and company info
                industry = await self._extract_industry(profile_data.get("bio", ""))
                company = await self._extract_company(profile_data.get("bio", ""))
                
                profile = SocialProfile(
                    platform=platform,
                    profile_id=profile_id,
                    username=profile_data.get("username", ""),
                    display_name=profile_data.get("display_name", ""),
                    bio=profile_data.get("bio", ""),
                    followers_count=profile_data.get("followers_count", 0),
                    following_count=profile_data.get("following_count", 0),
                    posts_count=profile_data.get("posts_count", 0),
                    engagement_rate=engagement_rate,
                    last_activity=profile_data.get("last_activity"),
                    is_verified=profile_data.get("is_verified", False),
                    industry=industry,
                    location=profile_data.get("location", ""),
                    company=company,
                    job_title=profile_data.get("job_title", "")
                )
                
                # Cache profile analysis
                await self.redis_manager.set_cache(
                    f"social_profile_{platform}_{profile_id}",
                    profile.dict(),
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "social_selling.profile_analyzed",
                    {
                        "platform": platform,
                        "profile_id": profile_id,
                        "lead_score": lead_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Analyzed social profile {profile_id} on {platform}")
                return profile
                
            except Exception as e:
                logger.error(f"Failed to analyze social profile: {e}")
                raise
    
    async def create_social_campaign(self, campaign_data: Dict[str, Any]) -> SocialCampaign:
        """Create a social selling campaign"""
        try:
            campaign_id = f"campaign_{datetime.utcnow().timestamp()}"
            
            campaign = SocialCampaign(
                campaign_id=campaign_id,
                name=campaign_data["name"],
                platform=campaign_data["platform"],
                objective=campaign_data["objective"],
                target_audience=campaign_data["target_audience"],
                content_strategy=campaign_data["content_strategy"],
                posting_schedule=campaign_data["posting_schedule"],
                budget=campaign_data.get("budget", 0.0),
                start_date=datetime.fromisoformat(campaign_data["start_date"]),
                end_date=datetime.fromisoformat(campaign_data["end_date"]),
                status="draft",
                created_at=datetime.utcnow()
            )
            
            # Cache campaign
            await self.redis_manager.set_cache(
                f"social_campaign_{campaign_id}",
                campaign.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "social_selling.campaign_created",
                {
                    "campaign_id": campaign_id,
                    "platform": campaign.platform,
                    "objective": campaign.objective,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Created social campaign {campaign_id}")
            return campaign
            
        except Exception as e:
            logger.error(f"Failed to create social campaign: {e}")
            raise
    
    async def generate_social_content(self, platform: str, content_type: str, target_audience: Dict[str, Any], objective: str) -> Dict[str, Any]:
        """Generate optimized social media content"""
        try:
            # Get platform-specific best practices
            platform_config = self.supported_platforms.get(platform, {})
            
            # Generate content using NLP
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            prompt = f"Generate {content_type} content for {platform} targeting {target_audience} with objective: {objective}"
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates social media content for sales."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            content = ai_response.text_content if ai_response.success else ""
            
            # Optimize content for platform
            optimized_content = await self._optimize_content_for_platform(
                content,
                platform,
                content_type
            )
            
            # Generate hashtags
            hashtags = await self._generate_relevant_hashtags(
                optimized_content,
                platform,
                target_audience
            )
            
            # Generate posting time recommendations
            posting_times = await self._get_optimal_posting_times(platform, target_audience)
            
            result = {
                "content": optimized_content,
                "hashtags": hashtags,
                "posting_times": posting_times,
                "platform": platform,
                "content_type": content_type,
                "best_practices": platform_config.get("best_practices", []),
                "character_limit": self._get_character_limit(platform, content_type)
            }
            
            logger.info(f"Generated social content for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate social content: {e}")
            raise
    
    async def track_social_engagement(self, platform: str, post_id: str) -> List[SocialEngagement]:
        """Track engagement on social media posts"""
        try:
            # Get engagement data from platform
            engagement_data = await self.platform_manager.get_engagement_data(platform, post_id)
            
            engagements = []
            for engagement in engagement_data:
                # Use AI Service Manager for sentiment analysis
                ai_manager = await get_ai_service_manager()
                content = engagement.get("content", "")
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment. Respond with JSON: {\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0}"}, {"role": "user", "content": f"Analyze the sentiment of: {content}"}]
                sentiment_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
                try:
                    import json
                    sentiment = json.loads(sentiment_response.text_content) if sentiment_response.success else {"sentiment": "neutral", "score": 0.5}
                except:
                    sentiment = {"sentiment": "neutral", "score": 0.5}
                
                # Determine if it's a lead
                is_lead = await self._is_potential_lead(engagement)
                lead_score = await self._calculate_engagement_lead_score(engagement) if is_lead else 0.0
                
                social_engagement = SocialEngagement(
                    engagement_id=engagement["id"],
                    platform=platform,
                    post_id=post_id,
                    user_id=engagement["user_id"],
                    engagement_type=engagement["type"],
                    content=engagement.get("content", ""),
                    sentiment=sentiment,
                    timestamp=datetime.fromisoformat(engagement["timestamp"]),
                    is_lead=is_lead,
                    lead_score=lead_score
                )
                engagements.append(social_engagement)
            
            # Cache engagement data
            await self.redis_manager.set_cache(
                f"social_engagement_{platform}_{post_id}",
                [e.dict() for e in engagements],
                expire=3600  # 1 hour
            )
            
            logger.info(f"Tracked {len(engagements)} engagements for post {post_id}")
            return engagements
            
        except Exception as e:
            logger.error(f"Failed to track social engagement: {e}")
            raise
    
    async def get_social_analytics(self, platform: str = None, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics for social selling activities"""
        try:
            # Query actual social selling data from database
            from ..models import SalesActivity, Lead, Deal
            
            # Calculate date range
            end_date = datetime.now()
            if date_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif date_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get social selling activities
            activities_query = db.query(SalesActivity).filter(
                and_(
                    SalesActivity.activity_type == "social_post",
                    SalesActivity.created_at >= start_date,
                    SalesActivity.created_at <= end_date
                )
            )
            
            if platform:
                activities_query = activities_query.filter(
                    SalesActivity.metadata.contains({"platform": platform})
                )
            
            activities = activities_query.all()
            
            # Calculate analytics
            total_posts = len(activities)
            total_engagement = sum(
                activity.metadata.get("engagement", 0) for activity in activities
            )
            engagement_rate = total_engagement / total_posts if total_posts > 0 else 0
            
            # Calculate leads generated
            leads_generated = 0
            for activity in activities:
                if activity.metadata.get("leads_generated"):
                    leads_generated += activity.metadata["leads_generated"]
            
            conversion_rate = leads_generated / total_posts if total_posts > 0 else 0
            
            # Calculate platform performance
            platform_performance = {}
            for activity in activities:
                platform_name = activity.metadata.get("platform", "unknown")
                if platform_name not in platform_performance:
                    platform_performance[platform_name] = {
                        "posts": 0,
                        "engagement": 0,
                        "leads": 0
                    }
                
                platform_performance[platform_name]["posts"] += 1
                platform_performance[platform_name]["engagement"] += activity.metadata.get("engagement", 0)
                platform_performance[platform_name]["leads"] += activity.metadata.get("leads_generated", 0)
            
            # Calculate engagement rates per platform
            for platform_name, data in platform_performance.items():
                data["engagement_rate"] = data["engagement"] / data["posts"] if data["posts"] > 0 else 0
            
            # Get top performing content
            top_performing_content = []
            for activity in activities:
                if activity.metadata.get("engagement", 0) > 0:
                    top_performing_content.append({
                        "platform": activity.metadata.get("platform", "unknown"),
                        "content": activity.metadata.get("content", "")[:100] + "...",
                        "engagement": activity.metadata.get("engagement", 0),
                        "leads": activity.metadata.get("leads_generated", 0)
                    })
            
            # Sort by engagement and get top 5
            top_performing_content.sort(key=lambda x: x["engagement"], reverse=True)
            top_performing_content = top_performing_content[:5]
            
            # Calculate best posting times (simplified)
            posting_times = {}
            for activity in activities:
                platform_name = activity.metadata.get("platform", "unknown")
                if platform_name not in posting_times:
                    posting_times[platform_name] = []
                
                hour = activity.created_at.hour
                posting_times[platform_name].append(hour)
            
            # Calculate best times (most common hours)
            best_posting_times = {}
            for platform_name, hours in posting_times.items():
                if hours:
                    # Get most common hours
                    hour_counts = {}
                    for hour in hours:
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    
                    # Sort by frequency and get top 3
                    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                    best_hours = [f"{hour}:00" for hour, count in sorted_hours[:3]]
                    best_posting_times[platform_name] = best_hours
                else:
                    best_posting_times[platform_name] = ["9:00 AM", "1:00 PM", "5:00 PM"]  # Default times
            
            analytics = {
                "total_posts": total_posts,
                "total_engagement": total_engagement,
                "engagement_rate": round(engagement_rate, 4),
                "leads_generated": leads_generated,
                "conversion_rate": round(conversion_rate, 4),
                "platform_performance": platform_performance,
                "top_performing_content": top_performing_content,
                "best_posting_times": best_posting_times
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get social analytics: {e}")
            raise
    
    async def get_supported_platforms(self) -> Dict[str, Any]:
        """Get supported social media platforms"""
        try:
            return {
                "platforms": self.supported_platforms,
                "total_platforms": len(self.supported_platforms),
                "features_available": ["profile_analysis", "content_generation", "engagement_tracking", "campaign_management"]
            }
        except Exception as e:
            logger.error(f"Failed to get supported platforms: {e}")
            raise
    
    async def _calculate_lead_score(self, profile_data: Dict[str, Any]) -> float:
        """Calculate lead score for a social profile"""
        try:
            score = 0.0
            
            # Factors that increase lead score
            if profile_data.get("followers_count", 0) > 1000:
                score += 0.2
            if profile_data.get("is_verified", False):
                score += 0.3
            if profile_data.get("job_title", ""):
                score += 0.2
            if profile_data.get("company", ""):
                score += 0.2
            if profile_data.get("industry", ""):
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate lead score: {e}")
            return 0.0
    
    async def _calculate_engagement_rate(self, profile_data: Dict[str, Any]) -> float:
        """Calculate engagement rate for a social profile"""
        try:
            followers = profile_data.get("followers_count", 1)
            total_engagement = profile_data.get("total_engagement", 0)
            
            if followers > 0:
                return total_engagement / followers
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement rate: {e}")
            return 0.0
    
    async def _extract_industry(self, bio: str) -> str:
        """Extract industry from bio text"""
        try:
            # Use NLP to extract industry
            # Use AI Service Manager for industry extraction
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that extracts industry information from text. Respond with only the industry name."}, {"role": "user", "content": f"Extract the industry from this bio: {bio}"}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=50, temperature=0.1)
            industry = ai_response.text_content.strip() if ai_response.success else ""
            return industry
        except Exception as e:
            logger.error(f"Failed to extract industry: {e}")
            return ""
    
    async def _extract_company(self, bio: str) -> str:
        """Extract company from bio text"""
        try:
            # Use NLP to extract company
            # Use AI Service Manager for company extraction
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that extracts company names from text. Respond with only the company name."}, {"role": "user", "content": f"Extract the company name from this bio: {bio}"}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=50, temperature=0.1)
            company = ai_response.text_content.strip() if ai_response.success else ""
            return company
        except Exception as e:
            logger.error(f"Failed to extract company: {e}")
            return ""
    
    async def _optimize_content_for_platform(self, content: str, platform: str, content_type: str) -> str:
        """Optimize content for specific platform"""
        try:
            # Get character limit
            char_limit = self._get_character_limit(platform, content_type)
            
            # Truncate if necessary
            if len(content) > char_limit:
                content = content[:char_limit-3] + "..."
            
            # Add platform-specific formatting
            if platform == "twitter":
                content = content.replace("&", "and")
            elif platform == "linkedin":
                content = content.replace("...", "…")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to optimize content: {e}")
            return content
    
    async def _generate_relevant_hashtags(self, content: str, platform: str, target_audience: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags for content"""
        try:
            # Use NLP to extract keywords
            # Use AI Service Manager for keyword extraction
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that extracts keywords from text. Return a comma-separated list of relevant keywords."}, {"role": "user", "content": f"Extract keywords from: {content}"}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            keywords_str = ai_response.text_content if ai_response.success else ""
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            # Add platform-specific hashtags
            platform_hashtags = {
                "linkedin": ["#business", "#sales", "#networking"],
                "instagram": ["#business", "#entrepreneur", "#success"],
                "twitter": ["#business", "#sales", "#growth"],
                "facebook": ["#business", "#entrepreneur", "#success"]
            }
            
            hashtags = keywords[:5] + platform_hashtags.get(platform, [])
            return hashtags[:10]  # Limit to 10 hashtags
            
        except Exception as e:
            logger.error(f"Failed to generate hashtags: {e}")
            return []
    
    async def _get_optimal_posting_times(self, platform: str, target_audience: Dict[str, Any]) -> List[str]:
        """Get optimal posting times for platform and audience"""
        try:
            # Platform-specific optimal times
            optimal_times = {
                "linkedin": ["9:00 AM", "1:00 PM", "5:00 PM"],
                "instagram": ["2:00 PM", "7:00 PM", "9:00 PM"],
                "twitter": ["8:00 AM", "12:00 PM", "6:00 PM"],
                "facebook": ["7:00 PM", "8:00 PM", "9:00 PM"]
            }
            
            return optimal_times.get(platform, ["9:00 AM", "12:00 PM", "6:00 PM"])
            
        except Exception as e:
            logger.error(f"Failed to get optimal posting times: {e}")
            return ["9:00 AM", "12:00 PM", "6:00 PM"]
    
    def _get_character_limit(self, platform: str, content_type: str) -> int:
        """Get character limit for platform and content type"""
        limits = {
            "linkedin": {"post": 3000, "article": 100000},
            "instagram": {"post": 2200, "story": 100},
            "twitter": {"tweet": 280, "thread": 280},
            "facebook": {"post": 63206, "story": 100}
        }
        
        return limits.get(platform, {}).get(content_type, 1000)
    
    async def _is_potential_lead(self, engagement: Dict[str, Any]) -> bool:
        """Determine if engagement is from a potential lead"""
        try:
            # Check engagement type
            if engagement["type"] in ["message", "comment"]:
                return True
            
            # Check user profile
            user_profile = engagement.get("user_profile", {})
            if user_profile.get("job_title") or user_profile.get("company"):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to determine if potential lead: {e}")
            return False
    
    async def _calculate_engagement_lead_score(self, engagement: Dict[str, Any]) -> float:
        """Calculate lead score for engagement"""
        try:
            score = 0.0
            
            # Engagement type scoring
            if engagement["type"] == "message":
                score += 0.8
            elif engagement["type"] == "comment":
                score += 0.6
            elif engagement["type"] == "share":
                score += 0.4
            elif engagement["type"] == "like":
                score += 0.2
            
            # Content sentiment scoring
            sentiment = engagement.get("sentiment", "neutral")
            if sentiment == "positive":
                score += 0.2
            elif sentiment == "negative":
                score -= 0.2
            
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement lead score: {e}")
            return 0.0
