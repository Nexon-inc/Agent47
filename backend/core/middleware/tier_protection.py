from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from jose import jwt, JWTError
from ..config import settings

logger = logging.getLogger(__name__)

class TierProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect agent routes and require tier selection.
    """
    
    def __init__(self, app, protected_paths: list = None):
        super().__init__(app)
        self.protected_paths = protected_paths or [
            "/api/agents/",
            "/dashboard",
            "/admin"
        ]
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Check if the request path is protected
            if any(request.url.path.startswith(path) for path in self.protected_paths):
                # Skip tier validation for health checks and docs
                if any(skip_path in request.url.path for skip_path in ["/health", "/docs", "/redoc", "/openapi.json"]):
                    return await call_next(request)
                
                # Get user tier from request state (set by auth middleware)
                user_tier = getattr(request.state, 'user_tier', None)
                
                # If no tier is set, try secondary sources (cookie or decode JWT directly)
                if not user_tier or user_tier == "null" or user_tier == "undefined":
                    # Cookie fallback set by billing endpoints
                    cookie_tier = request.cookies.get("user_tier")
                    if cookie_tier and cookie_tier not in ("null", "undefined"):
                        request.state.user_tier = cookie_tier
                        return await call_next(request)

                    # JWT fallback: decode Authorization header directly
                    auth_header = request.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        token = auth_header.split(" ")[1]
                        try:
                            payload = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
                            claim_tier = payload.get("tier")
                            if claim_tier:
                                request.state.user_tier = str(claim_tier)
                                return await call_next(request)
                        except JWTError:
                            # ignore and proceed to 403 below
                            pass

                    # Still no tier — reject and hint pricing
                    logger.warning(f"User attempted to access protected path {request.url.path} without tier selection")
                    
                    # For API requests, return 403
                    if request.url.path.startswith("/api/"):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Tier selection required. Please select a subscription tier to access this feature.",
                            headers={"X-Redirect-To": "/pricing"}
                        )
                    
                    # For web requests, redirect to pricing
                    return RedirectResponse(
                        url="/pricing?redirect=" + str(request.url.path),
                        status_code=status.HTTP_302_FOUND
                    )
            
            return await call_next(request)
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 403) without modification
            raise
        except Exception as e:
            # Log unexpected errors and return 500
            logger.error(f"Tier protection middleware error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error in tier protection"
            )
