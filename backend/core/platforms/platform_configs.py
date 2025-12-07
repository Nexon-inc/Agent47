from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    SOCIAL_MEDIA = "social_media"
    BUSINESS = "business"
    CONTENT = "content"
    ANALYTICS = "analytics"
    PRODUCTIVITY = "productivity"
    ECOMMERCE = "ecommerce"
    COMMUNICATION = "communication"

@dataclass
class PlatformConfig:
    """Configuration for a platform's OAuth and API settings"""
    name: str
    display_name: str
    platform_type: PlatformType
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    redirect_uri: str
    scopes: List[str]
    supports_refresh: bool
    supports_workspaces: bool
    max_users_per_app: int
    rate_limits: Dict[str, int]
    supported_features: Dict[str, bool]
    api_base_url: str
    api_version: str
    documentation_url: str

class PlatformConfigManager:
    """Manages platform configurations for OAuth and API access"""
    
    def __init__(self):
        self._configs = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize platform configurations from environment variables"""
        if self._initialized:
            return
        
        try:
            from ..config import settings
            
            self._configs = {
                "linkedin": PlatformConfig(
                    name="linkedin",
                    display_name="LinkedIn",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.linkedin.client_id or "default_client_id",
                    client_secret=settings.linkedin.client_secret or "default_client_secret",
                    auth_url="https://www.linkedin.com/oauth/v2/authorization",
                    token_url="https://www.linkedin.com/oauth/v2/accessToken",
                    redirect_uri=f"{settings.base_url}/auth/callback/linkedin",
                    scopes=["r_liteprofile", "r_emailaddress", "w_member_social", "rw_organization_admin"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 500,
                        "requests_per_day": 5000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://api.linkedin.com/v2",
                    api_version="2.0",
                    documentation_url="https://docs.microsoft.com/en-us/linkedin/"
                ),
                "twitter": PlatformConfig(
                    name="twitter",
                    display_name="Twitter (X)",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.twitter.client_id or "default_client_id",
                    client_secret=settings.twitter.client_secret or "default_client_secret",
                    auth_url="https://twitter.com/i/oauth2/authorize",
                    token_url="https://api.twitter.com/2/oauth2/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/twitter",
                    scopes=["tweet.read", "tweet.write", "users.read", "follows.read", "follows.write"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=10000,
                    rate_limits={
                        "requests_per_minute": 300,
                        "requests_per_hour": 3000,
                        "requests_per_day": 300000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://api.twitter.com/2",
                    api_version="2.0",
                    documentation_url="https://developer.twitter.com/en/docs"
                ),
                "facebook": PlatformConfig(
                    name="facebook",
                    display_name="Facebook",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.facebook.app_id or "default_client_id",
                    client_secret=settings.facebook.app_secret or "default_client_secret",
                    auth_url="https://www.facebook.com/v18.0/dialog/oauth",
                    token_url="https://graph.facebook.com/v18.0/oauth/access_token",
                    redirect_uri=f"{settings.base_url}/auth/callback/facebook",
                    scopes=["pages_manage_posts", "pages_read_engagement", "pages_show_list", "instagram_basic", "instagram_content_publish"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=10000,
                    rate_limits={
                        "requests_per_minute": 200,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://graph.facebook.com/v18.0",
                    api_version="18.0",
                    documentation_url="https://developers.facebook.com/docs"
                ),
                "instagram": PlatformConfig(
                    name="instagram",
                    display_name="Instagram",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.instagram.client_id or "default_client_id",
                    client_secret=settings.instagram.client_secret or "default_client_secret",
                    auth_url="https://api.instagram.com/oauth/authorize",
                    token_url="https://api.instagram.com/oauth/access_token",
                    redirect_uri=f"{settings.base_url}/auth/callback/instagram",
                    scopes=["user_profile", "user_media"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 200,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://graph.instagram.com",
                    api_version="18.0",
                    documentation_url="https://developers.facebook.com/docs/instagram-basic-display-api"
                ),
                "youtube": PlatformConfig(
                    name="youtube",
                    display_name="YouTube",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.youtube.client_id or "default_client_id",
                    client_secret=settings.youtube.client_secret or "default_client_secret",
                    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                    token_url="https://oauth2.googleapis.com/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/youtube",
                    scopes=["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=10000,
                    rate_limits={
                        "requests_per_minute": 300,
                        "requests_per_hour": 10000,
                        "requests_per_day": 100000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://www.googleapis.com/youtube/v3",
                    api_version="3.0",
                    documentation_url="https://developers.google.com/youtube/v3"
                ),
                "tiktok": PlatformConfig(
                    name="tiktok",
                    display_name="TikTok",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.tiktok.client_id or "default_client_id",
                    client_secret=settings.tiktok.client_secret or "default_client_secret",
                    auth_url="https://www.tiktok.com/auth/authorize",
                    token_url="https://open.tiktokapis.com/v2/oauth/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/tiktok",
                    scopes=["user.info.basic", "video.publish"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://open.tiktokapis.com/v2",
                    api_version="1.0",
                    documentation_url="https://developers.tiktok.com/doc"
                ),
                "pinterest": PlatformConfig(
                    name="pinterest",
                    display_name="Pinterest",
                    platform_type=PlatformType.SOCIAL_MEDIA,
                    client_id=settings.pinterest.client_id or "default_client_id",
                    client_secret=settings.pinterest.client_secret or "default_client_secret",
                    auth_url="https://www.pinterest.com/oauth",
                    token_url="https://api.pinterest.com/v5/oauth/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/pinterest",
                    scopes=["pins:read", "pins:write", "boards:read", "boards:write"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://api.pinterest.com/v5",
                    api_version="5.0",
                    documentation_url="https://developers.pinterest.com/docs"
                ),
                "slack": PlatformConfig(
                    name="slack",
                    display_name="Slack",
                    platform_type=PlatformType.COMMUNICATION,
                    client_id=settings.slack.client_id or "default_client_id",
                    client_secret=settings.slack.client_secret or "default_client_secret",
                    auth_url="https://slack.com/oauth/v2/authorize",
                    token_url="https://slack.com/api/oauth.v2.access",
                    redirect_uri=f"{settings.base_url}/auth/callback/slack",
                    scopes=["chat:write", "channels:read", "users:read", "files:write"],
                    supports_refresh=False,
                    supports_workspaces=True,
                    max_users_per_app=10000,
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": True,
                        "analytics": False,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://slack.com/api",
                    api_version="2.0",
                    documentation_url="https://api.slack.com"
                ),
                "hubspot": PlatformConfig(
                    name="hubspot",
                    display_name="HubSpot",
                    platform_type=PlatformType.BUSINESS,
                    client_id=settings.hubspot.client_id or "default_client_id",
                    client_secret=settings.hubspot.client_secret or "default_client_secret",
                    auth_url="https://app.hubspot.com/oauth/authorize",
                    token_url="https://api.hubapi.com/oauth/v1/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/hubspot",
                    scopes=["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read", "crm.objects.companies.write"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": False,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://api.hubapi.com",
                    api_version="3.0",
                    documentation_url="https://developers.hubspot.com/docs"
                ),
                "salesforce": PlatformConfig(
                    name="salesforce",
                    display_name="Salesforce",
                    platform_type=PlatformType.BUSINESS,
                    client_id=settings.salesforce.client_id or "default_client_id",
                    client_secret=settings.salesforce.client_secret or "default_client_secret",
                    auth_url="https://login.salesforce.com/services/oauth2/authorize",
                    token_url="https://login.salesforce.com/services/oauth2/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/salesforce",
                    scopes=["api", "refresh_token", "id", "profile", "email"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 1000,
                        "requests_per_hour": 10000,
                        "requests_per_day": 100000
                    },
                    supported_features={
                        "posting": False,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://api.salesforce.com",
                    api_version="58.0",
                    documentation_url="https://developer.salesforce.com/docs"
                ),
                "mailchimp": PlatformConfig(
                    name="mailchimp",
                    display_name="Mailchimp",
                    platform_type=PlatformType.COMMUNICATION,
                    client_id=settings.mailchimp.client_id or "default_client_id",
                    client_secret=settings.mailchimp.client_secret or "default_client_secret",
                    auth_url="https://login.mailchimp.com/oauth2/authorize",
                    token_url="https://login.mailchimp.com/oauth2/token",
                    redirect_uri=f"{settings.base_url}/auth/callback/mailchimp",
                    scopes=["campaigns:read", "campaigns:write", "lists:read", "lists:write"],
                    supports_refresh=True,
                    supports_workspaces=False,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 10,
                        "requests_per_hour": 100,
                        "requests_per_day": 1000
                    },
                    supported_features={
                        "posting": False,
                        "analytics": True,
                        "engagement": True,
                        "scheduling": True,
                        "automation": True
                    },
                    api_base_url="https://us1.api.mailchimp.com/3.0",
                    api_version="3.0",
                    documentation_url="https://mailchimp.com/developer"
                ),
                "shopify": PlatformConfig(
                    name="shopify",
                    display_name="Shopify",
                    platform_type=PlatformType.ECOMMERCE,
                    client_id=settings.shopify.client_id or "default_client_id",
                    client_secret=settings.shopify.client_secret or "default_client_secret",
                    auth_url="https://{shop}.myshopify.com/admin/oauth/authorize",
                    token_url="https://{shop}.myshopify.com/admin/oauth/access_token",
                    redirect_uri=f"{settings.base_url}/auth/callback/shopify",
                    scopes=["read_products", "write_products", "read_orders", "write_orders"],
                    supports_refresh=False,
                    supports_workspaces=True,
                    max_users_per_app=1000,
                    rate_limits={
                        "requests_per_minute": 40,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "posting": False,
                        "analytics": True,
                        "engagement": False,
                        "scheduling": False,
                        "automation": True
                    },
                    api_base_url="https://{shop}.myshopify.com/admin/api/2023-10",
                    api_version="2023-10",
                    documentation_url="https://shopify.dev/api"
                )
            }
            
            self._initialized = True
            logger.info(f"Platform configurations initialized for {len(self._configs)} platforms")
            
        except Exception as e:
            logger.error(f"Failed to initialize platform configurations: {e}")
            raise
    
    def get_config(self, platform_name: str) -> PlatformConfig:
        """Get configuration for a specific platform"""
        if not self._initialized:
            raise RuntimeError("Platform config manager not initialized")
        
        if platform_name not in self._configs:
            raise ValueError(f"Platform '{platform_name}' not configured")
        
        return self._configs[platform_name]
    
    def get_all_configs(self) -> Dict[str, PlatformConfig]:
        """Get all platform configurations"""
        if not self._initialized:
            raise RuntimeError("Platform config manager not initialized")
        
        return self._configs.copy()
    
    def get_platforms_by_type(self, platform_type: PlatformType) -> Dict[str, PlatformConfig]:
        """Get platforms filtered by type"""
        if not self._initialized:
            raise RuntimeError("Platform config manager not initialized")
        
        return {
            name: config for name, config in self._configs.items()
            if config.platform_type == platform_type
        }
    
    def validate_config(self, platform_name: str) -> bool:
        """Validate that a platform configuration is complete"""
        try:
            config = self.get_config(platform_name)
            required_fields = [
                'client_id', 'client_secret', 'auth_url', 'token_url',
                'redirect_uri', 'scopes', 'api_base_url'
            ]
            
            for field in required_fields:
                if not getattr(config, field):
                    logger.error(f"Platform {platform_name} missing required field: {field}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to validate platform {platform_name}: {e}")
            return False
    
    def get_oauth_url(self, platform_name: str, state: str) -> str:
        """Generate OAuth authorization URL for a platform"""
        config = self.get_config(platform_name)
        
        params = {
            'client_id': config.client_id,
            'redirect_uri': config.redirect_uri,
            'scope': ' '.join(config.scopes),
            'response_type': 'code',
            'state': state
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{config.auth_url}?{query_string}"

# Global instance
platform_config_manager = PlatformConfigManager()

async def get_platform_config_manager() -> PlatformConfigManager:
    """Get the global platform config manager instance"""
    if not platform_config_manager._initialized:
        await platform_config_manager.initialize()
    return platform_config_manager
