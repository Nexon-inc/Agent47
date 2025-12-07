import time
import hashlib
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from ..cache import get_redis
from ..config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.redis = None
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.rate_limit_per_hour = settings.rate_limit_per_hour
    
    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = await get_redis()
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client"""
        # Try to get user ID from token if authenticated
        user_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                # Decode token to get user ID (simplified)
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
        except:
            pass
        
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Create hash of IP + User-Agent for better identification
        identifier = f"{client_ip}:{user_agent}"
        return f"ip:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    async def _check_rate_limit(self, identifier: str, window: str, limit: int) -> bool:
        """Check if rate limit is exceeded for a specific window"""
        try:
            await self.initialize()
            
            current_time = int(time.time())
            
            if window == "minute":
                window_start = current_time - (current_time % 60)
                key = f"rate_limit:{identifier}:minute:{window_start}"
                ttl = 60
            elif window == "hour":
                window_start = current_time - (current_time % 3600)
                key = f"rate_limit:{identifier}:hour:{window_start}"
                ttl = 3600
            else:
                return True
            
            # Get current count
            current_count = await self.redis.get(key)
            count = int(current_count) if current_count else 0
            
            if count >= limit:
                return False
            
            # Increment count
            await self.redis.increment(key)
            await self.redis.expire(key, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True
    
    async def check_rate_limit(self, request: Request) -> Dict[str, Any]:
        """Check rate limits for a request"""
        try:
            identifier = self._get_client_identifier(request)
            
            # Check minute limit
            minute_allowed = await self._check_rate_limit(
                identifier, "minute", self.rate_limit_per_minute
            )
            
            # Check hour limit
            hour_allowed = await self._check_rate_limit(
                identifier, "hour", self.rate_limit_per_hour
            )
            
            if not minute_allowed:
                return {
                    "allowed": False,
                    "window": "minute",
                    "limit": self.rate_limit_per_minute,
                    "retry_after": 60
                }
            
            if not hour_allowed:
                return {
                    "allowed": False,
                    "window": "hour",
                    "limit": self.rate_limit_per_hour,
                    "retry_after": 3600
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return {"allowed": True}
    
    async def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information for a client"""
        try:
            await self.initialize()
            
            current_time = int(time.time())
            
            # Get minute window info
            minute_start = current_time - (current_time % 60)
            minute_key = f"rate_limit:{identifier}:minute:{minute_start}"
            minute_count = await self.redis.get(minute_key) or 0
            
            # Get hour window info
            hour_start = current_time - (current_time % 3600)
            hour_key = f"rate_limit:{identifier}:hour:{hour_start}"
            hour_count = await self.redis.get(hour_key) or 0
            
            return {
                "minute": {
                    "current": int(minute_count),
                    "limit": self.rate_limit_per_minute,
                    "remaining": max(0, self.rate_limit_per_minute - int(minute_count)),
                    "reset_time": minute_start + 60
                },
                "hour": {
                    "current": int(hour_count),
                    "limit": self.rate_limit_per_hour,
                    "remaining": max(0, self.rate_limit_per_hour - int(hour_count)),
                    "reset_time": hour_start + 3600
                }
            }
            
        except Exception as e:
            logger.error(f"Get rate limit info error: {e}")
            return {}
    
    async def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for a client"""
        try:
            await self.initialize()
            
            current_time = int(time.time())
            
            # Reset minute window
            minute_start = current_time - (current_time % 60)
            minute_key = f"rate_limit:{identifier}:minute:{minute_start}"
            await self.redis.delete(minute_key)
            
            # Reset hour window
            hour_start = current_time - (current_time % 3600)
            hour_key = f"rate_limit:{identifier}:hour:{hour_start}"
            await self.redis.delete(hour_key)
            
            logger.info(f"Rate limit reset for {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False
    
    async def get_all_rate_limits(self) -> Dict[str, Any]:
        """Get all rate limit information"""
        try:
            await self.initialize()
            
            # Get all rate limit keys
            pattern = "rate_limit:*"
            keys = await self.redis.clear_pattern(pattern)
            
            return {
                "total_keys": keys,
                "minute_limit": self.rate_limit_per_minute,
                "hour_limit": self.rate_limit_per_hour
            }
            
        except Exception as e:
            logger.error(f"Get all rate limits error: {e}")
            return {}

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        # Check rate limit
        rate_limit_result = await self.rate_limiter.check_rate_limit(request)
        
        if not rate_limit_result["allowed"]:
            # Rate limit exceeded
            response_data = {
                "error": "Rate limit exceeded",
                "window": rate_limit_result["window"],
                "limit": rate_limit_result["limit"],
                "retry_after": rate_limit_result["retry_after"]
            }
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=response_data
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rate_limit_result["retry_after"])
            response.headers["Retry-After"] = str(rate_limit_result["retry_after"])
            
            return response
        
        # Rate limit check passed, proceed with request
        response = await call_next(request)
        
        # Add rate limit headers to response
        identifier = self.rate_limiter._get_client_identifier(request)
        rate_limit_info = await self.rate_limiter.get_rate_limit_info(identifier)
        
        if rate_limit_info:
            response.headers["X-RateLimit-Limit-Minute"] = str(rate_limit_info["minute"]["limit"])
            response.headers["X-RateLimit-Remaining-Minute"] = str(rate_limit_info["minute"]["remaining"])
            response.headers["X-RateLimit-Reset-Minute"] = str(rate_limit_info["minute"]["reset_time"])
            
            response.headers["X-RateLimit-Limit-Hour"] = str(rate_limit_info["hour"]["limit"])
            response.headers["X-RateLimit-Remaining-Hour"] = str(rate_limit_info["hour"]["remaining"])
            response.headers["X-RateLimit-Reset-Hour"] = str(rate_limit_info["hour"]["reset_time"])
        
        return response

# Global rate limiter instance
rate_limiter = RateLimiter()

async def get_rate_limiter() -> RateLimiter:
    return rate_limiter

async def init_rate_limiter():
    await rate_limiter.initialize()
