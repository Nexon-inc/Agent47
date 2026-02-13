from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    CRM = "crm"
    CONTENT = "content"
    DESIGN = "design"
    PRODUCTIVITY = "productivity"
    FINANCE = "finance"
    RESEARCH = "research"
    AUTOMATION = "automation"
    AI = "ai"
    COMMUNICATION = "communication"
    ECOMMERCE = "ecommerce"

@dataclass
class IntegrationConfig:
    """Configuration for an integration's API and authentication settings"""
    name: str
    display_name: str
    integration_type: IntegrationType
    description: str
    provider: str
    api_version: str
    api_base_url: str
    documentation_url: str
    pricing_tier: str
    rate_limits: Dict[str, int]
    supported_features: Dict[str, bool]
    authentication_methods: Dict[str, bool]
    scopes: List[str]
    supports_oauth: bool
    supports_api_key: bool
    supports_bearer_token: bool
    oauth_url: str = None
    token_url: str = None
    redirect_uri: str = None

class IntegrationConfigManager:
    """Manages integration configurations for API access and authentication"""
    
    def __init__(self):
        self._configs = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize integration configurations from environment variables"""
        if self._initialized:
            return
        
        try:
            from ..config import settings
            
            self._configs = {
                # Marketing Tools
                "mailchimp": IntegrationConfig(
                    name="mailchimp",
                    display_name="Mailchimp",
                    integration_type=IntegrationType.MARKETING,
                    description="Email marketing and automation platform",
                    provider="Mailchimp",
                    api_version="3.0",
                    api_base_url="https://us1.api.mailchimp.com/3.0",
                    documentation_url="https://mailchimp.com/developer",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 10,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": False,
                        "bulk_operations": True,
                        "campaigns": True,
                        "lists": True,
                        "automation": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["campaigns:read", "campaigns:write", "lists:read", "lists:write"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=False,
                    oauth_url="https://login.mailchimp.com/oauth2/authorize",
                    token_url="https://login.mailchimp.com/oauth2/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/mailchimp"
                ),
                "convertkit": IntegrationConfig(
                    name="convertkit",
                    display_name="ConvertKit",
                    integration_type=IntegrationType.MARKETING,
                    description="Email marketing platform for creators",
                    provider="ConvertKit",
                    api_version="3.0",
                    api_base_url="https://api.convertkit.com/v3",
                    documentation_url="https://developers.convertkit.com",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": False,
                        "bulk_operations": True,
                        "campaigns": True,
                        "subscribers": True,
                        "automation": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["broadcasts:read", "broadcasts:write", "subscribers:read", "subscribers:write"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=False
                ),
                "klaviyo": IntegrationConfig(
                    name="klaviyo",
                    display_name="Klaviyo",
                    integration_type=IntegrationType.MARKETING,
                    description="Customer data and marketing automation platform",
                    provider="Klaviyo",
                    api_version="2023-02-22",
                    api_base_url="https://a.klaviyo.com/api",
                    documentation_url="https://developers.klaviyo.com",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "campaigns": True,
                        "profiles": True,
                        "automation": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["campaigns:read", "campaigns:write", "profiles:read", "profiles:write"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=False
                ),
                
                # Analytics Tools
                "google_analytics": IntegrationConfig(
                    name="google_analytics",
                    display_name="Google Analytics",
                    integration_type=IntegrationType.ANALYTICS,
                    description="Web analytics service",
                    provider="Google",
                    api_version="4",
                    api_base_url="https://analyticsreporting.googleapis.com/v4",
                    documentation_url="https://developers.google.com/analytics",
                    pricing_tier="free",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": False,
                        "real_time": True,
                        "bulk_operations": True,
                        "reports": True,
                        "segments": True,
                        "goals": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["https://www.googleapis.com/auth/analytics.readonly"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=False,
                    oauth_url="https://accounts.google.com/o/oauth2/v2/auth",
                    token_url="https://oauth2.googleapis.com/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/google_analytics"
                ),
                "mixpanel": IntegrationConfig(
                    name="mixpanel",
                    display_name="Mixpanel",
                    integration_type=IntegrationType.ANALYTICS,
                    description="Product analytics platform",
                    provider="Mixpanel",
                    api_version="2.0",
                    api_base_url="https://mixpanel.com/api/2.0",
                    documentation_url="https://developer.mixpanel.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "events": True,
                        "funnels": True,
                        "retention": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["events:read", "events:write", "insights:read"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=False
                ),
                "amplitude": IntegrationConfig(
                    name="amplitude",
                    display_name="Amplitude",
                    integration_type=IntegrationType.ANALYTICS,
                    description="Digital analytics platform",
                    provider="Amplitude",
                    api_version="2",
                    api_base_url="https://amplitude.com/api/2",
                    documentation_url="https://developers.amplitude.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "events": True,
                        "cohorts": True,
                        "experiments": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["events:read", "events:write", "cohorts:read"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=False
                ),
                
                # CRM Tools
                "hubspot": IntegrationConfig(
                    name="hubspot",
                    display_name="HubSpot",
                    integration_type=IntegrationType.CRM,
                    description="Inbound marketing and sales platform",
                    provider="HubSpot",
                    api_version="3.0",
                    api_base_url="https://api.hubapi.com",
                    documentation_url="https://developers.hubspot.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "contacts": True,
                        "companies": True,
                        "deals": True,
                        "automation": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read", "crm.objects.companies.write"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=False,
                    oauth_url="https://app.hubspot.com/oauth/authorize",
                    token_url="https://api.hubapi.com/oauth/v1/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/hubspot"
                ),
                "salesforce": IntegrationConfig(
                    name="salesforce",
                    display_name="Salesforce",
                    integration_type=IntegrationType.CRM,
                    description="Customer relationship management platform",
                    provider="Salesforce",
                    api_version="58.0",
                    api_base_url="https://api.salesforce.com",
                    documentation_url="https://developer.salesforce.com",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 1000,
                        "requests_per_hour": 10000,
                        "requests_per_day": 100000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "leads": True,
                        "opportunities": True,
                        "accounts": True,
                        "automation": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": False,
                        "bearer_token": False
                    },
                    scopes=["api", "refresh_token", "id", "profile", "email"],
                    supports_oauth=True,
                    supports_api_key=False,
                    supports_bearer_token=False,
                    oauth_url="https://login.salesforce.com/services/oauth2/authorize",
                    token_url="https://login.salesforce.com/services/oauth2/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/salesforce"
                ),
                "pipedrive": IntegrationConfig(
                    name="pipedrive",
                    display_name="Pipedrive",
                    integration_type=IntegrationType.CRM,
                    description="Sales CRM and pipeline management",
                    provider="Pipedrive",
                    api_version="1",
                    api_base_url="https://api.pipedrive.com/v1",
                    documentation_url="https://developers.pipedrive.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "deals": True,
                        "persons": True,
                        "organizations": True,
                        "activities": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["deals:read", "deals:write", "persons:read", "persons:write"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=False
                ),
                
                # Content Tools
                "wordpress": IntegrationConfig(
                    name="wordpress",
                    display_name="WordPress",
                    integration_type=IntegrationType.CONTENT,
                    description="Content management system",
                    provider="WordPress",
                    api_version="2",
                    api_base_url="https://your-site.com/wp-json/wp/v2",
                    documentation_url="https://developer.wordpress.org/rest-api",
                    pricing_tier="free",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": False,
                        "real_time": False,
                        "bulk_operations": True,
                        "posts": True,
                        "pages": True,
                        "media": True,
                        "comments": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["posts:read", "posts:write", "pages:read", "pages:write"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True
                ),
                "contentful": IntegrationConfig(
                    name="contentful",
                    display_name="Contentful",
                    integration_type=IntegrationType.CONTENT,
                    description="Headless content management platform",
                    provider="Contentful",
                    api_version="1",
                    api_base_url="https://api.contentful.com",
                    documentation_url="https://www.contentful.com/developers",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "entries": True,
                        "assets": True,
                        "spaces": True,
                        "environments": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["content:read", "content:write", "assets:read", "assets:write"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=True
                ),
                "notion": IntegrationConfig(
                    name="notion",
                    display_name="Notion",
                    integration_type=IntegrationType.PRODUCTIVITY,
                    description="All-in-one workspace for notes and collaboration",
                    provider="Notion",
                    api_version="2022-06-28",
                    api_base_url="https://api.notion.com/v1",
                    documentation_url="https://developers.notion.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 3,
                        "requests_per_hour": 100,
                        "requests_per_day": 1000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "pages": True,
                        "databases": True,
                        "blocks": True,
                        "users": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["read", "write", "insert"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True,
                    oauth_url="https://api.notion.com/v1/oauth/authorize",
                    token_url="https://api.notion.com/v1/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/notion"
                ),
                
                # Design Tools
                "figma": IntegrationConfig(
                    name="figma",
                    display_name="Figma",
                    integration_type=IntegrationType.DESIGN,
                    description="Collaborative interface design tool",
                    provider="Figma",
                    api_version="1",
                    api_base_url="https://api.figma.com/v1",
                    documentation_url="https://www.figma.com/developers",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": False,
                        "files": True,
                        "projects": True,
                        "teams": True,
                        "comments": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["file_read", "file_write", "team_read"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True,
                    oauth_url="https://www.figma.com/oauth",
                    token_url="https://www.figma.com/api/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/figma"
                ),
                "canva": IntegrationConfig(
                    name="canva",
                    display_name="Canva",
                    integration_type=IntegrationType.DESIGN,
                    description="Graphic design platform",
                    provider="Canva",
                    api_version="1.0",
                    api_base_url="https://api.canva.com",
                    documentation_url="https://www.canva.dev/docs",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": False,
                        "real_time": False,
                        "bulk_operations": False,
                        "templates": True,
                        "designs": True,
                        "brands": True,
                        "folders": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": False,
                        "bearer_token": False
                    },
                    scopes=["design:read", "design:write", "template:read"],
                    supports_oauth=True,
                    supports_api_key=False,
                    supports_bearer_token=False,
                    oauth_url="https://www.canva.com/api/oauth/authorize",
                    token_url="https://api.canva.com/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/canva"
                ),
                
                # Communication Tools
                "slack": IntegrationConfig(
                    name="slack",
                    display_name="Slack",
                    integration_type=IntegrationType.COMMUNICATION,
                    description="Team communication and collaboration platform",
                    provider="Slack",
                    api_version="2.0",
                    api_base_url="https://slack.com/api",
                    documentation_url="https://api.slack.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "messages": True,
                        "channels": True,
                        "users": True,
                        "files": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": False,
                        "bearer_token": True
                    },
                    scopes=["chat:write", "channels:read", "users:read", "files:write"],
                    supports_oauth=True,
                    supports_api_key=False,
                    supports_bearer_token=True,
                    oauth_url="https://slack.com/oauth/v2/authorize",
                    token_url="https://slack.com/api/oauth.v2.access",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/slack"
                ),
                "trello": IntegrationConfig(
                    name="trello",
                    display_name="Trello",
                    integration_type=IntegrationType.PRODUCTIVITY,
                    description="Project management and collaboration tool",
                    provider="Trello",
                    api_version="1",
                    api_base_url="https://api.trello.com/1",
                    documentation_url="https://developer.atlassian.com/cloud/trello",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "boards": True,
                        "lists": True,
                        "cards": True,
                        "members": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["read", "write", "account"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True,
                    oauth_url="https://trello.com/1/OAuthAuthorizeToken",
                    token_url="https://trello.com/1/OAuthGetAccessToken",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/trello"
                ),
                "asana": IntegrationConfig(
                    name="asana",
                    display_name="Asana",
                    integration_type=IntegrationType.PRODUCTIVITY,
                    description="Work management and team collaboration platform",
                    provider="Asana",
                    api_version="1.0",
                    api_base_url="https://app.asana.com/api/1.0",
                    documentation_url="https://developers.asana.com",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "projects": True,
                        "tasks": True,
                        "teams": True,
                        "users": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["default"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True,
                    oauth_url="https://app.asana.com/-/oauth_authorize",
                    token_url="https://app.asana.com/-/oauth_token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/asana"
                ),
                
                # Finance Tools
                "stripe": IntegrationConfig(
                    name="stripe",
                    display_name="Stripe",
                    integration_type=IntegrationType.FINANCE,
                    description="Payment processing platform",
                    provider="Stripe",
                    api_version="2023-10-16",
                    api_base_url="https://api.stripe.com/v1",
                    documentation_url="https://stripe.com/docs/api",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "payments": True,
                        "customers": True,
                        "subscriptions": True,
                        "invoices": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": False
                    },
                    scopes=["read", "write"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=False,
                    oauth_url="https://connect.stripe.com/oauth/authorize",
                    token_url="https://connect.stripe.com/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/stripe"
                ),
                "paypal": IntegrationConfig(
                    name="paypal",
                    display_name="PayPal",
                    integration_type=IntegrationType.FINANCE,
                    description="Online payment system",
                    provider="PayPal",
                    api_version="2.0",
                    api_base_url="https://api-m.paypal.com/v2",
                    documentation_url="https://developer.paypal.com",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": True,
                        "payments": True,
                        "orders": True,
                        "subscriptions": True,
                        "payouts": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": False,
                        "bearer_token": True
                    },
                    scopes=["https://uri.paypal.com/services/subscriptions"],
                    supports_oauth=True,
                    supports_api_key=False,
                    supports_bearer_token=True,
                    oauth_url="https://www.paypal.com/signin/authorize",
                    token_url="https://api-m.paypal.com/v1/oauth2/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/paypal"
                ),
                
                # AI Tools
                "openai": IntegrationConfig(
                    name="openai",
                    display_name="OpenAI",
                    integration_type=IntegrationType.AI,
                    description="Artificial intelligence research and deployment company",
                    provider="OpenAI",
                    api_version="1",
                    api_base_url="https://api.openai.com/v1",
                    documentation_url="https://platform.openai.com/docs",
                    pricing_tier="paid",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": False,
                        "real_time": True,
                        "bulk_operations": True,
                        "completions": True,
                        "embeddings": True,
                        "images": True,
                        "fine_tuning": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["completions:read", "completions:write", "embeddings:read"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=True
                ),
                # Chutes AI removed
                "grok-llm": IntegrationConfig(
                    name="grok-llm",
                    display_name="Grok LLM",
                    integration_type=IntegrationType.AI,
                    description="Large language model for text generation and analysis",
                    provider="Grok",
                    api_version="1.0",
                    api_base_url="https://api.grok.ai/v1",
                    documentation_url="https://docs.grok.ai",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": False,
                        "real_time": True,
                        "bulk_operations": True,
                        "text_generation": True,
                        "conversation": True,
                        "analysis": True,
                        "translation": True
                    },
                    authentication_methods={
                        "oauth2": False,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["text:generate", "conversation:create", "analysis:perform"],
                    supports_oauth=False,
                    supports_api_key=True,
                    supports_bearer_token=True
                ),
                
                # Automation Tools
                "zapier": IntegrationConfig(
                    name="zapier",
                    display_name="Zapier",
                    integration_type=IntegrationType.AUTOMATION,
                    description="Workflow automation platform",
                    provider="Zapier",
                    api_version="1.0",
                    api_base_url="https://hooks.zapier.com/hooks/catch",
                    documentation_url="https://zapier.com/developer",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": False,
                        "zaps": True,
                        "triggers": True,
                        "actions": True,
                        "filters": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": True,
                        "bearer_token": True
                    },
                    scopes=["zaps:read", "zaps:write", "triggers:read", "actions:write"],
                    supports_oauth=True,
                    supports_api_key=True,
                    supports_bearer_token=True,
                    oauth_url="https://zapier.com/oauth/authorize",
                    token_url="https://zapier.com/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/zapier"
                ),
                "ifttt": IntegrationConfig(
                    name="ifttt",
                    display_name="IFTTT",
                    integration_type=IntegrationType.AUTOMATION,
                    description="Platform for creating conditional statements called applets",
                    provider="IFTTT",
                    api_version="1",
                    api_base_url="https://connect.ifttt.com/v1",
                    documentation_url="https://platform.ifttt.com/docs",
                    pricing_tier="freemium",
                    rate_limits={
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "requests_per_day": 10000
                    },
                    supported_features={
                        "api_access": True,
                        "webhooks": True,
                        "real_time": True,
                        "bulk_operations": False,
                        "applets": True,
                        "triggers": True,
                        "actions": True,
                        "queries": True
                    },
                    authentication_methods={
                        "oauth2": True,
                        "api_key": False,
                        "bearer_token": True
                    },
                    scopes=["applets:read", "applets:write", "triggers:read", "actions:write"],
                    supports_oauth=True,
                    supports_api_key=False,
                    supports_bearer_token=True,
                    oauth_url="https://ifttt.com/oauth/authorize",
                    token_url="https://ifttt.com/oauth/token",
                    redirect_uri=f"{settings.base_url}{settings.api_v1_prefix}/integrations/callback/ifttt"
                )
            }
            
            self._initialized = True
            logger.info(f"Integration configurations initialized for {len(self._configs)} integrations")
            
        except Exception as e:
            logger.error(f"Failed to initialize integration configurations: {e}")
            raise
    
    def get_config(self, integration_name: str) -> IntegrationConfig:
        """Get configuration for a specific integration"""
        if not self._initialized:
            raise RuntimeError("Integration config manager not initialized")
        
        if integration_name not in self._configs:
            raise ValueError(f"Integration '{integration_name}' not configured")
        
        return self._configs[integration_name]
    
    def get_all_configs(self) -> Dict[str, IntegrationConfig]:
        """Get all integration configurations"""
        if not self._initialized:
            raise RuntimeError("Integration config manager not initialized")
        
        return self._configs.copy()
    
    def get_integrations_by_type(self, integration_type: IntegrationType) -> Dict[str, IntegrationConfig]:
        """Get integrations filtered by type"""
        if not self._initialized:
            raise RuntimeError("Integration config manager not initialized")
        
        return {
            name: config for name, config in self._configs.items()
            if config.integration_type == integration_type
        }
    
    def validate_config(self, integration_name: str) -> bool:
        """Validate that an integration configuration is complete"""
        try:
            config = self.get_config(integration_name)
            required_fields = [
                'name', 'display_name', 'integration_type', 'description',
                'provider', 'api_version', 'api_base_url', 'documentation_url'
            ]
            
            for field in required_fields:
                if not getattr(config, field):
                    logger.error(f"Integration {integration_name} missing required field: {field}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to validate integration {integration_name}: {e}")
            return False
    
    def get_oauth_url(self, integration_name: str, state: str) -> str:
        """Generate OAuth authorization URL for an integration"""
        config = self.get_config(integration_name)
        
        if not config.supports_oauth or not config.oauth_url:
            raise ValueError(f"Integration {integration_name} does not support OAuth")
        
        params = {
            'client_id': f"{integration_name.upper()}_CLIENT_ID",  # Would come from settings
            'redirect_uri': config.redirect_uri,
            'scope': ' '.join(config.scopes),
            'response_type': 'code',
            'state': state
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{config.oauth_url}?{query_string}"

# Global instance
integration_config_manager = IntegrationConfigManager()

async def get_integration_config_manager() -> IntegrationConfigManager:
    """Get the global integration config manager instance"""
    if not integration_config_manager._initialized:
        await integration_config_manager.initialize()
    return integration_config_manager
