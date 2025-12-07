import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy import and_
from .models import Integration, IntegrationType, IntegrationStatus
from ..database.connection import get_database

logger = logging.getLogger(__name__)

class IntegrationTypes:
    """Manages different types of integrations for Agent47 system."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize integration types with default configurations."""
        if self._initialized:
            return
        
        db = get_database()
        async with db.get_session() as session:
            # Check if integrations already exist
            existing_integrations = await session.execute(select(Integration))
            if existing_integrations.scalars().first():
                logger.info("Integration types already exist in database.")
                self._initialized = True
                return
            
            # Create default integrations
            default_integrations = self._get_default_integrations()
            for integration_data in default_integrations:
                integration = Integration(**integration_data)
                session.add(integration)
            
            await session.commit()
            logger.info("Default integration types created successfully.")
        
        self._initialized = True
    
    def _get_default_integrations(self) -> List[Dict[str, Any]]:
        """Get default integration configurations."""
        return [
            # Marketing Integrations
            {
                "name": "mailchimp",
                "display_name": "Mailchimp",
                "integration_type": IntegrationType.MARKETING,
                "description": "Email marketing and automation platform",
                "provider": "Mailchimp",
                "api_version": "v3",
                "base_url": "https://us1.api.mailchimp.com/3.0",
                "api_documentation_url": "https://mailchimp.com/developer",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 10,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": False,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "convertkit",
                "display_name": "ConvertKit",
                "integration_type": IntegrationType.MARKETING,
                "description": "Email marketing platform for creators",
                "provider": "ConvertKit",
                "api_version": "v3",
                "base_url": "https://api.convertkit.com/v3",
                "api_documentation_url": "https://developers.convertkit.com",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": False,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "klaviyo",
                "display_name": "Klaviyo",
                "integration_type": IntegrationType.MARKETING,
                "description": "Customer data and marketing automation platform",
                "provider": "Klaviyo",
                "api_version": "v2",
                "base_url": "https://a.klaviyo.com/api/v2",
                "api_documentation_url": "https://developers.klaviyo.com",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Analytics Integrations
            {
                "name": "google_analytics",
                "display_name": "Google Analytics",
                "integration_type": IntegrationType.ANALYTICS,
                "description": "Web analytics service for tracking website traffic",
                "provider": "Google",
                "api_version": "v1",
                "base_url": "https://analyticsdata.googleapis.com/v1beta",
                "api_documentation_url": "https://developers.google.com/analytics/devguides/reporting/data/v1",
                "pricing_tier": "free",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "mixpanel",
                "display_name": "Mixpanel",
                "integration_type": IntegrationType.ANALYTICS,
                "description": "Product analytics platform for user behavior tracking",
                "provider": "Mixpanel",
                "api_version": "v2",
                "base_url": "https://api.mixpanel.com",
                "api_documentation_url": "https://developer.mixpanel.com/docs",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "amplitude",
                "display_name": "Amplitude",
                "integration_type": IntegrationType.ANALYTICS,
                "description": "Product analytics platform for digital products",
                "provider": "Amplitude",
                "api_version": "v2",
                "base_url": "https://api.amplitude.com",
                "api_documentation_url": "https://www.docs.developers.amplitude.com",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # CRM Integrations
            {
                "name": "hubspot",
                "display_name": "HubSpot",
                "integration_type": IntegrationType.CRM,
                "description": "Customer relationship management platform",
                "provider": "HubSpot",
                "api_version": "v3",
                "base_url": "https://api.hubapi.com",
                "api_documentation_url": "https://developers.hubspot.com/docs/api",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "salesforce",
                "display_name": "Salesforce",
                "integration_type": IntegrationType.CRM,
                "description": "Customer relationship management and cloud computing platform",
                "provider": "Salesforce",
                "api_version": "v58.0",
                "base_url": "https://{instance}.salesforce.com/services/data/v58.0",
                "api_documentation_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 15000,
                    "requests_per_hour": 100000,
                    "requests_per_day": 1000000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "pipedrive",
                "display_name": "Pipedrive",
                "integration_type": IntegrationType.CRM,
                "description": "Sales CRM and pipeline management platform",
                "provider": "Pipedrive",
                "api_version": "v1",
                "base_url": "https://api.pipedrive.com/v1",
                "api_documentation_url": "https://developers.pipedrive.com",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Content Integrations
            {
                "name": "wordpress",
                "display_name": "WordPress",
                "integration_type": IntegrationType.CONTENT,
                "description": "Content management system and website builder",
                "provider": "WordPress.org",
                "api_version": "v2",
                "base_url": "https://{site}/wp-json/wp/v2",
                "api_documentation_url": "https://developer.wordpress.org/rest-api",
                "pricing_tier": "free",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "contentful",
                "display_name": "Contentful",
                "integration_type": IntegrationType.CONTENT,
                "description": "Headless content management system",
                "provider": "Contentful",
                "api_version": "v3",
                "base_url": "https://cdn.contentful.com/spaces/{space_id}",
                "api_documentation_url": "https://www.contentful.com/developers/docs",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "notion",
                "display_name": "Notion",
                "integration_type": IntegrationType.CONTENT,
                "description": "All-in-one workspace for notes, docs, and collaboration",
                "provider": "Notion",
                "api_version": "v1",
                "base_url": "https://api.notion.com/v1",
                "api_documentation_url": "https://developers.notion.com",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 3,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": False,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Design Integrations
            {
                "name": "figma",
                "display_name": "Figma",
                "integration_type": IntegrationType.DESIGN,
                "description": "Collaborative interface design tool",
                "provider": "Figma",
                "api_version": "v1",
                "base_url": "https://api.figma.com/v1",
                "api_documentation_url": "https://www.figma.com/developers/api",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "canva",
                "display_name": "Canva",
                "integration_type": IntegrationType.DESIGN,
                "description": "Graphic design platform for creating visual content",
                "provider": "Canva",
                "api_version": "v1",
                "base_url": "https://api.canva.com/v1",
                "api_documentation_url": "https://www.canva.dev",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": False
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Productivity Integrations
            {
                "name": "slack",
                "display_name": "Slack",
                "integration_type": IntegrationType.PRODUCTIVITY,
                "description": "Team communication and collaboration platform",
                "provider": "Slack",
                "api_version": "v1",
                "base_url": "https://slack.com/api",
                "api_documentation_url": "https://api.slack.com",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 50,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "trello",
                "display_name": "Trello",
                "integration_type": IntegrationType.PRODUCTIVITY,
                "description": "Project management and collaboration tool",
                "provider": "Atlassian",
                "api_version": "v1",
                "base_url": "https://api.trello.com/1",
                "api_documentation_url": "https://developer.atlassian.com/cloud/trello",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "asana",
                "display_name": "Asana",
                "integration_type": IntegrationType.PRODUCTIVITY,
                "description": "Work management platform for teams",
                "provider": "Asana",
                "api_version": "v1",
                "base_url": "https://app.asana.com/api/1.0",
                "api_documentation_url": "https://developers.asana.com",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Finance Integrations
            {
                "name": "stripe",
                "display_name": "Stripe",
                "integration_type": IntegrationType.FINANCE,
                "description": "Payment processing platform",
                "provider": "Stripe",
                "api_version": "2023-10-16",
                "base_url": "https://api.stripe.com/v1",
                "api_documentation_url": "https://stripe.com/docs/api",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "paypal",
                "display_name": "PayPal",
                "integration_type": IntegrationType.FINANCE,
                "description": "Online payment system",
                "provider": "PayPal",
                "api_version": "v1",
                "base_url": "https://api-m.paypal.com/v1",
                "api_documentation_url": "https://developer.paypal.com",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Research Integrations - Chutes AI removed
            {
                "name": "grok-llm",
                "display_name": "Grok LLM (Fallback)",
                "integration_type": IntegrationType.RESEARCH,
                "description": "Advanced AI language model for business automation and analysis - Emergency fallback",
                "provider": "xAI",
                "api_version": "v1",
                "base_url": "http://localhost:8008",  # Local Grok service
                "api_documentation_url": "https://x.ai/grok",
                "pricing_tier": "free",  # Local deployment
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": True,
                    "bulk_operations": True,
                    "local_deployment": True,
                    "custom_training": True,
                    "fallback_mode": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": True,
                    "local_auth": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "openai",
                "display_name": "OpenAI (Fallback)",
                "integration_type": IntegrationType.RESEARCH,
                "description": "Artificial intelligence research and deployment company - Fallback option",
                "provider": "OpenAI",
                "api_version": "v1",
                "base_url": "https://api.openai.com/v1",
                "api_documentation_url": "https://platform.openai.com/docs",
                "pricing_tier": "paid",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": False,
                    "real_time": True,
                    "bulk_operations": True,
                    "fallback_mode": True
                },
                "authentication_methods": {
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            # Automation Integrations
            {
                "name": "zapier",
                "display_name": "Zapier",
                "integration_type": IntegrationType.AUTOMATION,
                "description": "Automation platform for connecting apps and services",
                "provider": "Zapier",
                "api_version": "v1",
                "base_url": "https://api.zapier.com/v1",
                "api_documentation_url": "https://zapier.com/developer",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            },
            {
                "name": "ifttt",
                "display_name": "IFTTT",
                "integration_type": IntegrationType.AUTOMATION,
                "description": "Platform for creating conditional statements called applets",
                "provider": "IFTTT",
                "api_version": "v1",
                "base_url": "https://connect.ifttt.com/v1",
                "api_documentation_url": "https://platform.ifttt.com/docs",
                "pricing_tier": "freemium",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                "supported_features": {
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": False
                },
                "authentication_methods": {
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                },
                "status": IntegrationStatus.ACTIVE,
                "is_available": True
            }
        ]
    
    async def get_integration_by_name(self, name: str) -> Optional[Integration]:
        """Get integration by name."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Integration).where(Integration.name == name)
            )
            return result.scalar_one_or_none()
    
    async def get_all_integrations(self) -> List[Integration]:
        """Get all available integrations."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Integration).where(Integration.is_available == True)
            )
            return result.scalars().all()
    
    async def get_integrations_by_type(self, integration_type: IntegrationType) -> List[Integration]:
        """Get integrations by type."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Integration).where(
                    and_(
                        Integration.integration_type == integration_type,
                        Integration.is_available == True
                    )
                )
            )
            return result.scalars().all()
    
    async def get_marketing_integrations(self) -> List[Integration]:
        """Get all marketing integrations."""
        return await self.get_integrations_by_type(IntegrationType.MARKETING)
    
    async def get_analytics_integrations(self) -> List[Integration]:
        """Get all analytics integrations."""
        return await self.get_integrations_by_type(IntegrationType.ANALYTICS)
    
    async def get_crm_integrations(self) -> List[Integration]:
        """Get all CRM integrations."""
        return await self.get_integrations_by_type(IntegrationType.CRM)
    
    async def get_content_integrations(self) -> List[Integration]:
        """Get all content integrations."""
        return await self.get_integrations_by_type(IntegrationType.CONTENT)
    
    async def get_design_integrations(self) -> List[Integration]:
        """Get all design integrations."""
        return await self.get_integrations_by_type(IntegrationType.DESIGN)
    
    async def get_productivity_integrations(self) -> List[Integration]:
        """Get all productivity integrations."""
        return await self.get_integrations_by_type(IntegrationType.PRODUCTIVITY)
    
    async def get_finance_integrations(self) -> List[Integration]:
        """Get all finance integrations."""
        return await self.get_integrations_by_type(IntegrationType.FINANCE)
    
    async def get_research_integrations(self) -> List[Integration]:
        """Get all research integrations."""
        return await self.get_integrations_by_type(IntegrationType.RESEARCH)
    
    async def get_automation_integrations(self) -> List[Integration]:
        """Get all automation integrations."""
        return await self.get_integrations_by_type(IntegrationType.AUTOMATION)
    
    async def get_integration_features(self, integration_name: str) -> Dict[str, Any]:
        """Get features for a specific integration."""
        integration = await self.get_integration_by_name(integration_name)
        if integration:
            return integration.supported_features
        return {}
    
    async def check_integration_feature(self, integration_name: str, feature: str) -> bool:
        """Check if an integration supports a specific feature."""
        features = await self.get_integration_features(integration_name)
        return features.get(feature, False)
    
    async def get_integration_rate_limits(self, integration_name: str) -> Dict[str, Any]:
        """Get rate limits for a specific integration."""
        integration = await self.get_integration_by_name(integration_name)
        if integration:
            return integration.rate_limits
        return {}
    
    async def get_integration_authentication_methods(self, integration_name: str) -> Dict[str, Any]:
        """Get authentication methods for a specific integration."""
        integration = await self.get_integration_by_name(integration_name)
        if integration:
            return integration.authentication_methods
        return {}
    
    async def update_integration_status(self, integration_name: str, status: IntegrationStatus) -> bool:
        """Update integration status."""
        db = get_database()
        
        async with db.get_session() as session:
            integration = await self.get_integration_by_name(integration_name)
            if not integration:
                return False
            
            integration.status = status
            integration.updated_at = datetime.utcnow()
            
            session.add(integration)
            await session.commit()
            
            logger.info(f"Updated integration status for {integration_name}: {status.value}")
            return True
    
    async def get_integration_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Get a comparison of all integrations."""
        integrations = await self.get_all_integrations()
        comparison = {}
        
        for integration in integrations:
            comparison[integration.name] = {
                "display_name": integration.display_name,
                "integration_type": integration.integration_type.value,
                "description": integration.description,
                "provider": integration.provider,
                "api_version": integration.api_version,
                "pricing_tier": integration.pricing_tier,
                "rate_limits": integration.rate_limits,
                "supported_features": integration.supported_features,
                "authentication_methods": integration.authentication_methods,
                "status": integration.status.value,
                "is_available": integration.is_available
            }
        
        return comparison

# Global instance
integration_types = IntegrationTypes()

async def get_integration_types() -> IntegrationTypes:
    """Get the global integration types instance."""
    if not integration_types._initialized:
        await integration_types.initialize()
    return integration_types
