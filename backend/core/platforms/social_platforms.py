import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import select
from ..database.models import SocialPlatform, PlatformType, PlatformStatus
from ..database.connection import get_database

logger = logging.getLogger(__name__)

class SocialPlatforms:
    """Manages social media and business platforms for Agent47 integrations."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize social platforms with default configurations."""
        if self._initialized:
            return
        from ..database.connection import get_supabase
        db = await get_supabase()
        async with db.get_session() as session:
            # Check if platforms already exist
            existing_platforms = await session.execute(select(SocialPlatform))
            if existing_platforms.scalars().first():
                logger.info("Social platforms already exist in database.")
                self._initialized = True
                return
            
            # Create default social platforms
            default_platforms = self._get_default_platforms()
            for platform_data in default_platforms:
                platform = SocialPlatform(**platform_data)
                session.add(platform)
            
            await session.commit()
            logger.info("Default social platforms created successfully.")
        
        self._initialized = True
    
    def _get_default_platforms(self) -> List[Dict[str, Any]]:
        """Get default social platform configurations."""
        return [
            # Social Media Platforms
            {
                "name": "facebook",
                "display_name": "Facebook",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "World's largest social networking platform",
                "api_version": "v18.0",
                "base_url": "https://graph.facebook.com",
                "api_documentation_url": "https://developers.facebook.com/docs/graph-api",
                "rate_limits": {
                    "requests_per_minute": 200,
                    "requests_per_hour": 4800,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "advertising": True,
                    "messaging": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "instagram",
                "display_name": "Instagram",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Photo and video sharing social network",
                "api_version": "v18.0",
                "base_url": "https://graph.instagram.com",
                "api_documentation_url": "https://developers.facebook.com/docs/instagram-basic-display-api",
                "rate_limits": {
                    "requests_per_minute": 200,
                    "requests_per_hour": 4800,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "stories": True,
                    "reels": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "twitter",
                "display_name": "Twitter/X",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Microblogging and social networking platform",
                "api_version": "v2",
                "base_url": "https://api.twitter.com/2",
                "api_documentation_url": "https://developer.twitter.com/en/docs",
                "rate_limits": {
                    "requests_per_minute": 300,
                    "requests_per_hour": 3000,
                    "requests_per_day": 300000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "trending_topics": True,
                    "lists": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "linkedin",
                "display_name": "LinkedIn",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Professional networking platform",
                "api_version": "v2",
                "base_url": "https://api.linkedin.com/v2",
                "api_documentation_url": "https://developer.linkedin.com/docs",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "networking": True,
                    "job_posting": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "youtube",
                "display_name": "YouTube",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Video sharing and streaming platform",
                "api_version": "v3",
                "base_url": "https://www.googleapis.com/youtube/v3",
                "api_documentation_url": "https://developers.google.com/youtube/v3",
                "rate_limits": {
                    "requests_per_minute": 300,
                    "requests_per_hour": 10000,
                    "requests_per_day": 1000000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "live_streaming": True,
                    "playlists": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "tiktok",
                "display_name": "TikTok",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Short-form video sharing platform",
                "api_version": "v1.3",
                "base_url": "https://open.tiktokapis.com/v1.3",
                "api_documentation_url": "https://developers.tiktok.com/doc",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "trending": True,
                    "duets": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "pinterest",
                "display_name": "Pinterest",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Visual discovery and bookmarking platform",
                "api_version": "v5",
                "base_url": "https://api.pinterest.com/v5",
                "api_documentation_url": "https://developers.pinterest.com/docs",
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "boards": True,
                    "pins": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "snapchat",
                "display_name": "Snapchat",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Multimedia messaging and social media platform",
                "api_version": "v1",
                "base_url": "https://kit.snapchat.com/v1",
                "api_documentation_url": "https://developers.snapchat.com/docs",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "stories": True,
                    "filters": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "reddit",
                "display_name": "Reddit",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Social news aggregation and discussion platform",
                "api_version": "v1",
                "base_url": "https://oauth.reddit.com",
                "api_documentation_url": "https://www.reddit.com/dev/api",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "subreddits": True,
                    "moderation": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "discord",
                "display_name": "Discord",
                "platform_type": PlatformType.SOCIAL_MEDIA,
                "description": "Voice, video, and text communication platform",
                "api_version": "v10",
                "base_url": "https://discord.com/api/v10",
                "api_documentation_url": "https://discord.com/developers/docs",
                "rate_limits": {
                    "requests_per_minute": 50,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": False,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "voice_channels": True,
                    "bots": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            # Business Platforms
            {
                "name": "shopify",
                "display_name": "Shopify",
                "platform_type": PlatformType.BUSINESS,
                "description": "E-commerce platform for online stores",
                "api_version": "2023-10",
                "base_url": "https://{shop}.myshopify.com/admin/api/2023-10",
                "api_documentation_url": "https://shopify.dev/api",
                "rate_limits": {
                    "requests_per_minute": 40,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": False,
                    "scheduling": False,
                    "automation": True,
                    "inventory": True,
                    "orders": True,
                    "customers": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "stripe",
                "display_name": "Stripe",
                "platform_type": PlatformType.BUSINESS,
                "description": "Payment processing platform",
                "api_version": "2023-10-16",
                "base_url": "https://api.stripe.com/v1",
                "api_documentation_url": "https://stripe.com/docs/api",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": False,
                    "scheduling": False,
                    "automation": True,
                    "payments": True,
                    "subscriptions": True,
                    "invoicing": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "mailchimp",
                "display_name": "Mailchimp",
                "platform_type": PlatformType.BUSINESS,
                "description": "Email marketing and automation platform",
                "api_version": "v3",
                "base_url": "https://us1.api.mailchimp.com/3.0",
                "api_documentation_url": "https://mailchimp.com/developer",
                "rate_limits": {
                    "requests_per_minute": 10,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "email_campaigns": True,
                    "audience_management": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "hubspot",
                "display_name": "HubSpot",
                "platform_type": PlatformType.BUSINESS,
                "description": "Customer relationship management platform",
                "api_version": "v3",
                "base_url": "https://api.hubapi.com",
                "api_documentation_url": "https://developers.hubspot.com/docs/api",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "crm": True,
                    "marketing": True,
                    "sales": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "salesforce",
                "display_name": "Salesforce",
                "platform_type": PlatformType.BUSINESS,
                "description": "Customer relationship management and cloud computing platform",
                "api_version": "v58.0",
                "base_url": "https://{instance}.salesforce.com/services/data/v58.0",
                "api_documentation_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest",
                "rate_limits": {
                    "requests_per_minute": 15000,
                    "requests_per_hour": 100000,
                    "requests_per_day": 1000000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "crm": True,
                    "sales": True,
                    "service": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            # Content Platforms
            {
                "name": "wordpress",
                "display_name": "WordPress",
                "platform_type": PlatformType.CONTENT,
                "description": "Content management system and website builder",
                "api_version": "v2",
                "base_url": "https://{site}/wp-json/wp/v2",
                "api_documentation_url": "https://developer.wordpress.org/rest-api",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": False,
                    "engagement": False,
                    "scheduling": True,
                    "automation": True,
                    "content_management": True,
                    "media_library": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "medium",
                "display_name": "Medium",
                "platform_type": PlatformType.CONTENT,
                "description": "Online publishing platform for articles and stories",
                "api_version": "v1",
                "base_url": "https://api.medium.com/v1",
                "api_documentation_url": "https://github.com/Medium/medium-api-docs",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True,
                    "publications": True,
                    "series": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "substack",
                "display_name": "Substack",
                "platform_type": PlatformType.CONTENT,
                "description": "Newsletter publishing and subscription platform",
                "api_version": "v1",
                "base_url": "https://substack.com/api/v1",
                "api_documentation_url": "https://substack.com/api/docs",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True,
                    "newsletters": True,
                    "subscriptions": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            # Analytics Platforms
            {
                "name": "google_analytics",
                "display_name": "Google Analytics",
                "platform_type": PlatformType.ANALYTICS,
                "description": "Web analytics service for tracking website traffic",
                "api_version": "v1",
                "base_url": "https://analyticsdata.googleapis.com/v1beta",
                "api_documentation_url": "https://developers.google.com/analytics/devguides/reporting/data/v1",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": False,
                    "scheduling": False,
                    "automation": True,
                    "traffic_analysis": True,
                    "conversion_tracking": True,
                    "audience_insights": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "mixpanel",
                "display_name": "Mixpanel",
                "platform_type": PlatformType.ANALYTICS,
                "description": "Product analytics platform for user behavior tracking",
                "api_version": "v2",
                "base_url": "https://api.mixpanel.com",
                "api_documentation_url": "https://developer.mixpanel.com/docs",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": False,
                    "scheduling": False,
                    "automation": True,
                    "event_tracking": True,
                    "funnel_analysis": True,
                    "cohort_analysis": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "amplitude",
                "display_name": "Amplitude",
                "platform_type": PlatformType.ANALYTICS,
                "description": "Product analytics platform for digital products",
                "api_version": "v2",
                "base_url": "https://api.amplitude.com",
                "api_documentation_url": "https://www.docs.developers.amplitude.com",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "posting": False,
                    "analytics": True,
                    "engagement": False,
                    "scheduling": False,
                    "automation": True,
                    "user_behavior": True,
                    "retention_analysis": True,
                    "path_analysis": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": PlatformStatus.ACTIVE,
                "is_available": True
            }
        ]
    
    async def get_platform_by_name(self, name: str) -> Optional[SocialPlatform]:
        """Get social platform by name."""
    from ..database.connection import get_supabase
    db = await get_supabase()
        async with db.get_session() as session:
            result = await session.execute(
                select(SocialPlatform).where(SocialPlatform.name == name)
            )
            return result.scalar_one_or_none()
    
    async def get_all_platforms(self) -> List[SocialPlatform]:
        """Get all available social platforms."""
    from ..database.connection import get_supabase
    db = await get_supabase()
        async with db.get_session() as session:
            result = await session.execute(
                select(SocialPlatform).where(SocialPlatform.is_available == True)
            )
            return result.scalars().all()
    
    async def get_platforms_by_type(self, platform_type: PlatformType) -> List[SocialPlatform]:
        """Get platforms by type."""
    from ..database.connection import get_supabase
    db = await get_supabase()
        async with db.get_session() as session:
            result = await session.execute(
                select(SocialPlatform).where(
                    and_(
                        SocialPlatform.platform_type == platform_type,
                        SocialPlatform.is_available == True
                    )
                )
            )
            return result.scalars().all()
    
    async def get_social_media_platforms(self) -> List[SocialPlatform]:
        """Get all social media platforms."""
        return await self.get_platforms_by_type(PlatformType.SOCIAL_MEDIA)
    
    async def get_business_platforms(self) -> List[SocialPlatform]:
        """Get all business platforms."""
        return await self.get_platforms_by_type(PlatformType.BUSINESS)
    
    async def get_content_platforms(self) -> List[SocialPlatform]:
        """Get all content platforms."""
        return await self.get_platforms_by_type(PlatformType.CONTENT)
    
    async def get_analytics_platforms(self) -> List[SocialPlatform]:
        """Get all analytics platforms."""
        return await self.get_platforms_by_type(PlatformType.ANALYTICS)
    
    async def get_platform_features(self, platform_name: str) -> Dict[str, Any]:
        """Get features for a specific platform."""
        platform = await self.get_platform_by_name(platform_name)
        if platform:
            return platform.supported_features
        return {}
    
    async def check_platform_feature(self, platform_name: str, feature: str) -> bool:
        """Check if a platform supports a specific feature."""
        features = await self.get_platform_features(platform_name)
        return features.get(feature, False)
    
    async def get_platform_rate_limits(self, platform_name: str) -> Dict[str, Any]:
        """Get rate limits for a specific platform."""
        platform = await self.get_platform_by_name(platform_name)
        if platform:
            return platform.rate_limits
        return {}
    
    async def get_platform_authentication_methods(self, platform_name: str) -> Dict[str, Any]:
        """Get authentication methods for a specific platform."""
        platform = await self.get_platform_by_name(platform_name)
        if platform:
            return platform.authentication_methods
        return {}
    
    async def update_platform_status(self, platform_name: str, status: PlatformStatus) -> bool:
        """Update platform status."""
        db = get_database()
        
        async with db.get_session() as session:
            platform = await self.get_platform_by_name(platform_name)
            if not platform:
                return False
            
            platform.status = status
            platform.updated_at = datetime.utcnow()
            
            session.add(platform)
            await session.commit()
            
            logger.info(f"Updated platform status for {platform_name}: {status.value}")
            return True
    
    async def get_platform_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Get a comparison of all platforms."""
        platforms = await self.get_all_platforms()
        comparison = {}
        
        for platform in platforms:
            comparison[platform.name] = {
                "display_name": platform.display_name,
                "platform_type": platform.platform_type.value,
                "description": platform.description,
                "api_version": platform.api_version,
                "rate_limits": platform.rate_limits,
                "supported_features": platform.supported_features,
                "authentication_methods": platform.authentication_methods,
                "status": platform.status.value,
                "is_available": platform.is_available
            }
        
        return comparison

# Global instance
social_platforms = SocialPlatforms()

async def get_social_platforms() -> SocialPlatforms:
    """Get the global social platforms instance."""
    if not social_platforms._initialized:
        await social_platforms.initialize()
    return social_platforms
