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

class EmergingChannelsService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used in this service
    
    async def initialize(self):
        """Initialize emerging channels service"""
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
            logger.info("Emerging channels service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize emerging channels service: {e}")
            raise
        
        self.supported_channels = {
            "tiktok": {
                "name": "TikTok",
                "description": "Short-form video platform for brand awareness and engagement",
                "features": ["video_ads", "live_streaming", "influencer_marketing", "hashtag_challenges"],
                "api_endpoints": ["ads_api", "content_api", "analytics_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            },
            "instagram_reels": {
                "name": "Instagram Reels",
                "description": "Short-form video content for Instagram users",
                "features": ["video_creation", "story_ads", "shopping_tags", "reels_ads"],
                "api_endpoints": ["instagram_basic_api", "instagram_graph_api", "ads_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            },
            "linkedin_live": {
                "name": "LinkedIn Live",
                "description": "Live streaming for professional networking",
                "features": ["live_streaming", "webinar_integration", "professional_networking", "thought_leadership"],
                "api_endpoints": ["linkedin_api", "live_api", "analytics_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            },
            "clubhouse": {
                "name": "Clubhouse",
                "description": "Audio-based social networking platform",
                "features": ["audio_rooms", "networking", "thought_leadership", "community_building"],
                "api_endpoints": ["clubhouse_api", "rooms_api", "analytics_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            },
            "telegram": {
                "name": "Telegram",
                "description": "Messaging platform with business features",
                "features": ["bot_integration", "channel_marketing", "group_management", "automated_messaging"],
                "api_endpoints": ["telegram_bot_api", "telegram_api", "analytics_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            },
            "discord": {
                "name": "Discord",
                "description": "Community platform for building engaged audiences",
                "features": ["server_management", "bot_integration", "community_building", "voice_channels"],
                "api_endpoints": ["discord_api", "bot_api", "analytics_api"],
                "lead_generation": True,
                "brand_awareness": True,
                "engagement": True
            }
        }

    async def setup_channel_integration(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Setup integration with an emerging sales channel"""
        try:
            channel_name = channel_data["channel_name"]
            
            if channel_name not in self.supported_channels:
                return {"success": False, "error": f"Channel {channel_name} is not supported"}
            
            channel_config = self.supported_channels[channel_name]
            
            integration = {
                "integration_id": f"integration_{channel_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "channel_name": channel_name,
                "channel_config": channel_config,
                "brand_id": channel_data["brand_id"],
                "api_credentials": channel_data.get("api_credentials", {}),
                "webhook_url": channel_data.get("webhook_url", ""),
                "settings": channel_data.get("settings", {}),
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            integration_key = f"channel_integration:{integration['integration_id']}"
            await self.redis_manager.set(
                integration_key,
                json.dumps(integration, default=str),
                expire=86400 * 365
            )
            
            await self._test_channel_connection(integration)
            await self._publish_integration_event("channel_integration_setup", integration)
            
            return {
                "success": True,
                "integration": integration
            }
            
        except Exception as e:
            logger.error(f"Failed to setup channel integration: {e}")
            return {"success": False, "error": str(e)}

    async def _test_channel_connection(self, integration: Dict[str, Any]) -> bool:
        """Test connection to the integrated channel"""
        try:
            channel_name = integration["channel_name"]
            api_credentials = integration["api_credentials"]
            
            if channel_name == "tiktok":
                return await self._test_tiktok_connection(api_credentials)
            elif channel_name == "instagram_reels":
                return await self._test_instagram_connection(api_credentials)
            elif channel_name == "linkedin_live":
                return await self._test_linkedin_connection(api_credentials)
            elif channel_name == "clubhouse":
                return await self._test_clubhouse_connection(api_credentials)
            elif channel_name == "telegram":
                return await self._test_telegram_connection(api_credentials)
            elif channel_name == "discord":
                return await self._test_discord_connection(api_credentials)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to test channel connection: {e}")
            return False

    async def _test_tiktok_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test TikTok API connection"""
        try:
            access_token = api_credentials.get("access_token")
            if not access_token:
                return False
            
            test_url = "https://open.tiktokapis.com/v2/user/info/"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test TikTok connection: {e}")
            return False

    async def _test_instagram_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test Instagram API connection"""
        try:
            access_token = api_credentials.get("access_token")
            if not access_token:
                return False
            
            test_url = "https://graph.instagram.com/me"
            params = {"access_token": access_token, "fields": "id,username"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, params=params)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test Instagram connection: {e}")
            return False

    async def _test_linkedin_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test LinkedIn API connection"""
        try:
            access_token = api_credentials.get("access_token")
            if not access_token:
                return False
            
            test_url = "https://api.linkedin.com/v2/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test LinkedIn connection: {e}")
            return False

    async def _test_clubhouse_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test Clubhouse API connection"""
        try:
            api_key = api_credentials.get("api_key")
            if not api_key:
                return False
            
            test_url = "https://www.clubhouseapi.com/api/get_profile"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test Clubhouse connection: {e}")
            return False

    async def _test_telegram_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test Telegram Bot API connection"""
        try:
            bot_token = api_credentials.get("bot_token")
            if not bot_token:
                return False
            
            test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test Telegram connection: {e}")
            return False

    async def _test_discord_connection(self, api_credentials: Dict[str, Any]) -> bool:
        """Test Discord API connection"""
        try:
            bot_token = api_credentials.get("bot_token")
            if not bot_token:
                return False
            
            test_url = "https://discord.com/api/v10/users/@me"
            headers = {"Authorization": f"Bot {bot_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to test Discord connection: {e}")
            return False

    async def generate_channel_content(self, channel_name: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content optimized for specific emerging channels"""
        try:
            if channel_name not in self.supported_channels:
                return {"success": False, "error": f"Channel {channel_name} is not supported"}
            
            channel_config = self.supported_channels[channel_name]
            
            if channel_name == "tiktok":
                return await self._generate_tiktok_content(content_data)
            elif channel_name == "instagram_reels":
                return await self._generate_instagram_reels_content(content_data)
            elif channel_name == "linkedin_live":
                return await self._generate_linkedin_live_content(content_data)
            elif channel_name == "clubhouse":
                return await self._generate_clubhouse_content(content_data)
            elif channel_name == "telegram":
                return await self._generate_telegram_content(content_data)
            elif channel_name == "discord":
                return await self._generate_discord_content(content_data)
            else:
                return {"success": False, "error": "Unsupported channel"}
                
        except Exception as e:
            logger.error(f"Failed to generate channel content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_tiktok_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate TikTok-optimized content"""
        try:
            prompt = f"""
            Create a TikTok video script for {content_data.get('product', 'our product')} that:
            - Is 15-60 seconds long
            - Uses trending hashtags
            - Has a hook in the first 3 seconds
            - Includes a call-to-action
            - Targets {content_data.get('audience', 'young professionals')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "script": generated_content,
                    "hashtags": await self._get_trending_hashtags("tiktok"),
                    "video_length": "30 seconds",
                    "platform": "tiktok",
                    "optimization_tips": [
                        "Start with a strong hook",
                        "Use trending music",
                        "Include text overlays",
                        "End with clear CTA"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate TikTok content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_instagram_reels_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Instagram Reels-optimized content"""
        try:
            prompt = f"""
            Create an Instagram Reels script for {content_data.get('product', 'our product')} that:
            - Is 15-90 seconds long
            - Uses Instagram-specific features
            - Includes shopping tags
            - Has engaging visuals
            - Targets {content_data.get('audience', 'Instagram users')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "script": generated_content,
                    "hashtags": await self._get_trending_hashtags("instagram"),
                    "video_length": "30 seconds",
                    "platform": "instagram_reels",
                    "optimization_tips": [
                        "Use Instagram filters",
                        "Include product tags",
                        "Add music from Instagram library",
                        "Use Instagram Stories features"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate Instagram Reels content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_linkedin_live_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LinkedIn Live-optimized content"""
        try:
            prompt = f"""
            Create a LinkedIn Live session outline for {content_data.get('product', 'our product')} that:
            - Is professional and business-focused
            - Includes thought leadership content
            - Has interactive elements
            - Targets {content_data.get('audience', 'professionals')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            - Includes Q&A session
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "outline": generated_content,
                    "duration": "45 minutes",
                    "platform": "linkedin_live",
                    "optimization_tips": [
                        "Start with professional introduction",
                        "Include industry insights",
                        "Encourage audience participation",
                        "End with networking opportunities"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate LinkedIn Live content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_clubhouse_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Clubhouse-optimized content"""
        try:
            prompt = f"""
            Create a Clubhouse room concept for {content_data.get('product', 'our product')} that:
            - Is audio-focused and engaging
            - Includes expert speakers
            - Has interactive discussions
            - Targets {content_data.get('audience', 'professionals')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            - Encourages networking
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "room_concept": generated_content,
                    "duration": "60 minutes",
                    "platform": "clubhouse",
                    "optimization_tips": [
                        "Invite industry experts",
                        "Create engaging room titles",
                        "Moderate discussions effectively",
                        "Follow up with attendees"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate Clubhouse content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_telegram_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Telegram-optimized content"""
        try:
            prompt = f"""
            Create Telegram channel content for {content_data.get('product', 'our product')} that:
            - Is concise and informative
            - Includes bot interactions
            - Has regular updates
            - Targets {content_data.get('audience', 'Telegram users')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            - Encourages engagement
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "channel_content": generated_content,
                    "platform": "telegram",
                    "optimization_tips": [
                        "Use Telegram bots for automation",
                        "Post regularly",
                        "Include multimedia content",
                        "Engage with subscribers"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate Telegram content: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_discord_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Discord-optimized content"""
        try:
            prompt = f"""
            Create Discord server content for {content_data.get('product', 'our product')} that:
            - Builds community engagement
            - Includes bot interactions
            - Has regular events
            - Targets {content_data.get('audience', 'Discord users')}
            - Highlights {content_data.get('key_benefits', 'key benefits')}
            - Encourages participation
            """
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates content for emerging social media platforms."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            generated_content = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "content": {
                    "server_content": generated_content,
                    "platform": "discord",
                    "optimization_tips": [
                        "Create engaging channels",
                        "Use Discord bots",
                        "Host regular events",
                        "Build community culture"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate Discord content: {e}")
            return {"success": False, "error": str(e)}

    async def _get_trending_hashtags(self, platform: str) -> List[str]:
        """Get trending hashtags for a platform"""
        try:
            hashtags_key = f"trending_hashtags:{platform}"
            cached_hashtags = await self.redis_manager.get(hashtags_key)
            
            if cached_hashtags:
                return json.loads(cached_hashtags)
            
            # Mock trending hashtags - in production, this would fetch from platform APIs
            trending_hashtags = {
                "tiktok": ["#fyp", "#viral", "#trending", "#business", "#entrepreneur"],
                "instagram": ["#reels", "#viral", "#trending", "#business", "#entrepreneur"],
                "linkedin": ["#business", "#entrepreneur", "#networking", "#professional", "#career"]
            }
            
            platform_hashtags = trending_hashtags.get(platform, ["#business", "#entrepreneur"])
            
            await self.redis_manager.set(
                hashtags_key,
                json.dumps(platform_hashtags),
                expire=3600  # Cache for 1 hour
            )
            
            return platform_hashtags
            
        except Exception as e:
            logger.error(f"Failed to get trending hashtags: {e}")
            return ["#business", "#entrepreneur"]

    async def track_channel_performance(self, integration_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track performance metrics for integrated channels"""
        try:
            integration_key = f"channel_integration:{integration_id}"
            integration_data = await self.redis_manager.get(integration_key)
            
            if not integration_data:
                return {"success": False, "error": "Integration not found"}
            
            integration = json.loads(integration_data)
            
            performance_record = {
                "record_id": f"performance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "integration_id": integration_id,
                "channel_name": integration["channel_name"],
                "brand_id": integration["brand_id"],
                "metrics": metrics_data,
                "timestamp": datetime.utcnow(),
                "period": "daily"
            }
            
            performance_key = f"channel_performance:{performance_record['record_id']}"
            await self.redis_manager.set(
                performance_key,
                json.dumps(performance_record, default=str),
                expire=86400 * 90  # Keep for 90 days
            )
            
            await self._analyze_performance_trends(integration_id, metrics_data)
            await self._publish_integration_event("performance_tracked", performance_record)
            
            return {
                "success": True,
                "performance_record": performance_record
            }
            
        except Exception as e:
            logger.error(f"Failed to track channel performance: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_performance_trends(self, integration_id: str, metrics_data: Dict[str, Any]) -> None:
        """Analyze performance trends and provide insights"""
        try:
            performance_key = f"channel_performance:{integration_id}"
            historical_data = await self.redis_manager.get(performance_key)
            
            if historical_data:
                historical_metrics = json.loads(historical_data)
                
                # Analyze trends
                engagement_trend = "increasing" if metrics_data.get("engagement_rate", 0) > historical_metrics.get("engagement_rate", 0) else "decreasing"
                reach_trend = "increasing" if metrics_data.get("reach", 0) > historical_metrics.get("reach", 0) else "decreasing"
                
                insights = {
                    "engagement_trend": engagement_trend,
                    "reach_trend": reach_trend,
                    "recommendations": await self._generate_performance_recommendations(metrics_data)
                }
                
                insights_key = f"performance_insights:{integration_id}"
                await self.redis_manager.set(
                    insights_key,
                    json.dumps(insights, default=str),
                    expire=86400 * 7
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze performance trends: {e}")

    async def _generate_performance_recommendations(self, metrics_data: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        try:
            recommendations = []
            
            engagement_rate = metrics_data.get("engagement_rate", 0)
            reach = metrics_data.get("reach", 0)
            conversion_rate = metrics_data.get("conversion_rate", 0)
            
            if engagement_rate < 0.05:
                recommendations.append("Focus on creating more engaging content to improve interaction rates")
            
            if reach < 1000:
                recommendations.append("Increase content frequency and use trending hashtags to expand reach")
            
            if conversion_rate < 0.02:
                recommendations.append("Optimize call-to-action placement and messaging to improve conversions")
            
            if not recommendations:
                recommendations.append("Performance is strong. Consider experimenting with new content formats")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate performance recommendations: {e}")
            return ["Continue monitoring performance and optimize based on data"]

    async def _publish_integration_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish integration event to Kafka"""
        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data
            }
            
            await self.kafka_manager.publish("eric.emerging_channels", event)
        except Exception as e:
            logger.error(f"Failed to publish integration event: {e}")

    async def get_supported_channels(self) -> Dict[str, Any]:
        """Get list of supported emerging channels"""
        try:
            return {
                "success": True,
                "supported_channels": self.supported_channels
            }
        except Exception as e:
            logger.error(f"Failed to get supported channels: {e}")
            return {"success": False, "error": str(e)}

    async def get_channel_integrations(self, brand_id: int) -> Dict[str, Any]:
        """Get all channel integrations for a brand"""
        try:
            integrations = []
            
            integration_keys = await self.redis_manager.keys("channel_integration:*")
            
            for key in integration_keys:
                integration_data = await self.redis_manager.get(key)
                if integration_data:
                    integration = json.loads(integration_data)
                    if integration["brand_id"] == brand_id:
                        integrations.append(integration)
            
            return {
                "success": True,
                "integrations": integrations
            }
            
        except Exception as e:
            logger.error(f"Failed to get channel integrations: {e}")
            return {"success": False, "error": str(e)}
