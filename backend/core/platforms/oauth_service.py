import httpx
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse
import logging

from .platform_configs import get_platform_config_manager, PlatformConfig
from .user_platform_tokens import get_user_platform_token_manager
from ..security import get_credential_encryption

logger = logging.getLogger(__name__)

class OAuthService:
    """Handles OAuth 2.0 flows for all supported platforms"""
    
    def __init__(self):
        self._initialized = False
        self._config_manager = None
        self._token_manager = None
        self._encryption = None
    
    async def initialize(self):
        """Initialize OAuth service"""
        if self._initialized:
            return
        
        try:
            self._config_manager = await get_platform_config_manager()
            self._token_manager = await get_user_platform_token_manager()
            self._encryption = await get_credential_encryption()
            self._initialized = True
            
            logger.info("OAuth service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OAuth service: {e}")
            raise
    
    def generate_state(self, user_id: int, platform_name: str) -> str:
        """Generate secure state parameter for OAuth flow"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        # Create state with user_id, platform, and random nonce
        nonce = secrets.token_urlsafe(32)
        state_data = f"{user_id}:{platform_name}:{nonce}"
        
        # Encrypt state for security
        encrypted_state = self._encryption.encrypt_credential(0, "oauth_state", state_data)
        return base64.urlsafe_b64encode(encrypted_state.encode()).decode()
    
    def validate_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate and decode state parameter"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            # Decode and decrypt state
            encrypted_state = base64.urlsafe_b64decode(state.encode()).decode()
            decrypted_state = self._encryption.decrypt_credential(0, "oauth_state", encrypted_state)
            
            # Parse state data
            parts = decrypted_state.split(":")
            if len(parts) != 3:
                return None
            
            user_id, platform_name, nonce = parts
            return {
                "user_id": int(user_id),
                "platform_name": platform_name,
                "nonce": nonce
            }
            
        except Exception as e:
            logger.error(f"Failed to validate OAuth state: {e}")
            return None
    
    def get_authorization_url(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Generate OAuth authorization URL for a platform"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            config = self._config_manager.get_config(platform_name)
            state = self.generate_state(user_id, platform_name)
            
            # Build authorization URL
            params = {
                'client_id': config.client_id,
                'redirect_uri': config.redirect_uri,
                'scope': ' '.join(config.scopes),
                'response_type': 'code',
                'state': state
            }
            
            # Add platform-specific parameters
            if platform_name == "slack":
                params['team'] = ''  # Allow any workspace
            elif platform_name == "shopify":
                params['shop'] = ''  # Will be filled by user
            
            query_string = urlencode(params)
            auth_url = f"{config.auth_url}?{query_string}"
            
            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "platform": platform_name,
                "scopes": config.scopes
            }
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL for {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def exchange_code_for_tokens(
        self, 
        platform_name: str, 
        code: str, 
        state: str,
        additional_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            # Validate state
            state_data = self.validate_state(state)
            if not state_data:
                return {"success": False, "error": "Invalid state parameter"}
            
            user_id = state_data["user_id"]
            config = self._config_manager.get_config(platform_name)
            
            # Prepare token exchange request
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': config.redirect_uri,
                'client_id': config.client_id,
                'client_secret': config.client_secret
            }
            
            # Add platform-specific parameters
            if additional_params:
                token_data.update(additional_params)
            
            # Make token exchange request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config.token_url,
                    data=token_data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token exchange failed for {platform_name}: {error_detail}")
                    return {"success": False, "error": f"Token exchange failed: {error_detail}"}
                
                tokens = response.json()
            
            # Extract platform-specific data
            workspace_id = None
            workspace_name = None
            
            if platform_name == "slack":
                workspace_id = tokens.get("team", {}).get("id")
                workspace_name = tokens.get("team", {}).get("name")
            elif platform_name == "shopify":
                workspace_id = additional_params.get("shop") if additional_params else None
                workspace_name = workspace_id
            
            # Store tokens
            store_result = await self._token_manager.store_tokens(
                user_id=user_id,
                platform_name=platform_name,
                tokens=tokens,
                scopes=config.scopes,
                workspace_id=workspace_id,
                workspace_name=workspace_name
            )
            
            if store_result["success"]:
                logger.info(f"Successfully exchanged code for tokens: user {user_id}, platform {platform_name}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "platform": platform_name,
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_name,
                    "scopes": config.scopes,
                    "expires_at": store_result.get("expires_at")
                }
            else:
                return store_result
                
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return {"success": False, "error": str(e)}
    
    async def refresh_user_tokens(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Refresh user's platform tokens"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            result = await self._token_manager.refresh_tokens(user_id, platform_name)
            
            if result["success"]:
                logger.info(f"Successfully refreshed tokens: user {user_id}, platform {platform_name}")
            else:
                logger.warning(f"Failed to refresh tokens: user {user_id}, platform {platform_name}, error: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to refresh tokens for user {user_id}, platform {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def revoke_user_tokens(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Revoke user's platform tokens"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            result = await self._token_manager.revoke_tokens(user_id, platform_name)
            
            if result["success"]:
                logger.info(f"Successfully revoked tokens: user {user_id}, platform {platform_name}")
            else:
                logger.warning(f"Failed to revoke tokens: user {user_id}, platform {platform_name}, error: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to revoke tokens for user {user_id}, platform {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_platforms(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all connected platforms for a user"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            platforms = await self._token_manager.get_user_platforms(user_id)
            
            # Add platform metadata
            for platform in platforms:
                try:
                    config = self._config_manager.get_config(platform["platform_name"])
                    platform["display_name"] = config.display_name
                    platform["platform_type"] = config.platform_type.value
                    platform["supported_features"] = config.supported_features
                except Exception as e:
                    logger.warning(f"Failed to get config for platform {platform['platform_name']}: {e}")
            
            return platforms
            
        except Exception as e:
            logger.error(f"Failed to get user platforms for user {user_id}: {e}")
            return []
    
    async def validate_platform_access(
        self, 
        user_id: int, 
        platform_name: str, 
        required_scopes: List[str] = None
    ) -> bool:
        """Validate that user has valid access to platform with required scopes"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            return await self._token_manager.validate_token_access(
                user_id, platform_name, required_scopes
            )
            
        except Exception as e:
            logger.error(f"Failed to validate platform access: {e}")
            return False
    
    async def get_platform_token(self, user_id: int, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get decrypted platform token for API calls"""
        if not self._initialized:
            raise RuntimeError("OAuth service not initialized")
        
        try:
            # Check if tokens need refresh
            tokens = await self._token_manager.get_tokens(user_id, platform_name)
            if not tokens:
                return None
            
            # Auto-refresh if needed
            if tokens.get("needs_refresh", False):
                refresh_result = await self.refresh_user_tokens(user_id, platform_name)
                if refresh_result["success"]:
                    tokens = await self._token_manager.get_tokens(user_id, platform_name)
                else:
                    logger.warning(f"Failed to refresh tokens for user {user_id}, platform {platform_name}")
                    return None
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get platform token: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check OAuth service health"""
        try:
            if not self._initialized:
                return False
            
            # Test encryption
            if not self._encryption.validate_encryption_key():
                return False
            
            # Test config manager
            configs = self._config_manager.get_all_configs()
            if not configs:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"OAuth service health check failed: {e}")
            return False

# Global instance
oauth_service = OAuthService()

async def get_oauth_service() -> OAuthService:
    """Get the global OAuth service instance"""
    if not oauth_service._initialized:
        await oauth_service.initialize()
    return oauth_service
