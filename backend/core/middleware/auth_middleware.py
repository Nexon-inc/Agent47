from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract user information from JWT tokens and set in headers.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
    
    async def dispatch(self, request: Request, call_next):
        # Skip JWT decoding for admin routes - they use session-based auth
        path = request.url.path
        if path.startswith("/api/v1/admin"):
            # Admin routes use their own authentication system
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            try:
                # Decode JWT token
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                
                # Extract user information
                user_id = payload.get("sub")
                user_tier = payload.get("tier")
                user_email = payload.get("email")
                
                # Check if user should get PRO tier (whitelist or admin)
                if user_email:
                    try:
                        from ..authentication.auth_manager import should_get_pro_tier
                        if await should_get_pro_tier(user_email):
                            user_tier = "pro"
                            from ..database import get_database
                            from ..database.models import User, UserTier
                            from sqlalchemy import select
                            db = await get_database()
                            async with db.get_session() as session:
                                result = await session.execute(select(User).where(User.email == user_email))
                                db_user = result.scalar_one_or_none()
                                if db_user and db_user.tier != UserTier.PRO:
                                    db_user.tier = UserTier.PRO
                                    await session.commit()
                                    logger.info(f"Set PRO tier for user in auth middleware: {user_email}")
                    except Exception:
                        pass
                
                # Set user information in headers for downstream middleware
                if user_id:
                    request.state.user_id = user_id
                if user_tier:
                    request.state.user_tier = str(user_tier)
                if user_email:
                    request.state.user_email = user_email
                    
            except JWTError as e:
                # Only log if it's not an admin token (admin tokens are verified separately)
                if not path.startswith("/api/v1/admin"):
                    logger.warning(f"JWT decode error: {e}")
                # Don't fail the request, just don't set user headers
            except Exception as e:
                logger.error(f"Auth middleware error: {e}")
                # Don't fail the request, just don't set user headers
        
        return await call_next(request)
