from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .models import IntegrationCredentials, Integration, CredentialStatus
from ..security import get_credential_encryption

logger = logging.getLogger(__name__)

class IntegrationCredentialsManager:
    """Manages user integration credentials with encryption and validation"""
    
    def __init__(self):
        self._initialized = False
        self._encryption = None
    
    async def initialize(self):
        """Initialize the credentials manager"""
        if self._initialized:
            return
        
        try:
            self._encryption = await get_credential_encryption()
            self._initialized = True
            
            logger.info("Integration credentials manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize integration credentials manager: {e}")
            raise
    
    async def store_credentials(
        self, 
        user_id: int, 
        integration_name: str, 
        credentials_data: Dict[str, Any],
        scopes: List[str] = None
    ) -> Dict[str, Any]:
        """Store encrypted integration credentials for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            db = get_database()
            async with db.get_session() as session:
                # Get integration ID
                integration_query = select(Integration).where(Integration.name == integration_name)
                integration_result = await session.execute(integration_query)
                integration = integration_result.scalar_one_or_none()
                
                if not integration:
                    return {"success": False, "error": "Integration not found"}
                
                # Encrypt sensitive credentials
                encrypted_credentials = self._encryption.encrypt_credentials_dict(
                    user_id, integration_name, credentials_data
                )
                
                # Check if credentials already exist for this user/integration
                existing_query = select(IntegrationCredentials).where(
                    and_(
                        IntegrationCredentials.user_id == user_id,
                        IntegrationCredentials.integration_id == integration.id
                    )
                )
                existing_result = await session.execute(existing_query)
                existing_credentials = existing_result.scalar_one_or_none()
                
                if existing_credentials:
                    # Update existing credentials
                    existing_credentials.api_key = encrypted_credentials.get('api_key')
                    existing_credentials.api_secret = encrypted_credentials.get('api_secret')
                    existing_credentials.access_token = encrypted_credentials.get('access_token')
                    existing_credentials.refresh_token = encrypted_credentials.get('refresh_token')
                    existing_credentials.bearer_token = encrypted_credentials.get('bearer_token')
                    existing_credentials.scopes = scopes or []
                    existing_credentials.status = CredentialStatus.valid
                    existing_credentials.last_updated = datetime.utcnow()
                    
                    # Set expiration if provided
                    if 'expires_in' in credentials_data:
                        expires_in = credentials_data['expires_in']
                        existing_credentials.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    credentials = existing_credentials
                else:
                    # Create new credentials
                    credentials = IntegrationCredentials(
                        user_id=user_id,
                        integration_id=integration.id,
                        api_key=encrypted_credentials.get('api_key'),
                        api_secret=encrypted_credentials.get('api_secret'),
                        access_token=encrypted_credentials.get('access_token'),
                        refresh_token=encrypted_credentials.get('refresh_token'),
                        bearer_token=encrypted_credentials.get('bearer_token'),
                        scopes=scopes or [],
                        status=CredentialStatus.valid
                    )
                    
                    # Set expiration if provided
                    if 'expires_in' in credentials_data:
                        expires_in = credentials_data['expires_in']
                        credentials.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    session.add(credentials)
                
                await session.commit()
                
                logger.info(f"Stored credentials for user {user_id}, integration {integration_name}")
                
                return {
                    "success": True,
                    "credentials_id": credentials.id,
                    "integration": integration_name,
                    "status": "stored",
                    "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to store credentials for user {user_id}, integration {integration_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_credentials(self, user_id: int, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials for a user and integration"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            db = get_database()
            async with db.get_session() as session:
                query = select(IntegrationCredentials, Integration).join(Integration).where(
                    and_(
                        IntegrationCredentials.user_id == user_id,
                        Integration.name == integration_name,
                        IntegrationCredentials.status == CredentialStatus.valid
                    )
                )
                result = await session.execute(query)
                credentials_record = result.first()
                
                if not credentials_record:
                    return None
                
                credentials, integration = credentials_record
                
                # Check if credentials are expired
                if credentials.expires_at and credentials.expires_at < datetime.utcnow():
                    credentials.status = CredentialStatus.expired
                    await session.commit()
                    return None
                
                # Decrypt credentials
                encrypted_credentials = {
                    'api_key': credentials.api_key,
                    'api_secret': credentials.api_secret,
                    'access_token': credentials.access_token,
                    'refresh_token': credentials.refresh_token,
                    'bearer_token': credentials.bearer_token
                }
                
                decrypted_credentials = self._encryption.decrypt_credentials_dict(
                    user_id, integration_name, encrypted_credentials
                )
                
                # Update last used timestamp
                credentials.last_used = datetime.utcnow()
                await session.commit()
                
                return {
                    **decrypted_credentials,
                    'scopes': credentials.scopes,
                    'expires_at': credentials.expires_at.isoformat() if credentials.expires_at else None,
                    'needs_refresh': self._needs_refresh(credentials)
                }
                
        except Exception as e:
            logger.error(f"Failed to get credentials for user {user_id}, integration {integration_name}: {e}")
            return None
    
    def _needs_refresh(self, credentials: IntegrationCredentials) -> bool:
        """Check if credentials need refresh (expires within 1 hour)"""
        if not credentials.expires_at:
            return False
        refresh_threshold = datetime.utcnow() + timedelta(hours=1)
        return refresh_threshold > credentials.expires_at.replace(tzinfo=None)
    
    async def refresh_credentials(self, user_id: int, integration_name: str) -> Dict[str, Any]:
        """Refresh expired credentials using refresh token"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            import httpx
            
            db = get_database()
            async with db.get_session() as session:
                query = select(IntegrationCredentials, Integration).join(Integration).where(
                    and_(
                        IntegrationCredentials.user_id == user_id,
                        Integration.name == integration_name,
                        IntegrationCredentials.status == CredentialStatus.valid
                    )
                )
                result = await session.execute(query)
                credentials_record = result.first()
                
                if not credentials_record:
                    return {"success": False, "error": "No credentials found"}
                
                credentials, integration = credentials_record
                
                if not credentials.refresh_token:
                    return {"success": False, "error": "No refresh token available"}
                
                # Decrypt refresh token
                decrypted_refresh_token = self._encryption.decrypt_credential(
                    user_id, integration_name, credentials.refresh_token
                )
                
                # Get integration config for refresh
                from .integration_configs import get_integration_config_manager
                config_manager = await get_integration_config_manager()
                config = config_manager.get_config(integration_name)
                
                if not config.supports_oauth or not config.token_url:
                    return {"success": False, "error": "Integration does not support token refresh"}
                
                # Prepare refresh request
                refresh_data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': decrypted_refresh_token,
                    'client_id': f"{integration_name.upper()}_CLIENT_ID",  # Would come from settings
                    'client_secret': f"{integration_name.upper()}_CLIENT_SECRET"  # Would come from settings
                }
                
                # Make refresh request
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        config.token_url,
                        data=refresh_data,
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        credentials.status = CredentialStatus.invalid
                        await session.commit()
                        return {"success": False, "error": f"Refresh failed: {response.text}"}
                    
                    new_credentials = response.json()
                
                # Store new credentials
                store_result = await self.store_credentials(
                    user_id, integration_name, new_credentials, credentials.scopes
                )
                
                if store_result["success"]:
                    logger.info(f"Refreshed credentials for user {user_id}, integration {integration_name}")
                    return {"success": True, "message": "Credentials refreshed successfully"}
                else:
                    return store_result
                
        except Exception as e:
            logger.error(f"Failed to refresh credentials for user {user_id}, integration {integration_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def revoke_credentials(self, user_id: int, integration_name: str) -> Dict[str, Any]:
        """Revoke user's integration credentials"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            db = get_database()
            async with db.get_session() as session:
                query = select(IntegrationCredentials, Integration).join(Integration).where(
                    and_(
                        IntegrationCredentials.user_id == user_id,
                        Integration.name == integration_name
                    )
                )
                result = await session.execute(query)
                credentials_record = result.first()
                
                if credentials_record:
                    credentials, integration = credentials_record
                    credentials.status = CredentialStatus.revoked
                    await session.commit()
                    
                    logger.info(f"Revoked credentials for user {user_id}, integration {integration_name}")
                    return {"success": True, "message": "Credentials revoked successfully"}
                else:
                    return {"success": False, "error": "No credentials found to revoke"}
                
        except Exception as e:
            logger.error(f"Failed to revoke credentials for user {user_id}, integration {integration_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_integrations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all connected integrations for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            db = get_database()
            async with db.get_session() as session:
                query = select(IntegrationCredentials, Integration).join(Integration).where(
                    and_(
                        IntegrationCredentials.user_id == user_id,
                        IntegrationCredentials.status == CredentialStatus.valid
                    )
                )
                result = await session.execute(query)
                credentials_list = result.all()
                
                integrations = []
                for credentials, integration in credentials_list:
                    integrations.append({
                        "id": credentials.id,
                        "integration_name": integration.name,
                        "integration_display_name": integration.display_name,
                        "integration_type": integration.integration_type.value,
                        "scopes": credentials.scopes,
                        "status": credentials.status.value,
                        "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                        "last_used": credentials.last_used.isoformat() if credentials.last_used else None,
                        "created_at": credentials.created_at.isoformat() if credentials.created_at else None,
                        "last_updated": credentials.last_updated.isoformat() if credentials.last_updated else None
                    })
                
                return integrations
                
        except Exception as e:
            logger.error(f"Failed to get user integrations for user {user_id}: {e}")
            return []
    
    async def validate_credential_access(self, user_id: int, integration_name: str, required_scopes: List[str] = None) -> bool:
        """Validate that user has valid credentials with required scopes"""
        if not self._initialized:
            await self.initialize()
        
        try:
            credentials = await self.get_user_credentials(user_id, integration_name)
            if not credentials:
                return False
            
            # Check scopes if required
            if required_scopes:
                user_scopes = credentials.get('scopes', [])
                if not all(scope in user_scopes for scope in required_scopes):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate credential access for user {user_id}, integration {integration_name}: {e}")
            return False

# Global instance
integration_credentials_manager = IntegrationCredentialsManager()

async def get_integration_credentials_manager() -> IntegrationCredentialsManager:
    """Get the global integration credentials manager instance"""
    if not integration_credentials_manager._initialized:
        await integration_credentials_manager.initialize()
    return integration_credentials_manager
