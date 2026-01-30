from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..database.models import UserPlatformToken, TokenStatus

logger = logging.getLogger(__name__)

class UserPlatformTokenManager:
    """Manages user platform tokens with encryption and validation"""
    
    def __init__(self):
        self._initialized = False
        self._encryption = None
        self._config_manager = None
    
    async def initialize(self):
        """Initialize the token manager"""
        if self._initialized:
            return
        
        try:
            from ..security import get_credential_encryption
            from .platform_configs import get_platform_config_manager
            from ..database.connection import get_database
            
            self._encryption = await get_credential_encryption()
            self._config_manager = await get_platform_config_manager()
            self._initialized = True
            
            logger.info("User platform token manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize user platform token manager: {e}")
            raise
    
    async def store_tokens(
        self, 
        user_id: int, 
        platform_name: str, 
        tokens: Dict[str, Any],
        scopes: List[str] = None,
        workspace_id: str = None,
        workspace_name: str = None
    ) -> Dict[str, Any]:
        """Store encrypted platform tokens for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            from ..database.connection import get_supabase
            db = await get_supabase()
            async with db.get_session() as session:
                # Get platform config to validate
                config = self._config_manager.get_config(platform_name)
                
                # Encrypt sensitive tokens
                encrypted_tokens = self._encryption.encrypt_credentials_dict(
                    user_id, platform_name, tokens
                )
                
                # Check if tokens already exist for this user/platform
                existing_query = select(UserPlatformToken).where(
                    and_(
                        UserPlatformToken.user_id == user_id,
                        UserPlatformToken.platform_name == platform_name
                    )
                )
                existing_result = await session.execute(existing_query)
                existing_token = existing_result.scalar_one_or_none()
                
                if existing_token:
                    # Update existing tokens
                    existing_token.access_token = encrypted_tokens.get('access_token')
                    existing_token.refresh_token = encrypted_tokens.get('refresh_token')
                    existing_token.api_key = encrypted_tokens.get('api_key')
                    existing_token.api_secret = encrypted_tokens.get('api_secret')
                    existing_token.bearer_token = encrypted_tokens.get('bearer_token')
                    existing_token.scopes = scopes or []
                    existing_token.workspace_id = workspace_id
                    existing_token.workspace_name = workspace_name
                    existing_token.status = TokenStatus.ACTIVE
                    existing_token.last_refreshed = datetime.utcnow()
                    
                    # Set expiration if provided
                    if 'expires_in' in tokens:
                        expires_in = tokens['expires_in']
                        existing_token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    token_record = existing_token
                else:
                    # Create new token record
                    token_record = UserPlatformToken(
                        user_id=user_id,
                        platform_name=platform_name,
                        access_token=encrypted_tokens.get('access_token'),
                        refresh_token=encrypted_tokens.get('refresh_token'),
                        api_key=encrypted_tokens.get('api_key'),
                        api_secret=encrypted_tokens.get('api_secret'),
                        bearer_token=encrypted_tokens.get('bearer_token'),
                        scopes=scopes or [],
                        workspace_id=workspace_id,
                        workspace_name=workspace_name,
                        status=TokenStatus.ACTIVE
                    )
                    
                    # Set expiration if provided
                    if 'expires_in' in tokens:
                        expires_in = tokens['expires_in']
                        token_record.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    session.add(token_record)
                
                await session.commit()
                
                logger.info(f"Stored tokens for user {user_id}, platform {platform_name}")
                
                return {
                    "success": True,
                    "token_id": token_record.id,
                    "platform": platform_name,
                    "status": "stored",
                    "expires_at": token_record.expires_at.isoformat() if token_record.expires_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to store tokens for user {user_id}, platform {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_tokens(self, user_id: int, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get decrypted tokens for a user and platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            from ..database.connection import get_supabase
            db = await get_supabase()
            async with db.get_session() as session:
                query = select(UserPlatformToken).where(
                    and_(
                        UserPlatformToken.user_id == user_id,
                        UserPlatformToken.platform_name == platform_name,
                        UserPlatformToken.status == TokenStatus.ACTIVE
                    )
                )
                result = await session.execute(query)
                token_record = result.scalar_one_or_none()
                
                if not token_record:
                    return None
                
                # Check if token is expired
                if token_record.is_expired():
                    token_record.status = TokenStatus.EXPIRED
                    await session.commit()
                    return None
                
                # Decrypt tokens
                encrypted_tokens = {
                    'access_token': token_record.access_token,
                    'refresh_token': token_record.refresh_token,
                    'api_key': token_record.api_key,
                    'api_secret': token_record.api_secret,
                    'bearer_token': token_record.bearer_token
                }
                
                decrypted_tokens = self._encryption.decrypt_credentials_dict(
                    user_id, platform_name, encrypted_tokens
                )
                
                # Update last used timestamp
                token_record.last_used = datetime.utcnow()
                await session.commit()
                
                return {
                    **decrypted_tokens,
                    'scopes': token_record.scopes,
                    'workspace_id': token_record.workspace_id,
                    'workspace_name': token_record.workspace_name,
                    'expires_at': token_record.expires_at.isoformat() if token_record.expires_at else None,
                    'needs_refresh': token_record.needs_refresh()
                }
                
        except Exception as e:
            logger.error(f"Failed to get tokens for user {user_id}, platform {platform_name}: {e}")
            return None
    
    async def refresh_tokens(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Refresh expired tokens using refresh token"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            import httpx
            
            from ..database.connection import get_supabase
            db = await get_supabase()
            async with db.get_session() as session:
                query = select(UserPlatformToken).where(
                    and_(
                        UserPlatformToken.user_id == user_id,
                        UserPlatformToken.platform_name == platform_name,
                        UserPlatformToken.status == TokenStatus.ACTIVE
                    )
                )
                result = await session.execute(query)
                token_record = result.scalar_one_or_none()
                
                if not token_record or not token_record.refresh_token:
                    return {"success": False, "error": "No refresh token available"}
                
                # Get platform config
                config = self._config_manager.get_config(platform_name)
                
                if not config.supports_refresh:
                    return {"success": False, "error": "Platform does not support token refresh"}
                
                # Decrypt refresh token
                decrypted_refresh_token = self._encryption.decrypt_credential(
                    user_id, platform_name, token_record.refresh_token
                )
                
                # Prepare refresh request
                refresh_data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': decrypted_refresh_token,
                    'client_id': config.client_id,
                    'client_secret': config.client_secret
                }
                
                # Make refresh request
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        config.token_url,
                        data=refresh_data,
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        token_record.status = TokenStatus.INVALID
                        await session.commit()
                        return {"success": False, "error": f"Refresh failed: {response.text}"}
                    
                    new_tokens = response.json()
                
                # Store new tokens
                store_result = await self.store_tokens(
                    user_id, platform_name, new_tokens, 
                    token_record.scopes, token_record.workspace_id, token_record.workspace_name
                )
                
                if store_result["success"]:
                    logger.info(f"Refreshed tokens for user {user_id}, platform {platform_name}")
                    return {"success": True, "message": "Tokens refreshed successfully"}
                else:
                    return store_result
                
        except Exception as e:
            logger.error(f"Failed to refresh tokens for user {user_id}, platform {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def revoke_tokens(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Revoke user's platform tokens"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            from ..database.connection import get_supabase
            db = await get_supabase()
            async with db.get_session() as session:
                query = select(UserPlatformToken).where(
                    and_(
                        UserPlatformToken.user_id == user_id,
                        UserPlatformToken.platform_name == platform_name
                    )
                )
                result = await session.execute(query)
                token_record = result.scalar_one_or_none()
                
                if token_record:
                    token_record.status = TokenStatus.REVOKED
                    await session.commit()
                    
                    logger.info(f"Revoked tokens for user {user_id}, platform {platform_name}")
                    return {"success": True, "message": "Tokens revoked successfully"}
                else:
                    return {"success": False, "error": "No tokens found to revoke"}
                
        except Exception as e:
            logger.error(f"Failed to revoke tokens for user {user_id}, platform {platform_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_platforms(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all connected platforms for a user"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from ..database.connection import get_database
            from sqlalchemy import select, and_
            
            from ..database.connection import get_supabase
            db = await get_supabase()
            async with db.get_session() as session:
                query = select(UserPlatformToken).where(
                    and_(
                        UserPlatformToken.user_id == user_id,
                        UserPlatformToken.status == TokenStatus.ACTIVE
                    )
                )
                result = await session.execute(query)
                tokens = result.scalars().all()
                
                platforms = []
                for token in tokens:
                    platforms.append(token.to_dict())
                
                return platforms
                
        except Exception as e:
            logger.error(f"Failed to get user platforms for user {user_id}: {e}")
            return []
    
    async def validate_token_access(self, user_id: int, platform_name: str, required_scopes: List[str] = None) -> bool:
        """Validate that user has valid tokens with required scopes"""
        if not self._initialized:
            await self.initialize()
        
        try:
            tokens = await self.get_tokens(user_id, platform_name)
            if not tokens:
                return False
            
            # Check scopes if required
            if required_scopes:
                user_scopes = tokens.get('scopes', [])
                if not all(scope in user_scopes for scope in required_scopes):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate token access for user {user_id}, platform {platform_name}: {e}")
            return False

# Global instance
user_platform_token_manager = UserPlatformTokenManager()

async def get_user_platform_token_manager() -> UserPlatformTokenManager:
    """Get the global user platform token manager instance"""
    if not user_platform_token_manager._initialized:
        await user_platform_token_manager.initialize()
    return user_platform_token_manager
