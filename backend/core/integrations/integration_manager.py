import httpx
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
import logging
from ..config import settings
from ..database.connection import get_database
from ..billing import get_billing
from .models import (
    Integration, IntegrationCredentials, IntegrationUsage,
    IntegrationType, IntegrationStatus, CredentialStatus
)

logger = logging.getLogger(__name__)

class IntegrationManager:
    def __init__(self):
        self._initialized = False
        self._integration_clients = {}
        
    async def initialize(self):
        """Initialize integration management system"""
        try:
            db = get_database()
            async with db.get_session() as session:
                await self._create_default_integrations(session)
            self._initialized = True
            logger.info("Integration manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integration manager: {e}")
            raise
    
    async def _create_default_integrations(self, session: AsyncSession):
        """Create default integrations if they don't exist"""
        existing_integrations = await session.execute(select(Integration))
        if existing_integrations.scalars().first():
            return
        
        default_integrations = [
            # Marketing Tools
            Integration(
                name="brandwatch",
                display_name="Brandwatch",
                integration_type=IntegrationType.ANALYTICS,
                description="Social listening and analytics",
                provider="Brandwatch",
                api_version="1.0",
                base_url=settings.brandwatch.base_url or "https://api.brandwatch.com",
                api_documentation_url="https://developers.brandwatch.com",
                pricing_tier="paid",
                rate_limits={
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            Integration(
                name="buffer",
                display_name="Buffer",
                integration_type=IntegrationType.PRODUCTIVITY,
                description="Social media scheduling platform",
                provider="Buffer",
                api_version="1.0",
                base_url=settings.buffer.base_url or "https://api.bufferapp.com/1",
                api_documentation_url="https://buffer.com/developers/api",
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
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            Integration(
                name="mailchimp",
                display_name="Mailchimp",
                integration_type=IntegrationType.MARKETING,
                description="Email marketing and automation platform",
                provider="Mailchimp",
                api_version="3.0",
                base_url="https://us1.api.mailchimp.com/3.0",
                api_documentation_url="https://mailchimp.com/developer/marketing/api",
                pricing_tier="free",
                rate_limits={
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": True,
                    "real_time": False,
                    "bulk_operations": True
                },
                authentication_methods={
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            Integration(
                name="hubspot",
                display_name="HubSpot",
                integration_type=IntegrationType.CRM,
                description="CRM and marketing automation platform",
                provider="HubSpot",
                api_version="3.0",
                base_url="https://api.hubapi.com",
                api_documentation_url="https://developers.hubspot.com/docs/api",
                pricing_tier="free",
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            # Analytics Tools
            Integration(
                name="google_analytics",
                display_name="Google Analytics",
                integration_type=IntegrationType.ANALYTICS,
                description="Web analytics service",
                provider="Google",
                api_version="4.0",
                base_url="https://analyticsdata.googleapis.com/v1beta",
                api_documentation_url="https://developers.google.com/analytics/devguides/reporting/data/v1",
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
                    "bulk_operations": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            Integration(
                name="semrush",
                display_name="SEMrush",
                integration_type=IntegrationType.ANALYTICS,
                description="SEO and competitive research platform",
                provider="SEMrush",
                api_version="3.0",
                base_url="https://api.semrush.com",
                api_documentation_url="https://developer.semrush.com/api",
                pricing_tier="paid",
                rate_limits={
                    "requests_per_minute": 5,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            # Content Tools
            Integration(
                name="canva",
                display_name="Canva",
                integration_type=IntegrationType.DESIGN,
                description="Graphic design platform",
                provider="Canva",
                api_version="1.0",
                base_url="https://api.canva.com",
                api_documentation_url="https://www.canva.dev/docs",
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
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            Integration(
                name="grammarly",
                display_name="Grammarly",
                integration_type=IntegrationType.CONTENT,
                description="Writing assistant and grammar checker",
                provider="Grammarly",
                api_version="1.0",
                base_url="https://api.grammarly.com",
                api_documentation_url="https://developer.grammarly.com",
                pricing_tier="paid",
                rate_limits={
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            # Productivity Tools
            Integration(
                name="zapier",
                display_name="Zapier",
                integration_type=IntegrationType.AUTOMATION,
                description="Workflow automation platform",
                provider="Zapier",
                api_version="1.0",
                base_url="https://api.zapier.com/v1",
                api_documentation_url="https://zapier.com/developer",
                pricing_tier="free",
                rate_limits={
                    "requests_per_minute": 5,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": True,
                    "real_time": True,
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            Integration(
                name="notion",
                display_name="Notion",
                integration_type=IntegrationType.PRODUCTIVITY,
                description="All-in-one workspace",
                provider="Notion",
                api_version="1.0",
                base_url="https://api.notion.com/v1",
                api_documentation_url="https://developers.notion.com",
                pricing_tier="free",
                rate_limits={
                    "requests_per_minute": 3,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": True,
                    "real_time": False,
                    "bulk_operations": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            # Research Tools
            Integration(
                name="google_trends",
                display_name="Google Trends",
                integration_type=IntegrationType.RESEARCH,
                description="Search trend analysis",
                provider="Google",
                api_version="1.0",
                base_url="https://trends.google.com/trends/api",
                api_documentation_url="https://developers.google.com/trends",
                pricing_tier="free",
                rate_limits={
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": False
                },
                authentication_methods={
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            Integration(
                name="crunchbase",
                display_name="Crunchbase",
                integration_type=IntegrationType.RESEARCH,
                description="Company and startup database",
                provider="Crunchbase",
                api_version="4.0",
                base_url="https://api.crunchbase.com/api/v4",
                api_documentation_url="https://data.crunchbase.com/docs",
                pricing_tier="paid",
                rate_limits={
                    "requests_per_minute": 10,
                    "requests_per_hour": 100,
                    "requests_per_day": 1000
                },
                supported_features={
                    "api_access": True,
                    "webhooks": False,
                    "real_time": False,
                    "bulk_operations": True
                },
                authentication_methods={
                    "oauth2": False,
                    "api_key": True,
                    "bearer_token": False
                }
            )
        ]
        
        for integration in default_integrations:
            session.add(integration)
        await session.commit()
        logger.info("Default integrations created")
    
    async def get_integration(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get integration information by name"""
        try:
            db = get_database()
            async with db.get_session() as session:
                integration = await session.execute(
                    select(Integration).where(Integration.name == integration_name)
                )
                integration = integration.scalar_one_or_none()
                
                if integration:
                    return {
                        "id": integration.id,
                        "name": integration.name,
                        "display_name": integration.display_name,
                        "integration_type": integration.integration_type.value,
                        "description": integration.description,
                        "provider": integration.provider,
                        "api_version": integration.api_version,
                        "base_url": integration.base_url,
                        "pricing_tier": integration.pricing_tier,
                        "rate_limits": integration.rate_limits,
                        "supported_features": integration.supported_features,
                        "authentication_methods": integration.authentication_methods,
                        "status": integration.status.value,
                        "is_available": integration.is_available
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get integration: {e}")
            return None
    
    async def get_integrations_by_type(self, integration_type: IntegrationType) -> List[Dict[str, Any]]:
        """Get all integrations of a specific type"""
        try:
            db = get_database()
            async with db.get_session() as session:
                integrations = await session.execute(
                    select(Integration).where(
                        and_(
                            Integration.integration_type == integration_type,
                            Integration.is_available == True
                        )
                    )
                )
                result = []
                
                for integration in integrations.scalars():
                    result.append({
                        "id": integration.id,
                        "name": integration.name,
                        "display_name": integration.display_name,
                        "description": integration.description,
                        "provider": integration.provider,
                        "pricing_tier": integration.pricing_tier,
                        "status": integration.status.value
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get integrations by type: {e}")
            return []
    
    async def store_integration_credentials(
        self, 
        user_id: int, 
        integration_name: str, 
        credentials_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store integration credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                integration = await session.execute(
                    select(Integration).where(Integration.name == integration_name)
                )
                integration = integration.scalar_one_or_none()
                
                if not integration:
                    return {"success": False, "error": "Integration not found"}
                
                # Check if credentials already exist
                existing_credentials = await session.execute(
                    select(IntegrationCredentials).where(
                        and_(
                            IntegrationCredentials.user_id == user_id,
                            IntegrationCredentials.integration_id == integration.id
                        )
                    )
                )
                existing_credentials = existing_credentials.scalar_one_or_none()
                
                if existing_credentials:
                    # Update existing credentials
                    for key, value in credentials_data.items():
                        if hasattr(existing_credentials, key):
                            setattr(existing_credentials, key, value)
                    existing_credentials.updated_at = datetime.utcnow()
                    existing_credentials.status = CredentialStatus.VALID
                    credentials = existing_credentials
                else:
                    # Create new credentials
                    credentials = IntegrationCredentials(
                        user_id=user_id,
                        integration_id=integration.id,
                        **credentials_data
                    )
                    session.add(credentials)
                
                await session.commit()
                
                return {
                    "success": True,
                    "credentials_id": credentials.id,
                    "message": "Integration credentials stored successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to store integration credentials: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_integration_credentials(self, user_id: int, integration_name: str = None) -> List[Dict[str, Any]]:
        """Get integration credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                query = select(IntegrationCredentials, Integration).join(Integration)
                
                if integration_name:
                    query = query.where(Integration.name == integration_name)
                
                query = query.where(IntegrationCredentials.user_id == user_id)
                
                credentials = await session.execute(query)
                result = []
                
                for cred, integration in credentials:
                    result.append({
                        "id": cred.id,
                        "integration_name": integration.name,
                        "integration_display_name": integration.display_name,
                        "credential_type": cred.credential_type,
                        "status": cred.status.value,
                        "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                        "last_used": cred.last_used.isoformat() if cred.last_used else None,
                        "scopes": cred.scopes
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get user integration credentials: {e}")
            return []
    
    async def validate_integration_credentials(self, user_id: int, integration_name: str) -> Dict[str, Any]:
        """Validate integration credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                credentials = await session.execute(
                    select(IntegrationCredentials, Integration)
                    .join(Integration)
                    .where(
                        and_(
                            Integration.name == integration_name,
                            IntegrationCredentials.user_id == user_id,
                            IntegrationCredentials.status == CredentialStatus.VALID
                        )
                    )
                )
                result = credentials.first()
                
                if not result:
                    return {"valid": False, "error": "No valid credentials found"}
                
                cred, integration = result
                
                # Check if credentials are expired
                if cred.expires_at and cred.expires_at < datetime.utcnow():
                    cred.status = CredentialStatus.EXPIRED
                    await session.commit()
                    return {"valid": False, "error": "Credentials have expired"}
                
                # Test API connection
                api_test = await self._test_integration_api(integration, cred)
                
                if api_test["success"]:
                    cred.last_used = datetime.utcnow()
                    await session.commit()
                    return {"valid": True, "message": "Credentials are valid"}
                else:
                    cred.status = CredentialStatus.INVALID
                    await session.commit()
                    return {"valid": False, "error": api_test["error"]}
                
        except Exception as e:
            logger.error(f"Failed to validate integration credentials: {e}")
            return {"valid": False, "error": str(e)}
    
    async def _test_integration_api(self, integration: Integration, credentials: IntegrationCredentials) -> Dict[str, Any]:
        """Test integration API connection"""
        try:
            headers = {}
            params = {}
            
            if credentials.bearer_token:
                headers["Authorization"] = f"Bearer {credentials.bearer_token}"
            elif credentials.access_token:
                headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                if integration.name == "mailchimp":
                    # Mailchimp uses API key in URL
                    params["apikey"] = credentials.api_key
                elif integration.name == "semrush":
                    # SEMrush uses API key in URL
                    params["key"] = credentials.api_key
                else:
                    headers["X-API-Key"] = credentials.api_key
            
            async with httpx.AsyncClient() as client:
                if integration.name == "mailchimp":
                    response = await client.get(
                        f"{integration.base_url}/ping",
                        params=params,
                        timeout=10.0
                    )
                elif integration.name == "hubspot":
                    response = await client.get(
                        f"{integration.base_url}/crm/v3/objects/contacts",
                        headers=headers,
                        timeout=10.0
                    )
                elif integration.name == "google_analytics":
                    response = await client.get(
                        f"{integration.base_url}/properties:runReport",
                        headers=headers,
                        timeout=10.0
                    )
                elif integration.name == "canva":
                    response = await client.get(
                        f"{integration.base_url}/users/me",
                        headers=headers,
                        timeout=10.0
                    )
                elif integration.name == "notion":
                    response = await client.get(
                        f"{integration.base_url}/users/me",
                        headers=headers,
                        timeout=10.0
                    )
                else:
                    # Generic test for other integrations
                    response = await client.get(
                        f"{integration.base_url}/ping",
                        headers=headers,
                        timeout=10.0
                    )
                
                if response.status_code == 200:
                    return {"success": True, "message": "API connection successful"}
                else:
                    return {"success": False, "error": f"API returned status {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Integration API test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def call_integration_api(
        self, 
        user_id: int, 
        integration_name: str, 
        endpoint: str, 
        method: str = "GET",
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make an API call to an integration"""
        try:
            # Check user billing limits
            billing = await get_billing()
            limit_check = await billing.check_user_limits(user_id, api_call=True)
            
            if not limit_check["allowed"]:
                return {"success": False, "error": limit_check["reason"]}
            
            # Get integration credentials
            db = get_database()
            async with db.get_session() as session:
                credentials = await session.execute(
                    select(IntegrationCredentials, Integration)
                    .join(Integration)
                    .where(
                        and_(
                            Integration.name == integration_name,
                            IntegrationCredentials.user_id == user_id,
                            IntegrationCredentials.status == CredentialStatus.VALID
                        )
                    )
                )
                result = credentials.first()
                
                if not result:
                    return {"success": False, "error": "No valid credentials found for this integration"}
                
                cred, integration = result
                
                # Check if integration supports API access
                if not integration.supported_features.get("api_access", False):
                    return {"success": False, "error": "This integration does not support API access"}
                
                # Make the actual API call
                api_result = await self._make_integration_api_call(integration, cred, endpoint, method, data, params)
                
                if api_result["success"]:
                    # Record usage
                    await billing.record_usage(user_id, api_call=True)
                    
                    # Store usage metrics
                    await self._store_integration_usage(
                        session, integration.id, user_id, 
                        api_result.get("data_size_mb", 0.0)
                    )
                    
                    # Log activity
                    from ..user_management import get_user_manager
                    user_mgr = await get_user_manager()
                    await user_mgr.log_user_activity(
                        user_id=user_id,
                        activity_type="api_call",
                        description=f"API call to {integration.display_name}",
                        metadata={
                            "integration": integration_name,
                            "endpoint": endpoint,
                            "method": method,
                            "success": True
                        }
                    )
                
                return api_result
                
        except Exception as e:
            logger.error(f"Failed to call integration API: {e}")
            return {"success": False, "error": str(e)}
    
    async def _make_integration_api_call(
        self, 
        integration: Integration, 
        credentials: IntegrationCredentials, 
        endpoint: str, 
        method: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make the actual API call to integration"""
        try:
            headers = {}
            request_params = params or {}
            
            if credentials.bearer_token:
                headers["Authorization"] = f"Bearer {credentials.bearer_token}"
            elif credentials.access_token:
                headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                if integration.name == "mailchimp":
                    request_params["apikey"] = credentials.api_key
                elif integration.name == "semrush":
                    request_params["key"] = credentials.api_key
                else:
                    headers["X-API-Key"] = credentials.api_key
            
            url = f"{integration.base_url}{endpoint}"
            
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=request_params, headers=headers, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, params=request_params, headers=headers, timeout=30.0)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, params=request_params, headers=headers, timeout=30.0)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=request_params, headers=headers, timeout=30.0)
                else:
                    return {"success": False, "error": f"Unsupported HTTP method: {method}"}
                
                if response.status_code in [200, 201, 204]:
                    response_data = response.json() if response.content else {}
                    data_size_mb = len(response.content) / (1024 * 1024) if response.content else 0.0
                    
                    return {
                        "success": True,
                        "message": f"API call successful to {integration.display_name}",
                        "data": response_data,
                        "status_code": response.status_code,
                        "data_size_mb": data_size_mb
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}",
                        "response": response.text,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Integration API call failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_integration_usage(self, user_id: int):
        """
        Get list of user's connected integrations for agent context.
        Used by agent_user_data.py to populate context.
        """
        try:
            db = get_database()
            async with db.get_session() as session:
                # Select specific fields to match agent_user_data expectation
                # We return rows which support dot access and return Enum objects for status fields
                query = (
                    select(
                        Integration.id.label("integration_id"),
                        Integration.name.label("integration_name"),
                        Integration.status, 
                        IntegrationCredentials.created_at.label("connected_at"),
                        IntegrationCredentials.last_used,
                        IntegrationCredentials.status.label("credentials_status")
                    )
                    .join(IntegrationCredentials, Integration.id == IntegrationCredentials.integration_id)
                    .where(
                        and_(
                            IntegrationCredentials.user_id == user_id,
                            IntegrationCredentials.status == CredentialStatus.VALID
                        )
                    )
                )
                
                result = await session.execute(query)
                return result.all()
        except Exception as e:
            logger.error(f"Failed to get user integration usage: {e}")
            return []

    async def _store_integration_usage(
        self, 
        session: AsyncSession, 
        integration_id: int, 
        user_id: int, 
        data_processed_mb: float
    ):
        """Store integration usage metrics"""
        try:
            current_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            usage = await session.execute(
                select(IntegrationUsage).where(
                    and_(
                        IntegrationUsage.integration_id == integration_id,
                        IntegrationUsage.user_id == user_id,
                        IntegrationUsage.date == current_date
                    )
                )
            )
            usage = usage.scalar_one_or_none()
            
            if not usage:
                usage = IntegrationUsage(
                    integration_id=integration_id,
                    user_id=user_id,
                    date=current_date
                )
                session.add(usage)
            
            usage.api_calls_count += 1
            usage.data_processed_mb += data_processed_mb
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store integration usage: {e}")
    
    async def get_integration_usage_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get integration usage summary for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                
                usage_data = await session.execute(
                    select(IntegrationUsage, Integration)
                    .join(Integration)
                    .where(
                        and_(
                            IntegrationUsage.user_id == user_id,
                            IntegrationUsage.date >= start_date
                        )
                    )
                )
                
                summary = {
                    "total_api_calls": 0,
                    "total_data_processed_mb": 0.0,
                    "integrations_used": {},
                    "daily_usage": {}
                }
                
                for usage, integration in usage_data:
                    summary["total_api_calls"] += usage.api_calls_count
                    summary["total_data_processed_mb"] += usage.data_processed_mb
                    
                    if integration.name not in summary["integrations_used"]:
                        summary["integrations_used"][integration.name] = {
                            "display_name": integration.display_name,
                            "api_calls": 0,
                            "data_processed_mb": 0.0
                        }
                    
                    summary["integrations_used"][integration.name]["api_calls"] += usage.api_calls_count
                    summary["integrations_used"][integration.name]["data_processed_mb"] += usage.data_processed_mb
                    
                    if usage.date not in summary["daily_usage"]:
                        summary["daily_usage"][usage.date] = {
                            "api_calls": 0,
                            "data_processed_mb": 0.0
                        }
                    
                    summary["daily_usage"][usage.date]["api_calls"] += usage.api_calls_count
                    summary["daily_usage"][usage.date]["data_processed_mb"] += usage.data_processed_mb
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get integration usage summary: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check integration management system health"""
        try:
            if not self._initialized:
                return False
            
            db = get_database()
            async with db.get_session() as session:
                await session.execute(select(Integration).limit(1))
            
            return True
        except Exception as e:
            logger.error(f"Integration management health check failed: {e}")
            return False

integration_manager = IntegrationManager()

async def get_integration_manager() -> IntegrationManager:
    return integration_manager

async def init_integrations():
    await integration_manager.initialize()
