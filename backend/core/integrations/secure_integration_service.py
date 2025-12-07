import httpx
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging

from .integration_configs import get_integration_config_manager
from .integration_credentials_manager import get_integration_credentials_manager
from .integration_audit_logger import get_integration_audit_logger, IntegrationAuditAction, IntegrationAuditSeverity
from ..security import get_credential_encryption

logger = logging.getLogger(__name__)

class SecureIntegrationService:
    """Secure service for agents to access user integration tools and make API calls"""
    
    def __init__(self):
        self._initialized = False
        self._config_manager = None
        self._credentials_manager = None
        self._audit_logger = None
        self._encryption = None
    
    async def initialize(self):
        """Initialize the secure integration service"""
        if self._initialized:
            return
        
        try:
            self._config_manager = await get_integration_config_manager()
            self._credentials_manager = await get_integration_credentials_manager()
            self._audit_logger = await get_integration_audit_logger()
            self._encryption = await get_credential_encryption()
            self._initialized = True
            
            logger.info("Secure integration service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize secure integration service: {e}")
            raise
    
    async def validate_integration_access(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        required_scopes: List[str] = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate that agent has permission to access user's integration data"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if user has valid credentials for integration
            credentials = await self._credentials_manager.get_user_credentials(user_id, integration_name)
            if not credentials:
                await self._audit_logger.log_security_event(
                    user_id=user_id,
                    integration_name=integration_name,
                    description=f"Agent {agent_name} attempted to access {integration_name} but no valid credentials found",
                    severity=IntegrationAuditSeverity.HIGH,
                    request_id=request_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return False, None
            
            # Check scopes if required
            if required_scopes:
                user_scopes = credentials.get('scopes', [])
                missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]
                if missing_scopes:
                    await self._audit_logger.log_security_event(
                        user_id=user_id,
                        integration_name=integration_name,
                        description=f"Agent {agent_name} attempted to access {integration_name} but missing scopes: {', '.join(missing_scopes)}",
                        severity=IntegrationAuditSeverity.HIGH,
                        metadata={"missing_scopes": missing_scopes, "user_scopes": user_scopes},
                        request_id=request_id,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return False, None
            
            # Log successful access
            await self._audit_logger.log_integration_accessed(
                user_id=user_id,
                integration_name=integration_name,
                agent_name=agent_name,
                scopes_used=required_scopes or credentials.get('scopes', []),
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, credentials
            
        except Exception as e:
            logger.error(f"Failed to validate integration access: {e}")
            await self._audit_logger.log_security_event(
                user_id=user_id,
                integration_name=integration_name,
                description=f"Error validating integration access: {str(e)}",
                severity=IntegrationAuditSeverity.CRITICAL,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return False, None
    
    async def make_integration_api_call(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        endpoint: str,
        method: str = "GET",
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        required_scopes: List[str] = None,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Make authenticated API call to integration on behalf of user"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        request_id = request_id or str(uuid.uuid4())
        
        try:
            # Validate integration access
            has_access, credentials = await self.validate_integration_access(
                user_id, integration_name, agent_name, required_scopes, request_id, ip_address, user_agent
            )
            
            if not has_access:
                return {
                    "success": False,
                    "error": "Agent does not have permission to access this integration",
                    "request_id": request_id
                }
            
            # Get integration configuration
            config = self._config_manager.get_config(integration_name)
            
            # Prepare API call
            url = f"{config.api_base_url}{endpoint}"
            headers = self._prepare_headers(integration_name, credentials)
            
            # Make API call
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data, params=params, timeout=30.0)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data, params=params, timeout=30.0)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params, timeout=30.0)
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported HTTP method: {method}",
                        "request_id": request_id
                    }
            
            duration_ms = int((time.time() - start_time) * 1000)
            success = 200 <= response.status_code < 300
            
            # Log API call
            await self._audit_logger.log_api_call(
                user_id=user_id,
                integration_name=integration_name,
                agent_name=agent_name,
                api_endpoint=endpoint,
                method=method,
                success=success,
                response_code=response.status_code,
                error_message=response.text if not success else None,
                scopes_used=required_scopes or credentials.get('scopes', []),
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )
            
            if success:
                return {
                    "success": True,
                    "data": response.json() if response.content else {},
                    "status_code": response.status_code,
                    "request_id": request_id,
                    "duration_ms": duration_ms
                }
            else:
                return {
                    "success": False,
                    "error": f"API call failed with status {response.status_code}",
                    "response": response.text,
                    "status_code": response.status_code,
                    "request_id": request_id,
                    "duration_ms": duration_ms
                }
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Failed to make integration API call: {e}")
            
            await self._audit_logger.log_api_call(
                user_id=user_id,
                integration_name=integration_name,
                agent_name=agent_name,
                api_endpoint=endpoint,
                method=method,
                success=False,
                error_message=str(e),
                scopes_used=required_scopes or [],
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms
            )
            
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id,
                "duration_ms": duration_ms
            }
    
    def _prepare_headers(self, integration_name: str, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Prepare headers for integration API call"""
        headers = {
            "User-Agent": "Agent47-Integration-Service/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add integration-specific authentication
        if credentials.get('access_token'):
            if integration_name in ['mailchimp', 'hubspot', 'salesforce', 'stripe', 'openai']:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
            elif integration_name in ['convertkit', 'klaviyo', 'mixpanel', 'amplitude']:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
            elif integration_name in ['notion', 'figma', 'canva', 'slack', 'trello', 'asana']:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
            elif integration_name in ['zapier', 'ifttt']:
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
        
        elif credentials.get('api_key'):
            if integration_name == 'google_analytics':
                headers["X-API-Key"] = credentials['api_key']
            elif integration_name in ['wordpress', 'contentful']:
                headers["Authorization"] = f"Bearer {credentials['api_key']}"
            elif integration_name in ['pipedrive', 'paypal']:
                headers["Authorization"] = f"Bearer {credentials['api_key']}"
            elif integration_name in ['grok-llm']:
                headers["X-API-Key"] = credentials['api_key']
        
        elif credentials.get('bearer_token'):
            headers["Authorization"] = f"Bearer {credentials['bearer_token']}"
        
        return headers
    
    async def send_email_campaign(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        campaign_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Send email campaign using integration"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if integration_name == "mailchimp":
                return await self._send_mailchimp_campaign(
                    user_id, agent_name, campaign_data, request_id, ip_address, user_agent
                )
            elif integration_name == "convertkit":
                return await self._send_convertkit_campaign(
                    user_id, agent_name, campaign_data, request_id, ip_address, user_agent
                )
            elif integration_name == "klaviyo":
                return await self._send_klaviyo_campaign(
                    user_id, agent_name, campaign_data, request_id, ip_address, user_agent
                )
            else:
                return {
                    "success": False,
                    "error": f"Email campaigns not supported for {integration_name}",
                    "request_id": request_id
                }
                
        except Exception as e:
            logger.error(f"Failed to send email campaign: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    async def _send_mailchimp_campaign(
        self,
        user_id: int,
        agent_name: str,
        campaign_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Send Mailchimp campaign"""
        campaign_payload = {
            "type": "regular",
            "recipients": {
                "list_id": campaign_data.get("list_id")
            },
            "settings": {
                "subject_line": campaign_data.get("subject"),
                "from_name": campaign_data.get("from_name"),
                "reply_to": campaign_data.get("reply_to")
            }
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="mailchimp",
            agent_name=agent_name,
            endpoint="/campaigns",
            method="POST",
            data=campaign_payload,
            required_scopes=["campaigns:write"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _send_convertkit_campaign(
        self,
        user_id: int,
        agent_name: str,
        campaign_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Send ConvertKit broadcast"""
        broadcast_payload = {
            "email": {
                "subject": campaign_data.get("subject"),
                "from_name": campaign_data.get("from_name"),
                "from_email": campaign_data.get("from_email"),
                "content": campaign_data.get("content")
            },
            "public": False
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="convertkit",
            agent_name=agent_name,
            endpoint="/broadcasts",
            method="POST",
            data=broadcast_payload,
            required_scopes=["broadcasts:write"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _send_klaviyo_campaign(
        self,
        user_id: int,
        agent_name: str,
        campaign_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Send Klaviyo campaign"""
        campaign_payload = {
            "data": {
                "type": "campaign",
                "attributes": {
                    "name": campaign_data.get("name"),
                    "audience": {
                        "included": [campaign_data.get("list_id")]
                    },
                    "message": {
                        "subject": campaign_data.get("subject"),
                        "from_email": campaign_data.get("from_email"),
                        "from_name": campaign_data.get("from_name")
                    }
                }
            }
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="klaviyo",
            agent_name=agent_name,
            endpoint="/campaigns",
            method="POST",
            data=campaign_payload,
            required_scopes=["campaigns:write"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_analytics_data(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        metric_type: str,
        start_date: str,
        end_date: str,
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Get analytics data from integration"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Integration-specific analytics endpoints
            if integration_name == "google_analytics":
                endpoint = "/data/ga"
                params = {
                    "ids": f"ga:{credentials.get('view_id', '')}",
                    "start-date": start_date,
                    "end-date": end_date,
                    "metrics": metric_type
                }
            elif integration_name == "mixpanel":
                endpoint = "/events"
                params = {
                    "from_date": start_date,
                    "to_date": end_date,
                    "event": metric_type
                }
            elif integration_name == "amplitude":
                endpoint = "/2/events"
                params = {
                    "start": start_date,
                    "end": end_date,
                    "event_type": metric_type
                }
            else:
                return {
                    "success": False,
                    "error": f"Analytics for {integration_name} not yet implemented",
                    "request_id": request_id
                }
            
            return await self.make_integration_api_call(
                user_id=user_id,
                integration_name=integration_name,
                agent_name=agent_name,
                endpoint=endpoint,
                method="GET",
                params=params,
                required_scopes=["analytics:read"],
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"Failed to get analytics for {integration_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    async def create_crm_contact(
        self,
        user_id: int,
        integration_name: str,
        agent_name: str,
        contact_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Create CRM contact using integration"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if integration_name == "hubspot":
                return await self._create_hubspot_contact(
                    user_id, agent_name, contact_data, request_id, ip_address, user_agent
                )
            elif integration_name == "salesforce":
                return await self._create_salesforce_contact(
                    user_id, agent_name, contact_data, request_id, ip_address, user_agent
                )
            elif integration_name == "pipedrive":
                return await self._create_pipedrive_contact(
                    user_id, agent_name, contact_data, request_id, ip_address, user_agent
                )
            else:
                return {
                    "success": False,
                    "error": f"CRM contact creation not supported for {integration_name}",
                    "request_id": request_id
                }
                
        except Exception as e:
            logger.error(f"Failed to create CRM contact: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    async def _create_hubspot_contact(
        self,
        user_id: int,
        agent_name: str,
        contact_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Create HubSpot contact"""
        contact_payload = {
            "properties": {
                "email": contact_data.get("email"),
                "firstname": contact_data.get("first_name"),
                "lastname": contact_data.get("last_name"),
                "phone": contact_data.get("phone"),
                "company": contact_data.get("company")
            }
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="hubspot",
            agent_name=agent_name,
            endpoint="/crm/v3/objects/contacts",
            method="POST",
            data=contact_payload,
            required_scopes=["crm.objects.contacts.write"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _create_salesforce_contact(
        self,
        user_id: int,
        agent_name: str,
        contact_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Create Salesforce contact"""
        contact_payload = {
            "FirstName": contact_data.get("first_name"),
            "LastName": contact_data.get("last_name"),
            "Email": contact_data.get("email"),
            "Phone": contact_data.get("phone"),
            "Company": contact_data.get("company")
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="salesforce",
            agent_name=agent_name,
            endpoint="/services/data/v58.0/sobjects/Contact",
            method="POST",
            data=contact_payload,
            required_scopes=["api"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _create_pipedrive_contact(
        self,
        user_id: int,
        agent_name: str,
        contact_data: Dict[str, Any],
        request_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Create Pipedrive person"""
        person_payload = {
            "name": f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
            "email": [{"value": contact_data.get("email"), "primary": True}],
            "phone": [{"value": contact_data.get("phone"), "primary": True}],
            "org_name": contact_data.get("company")
        }
        
        return await self.make_integration_api_call(
            user_id=user_id,
            integration_name="pipedrive",
            agent_name=agent_name,
            endpoint="/persons",
            method="POST",
            data=person_payload,
            required_scopes=["persons:write"],
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def health_check(self) -> bool:
        """Check secure integration service health"""
        try:
            if not self._initialized:
                return False
            
            # Test all dependencies
            config_health = self._config_manager is not None
            credentials_health = self._credentials_manager is not None
            audit_health = self._audit_logger is not None
            encryption_health = self._encryption is not None
            
            return config_health and credentials_health and audit_health and encryption_health
            
        except Exception as e:
            logger.error(f"Secure integration service health check failed: {e}")
            return False

# Global instance
secure_integration_service = SecureIntegrationService()

async def get_secure_integration_service() -> SecureIntegrationService:
    """Get the global secure integration service instance"""
    if not secure_integration_service._initialized:
        await secure_integration_service.initialize()
    return secure_integration_service
