"""
Groq Rate Limiter Service

This module provides centralized rate limiting for Groq API services (LLM, TTS, STT).
Supports Redis-based rate limiting with in-memory fallback.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..config import settings
from ..logs import get_logger

logger = get_logger(__name__)


class ServiceType(str, Enum):
    """Groq service types"""
    LLM = "llm"
    TTS = "tts"
    STT = "stt"


class GroqRateLimiter:
    """Centralized rate limiter for Groq API services"""
    
    def __init__(self):
        self.redis_client = None
        self._use_redis = False
        self._initialized = False
        
        # In-memory storage as fallback
        self._in_memory_storage: Dict[str, Dict[str, Any]] = {}
        
        # Rate limits per service (from config)
        self._rate_limits = {
            ServiceType.LLM: {
                "per_minute": settings.groq.groq_rate_limit_per_minute,
                "per_day": settings.groq.groq_rate_limit_per_day
            },
            ServiceType.TTS: {
                "per_minute": settings.groq.groq_tts_rate_limit_per_minute,
                "per_day": settings.groq.groq_tts_rate_limit_per_day
            },
            ServiceType.STT: {
                "per_minute": settings.groq.groq_stt_rate_limit_per_minute,
                "per_day": settings.groq.groq_stt_rate_limit_per_day
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize rate limiter with Redis if available"""
        try:
            # Try to initialize Redis connection
            try:
                from ..cache.redis_manager import get_redis_client
                self.redis_client = await get_redis_client()
                if self.redis_client:
                    # Test Redis connection
                    await self.redis_client.ping()
                    self._use_redis = True
                    logger.info("Groq Rate Limiter initialized with Redis")
            except Exception as e:
                logger.warning(f"Redis not available for rate limiting: {e}. Using in-memory storage.")
                self._use_redis = False
                self.redis_client = None
            
            self._initialized = True
            logger.info("Groq Rate Limiter initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq Rate Limiter: {e}")
            self._use_redis = False
            self._initialized = True  # Still allow in-memory operation
            return True
    
    def _get_redis_key(self, service_type: ServiceType, user_id: Optional[int], key_type: str) -> str:
        """Generate Redis key for rate limiting"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        if user_id:
            return f"groq:rate_limit:{service_type.value}:{user_id}:{key_type}:{date_str}"
        else:
            return f"groq:rate_limit:{service_type.value}:global:{key_type}:{date_str}"
    
    def _get_memory_key(self, service_type: ServiceType, user_id: Optional[int], key_type: str) -> str:
        """Generate in-memory key for rate limiting"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        if user_id:
            return f"{service_type.value}:{user_id}:{key_type}:{date_str}"
        else:
            return f"{service_type.value}:global:{key_type}:{date_str}"
    
    async def check_rate_limit(
        self,
        service_type: ServiceType,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check if rate limit is exceeded
        
        Returns:
            Tuple of (allowed, error_message, usage_stats)
        """
        if not self._initialized:
            await self.initialize()
        
        limits = self._rate_limits.get(service_type, {"per_minute": 30, "per_day": 1000})
        current_time = time.time()
        current_minute = int(current_time / 60)
        
        if self._use_redis and self.redis_client:
            return await self._check_rate_limit_redis(service_type, user_id, limits, current_minute)
        else:
            return await self._check_rate_limit_memory(service_type, user_id, limits, current_minute)
    
    async def _check_rate_limit_redis(
        self,
        service_type: ServiceType,
        user_id: Optional[int],
        limits: Dict[str, int],
        current_minute: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check rate limit using Redis"""
        try:
            # Daily limit check
            daily_key = self._get_redis_key(service_type, user_id, "daily")
            daily_count = await self.redis_client.get(daily_key)
            daily_count = int(daily_count) if daily_count else 0
            
            if daily_count >= limits["per_day"]:
                return False, f"Daily rate limit exceeded ({daily_count}/{limits['per_day']})", {
                    "daily_used": daily_count,
                    "daily_limit": limits["per_day"],
                    "per_minute_used": 0,
                    "per_minute_limit": limits["per_minute"]
                }
            
            # Per-minute limit check
            minute_key = self._get_redis_key(service_type, user_id, f"minute:{current_minute}")
            minute_count = await self.redis_client.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0
            
            if minute_count >= limits["per_minute"]:
                return False, f"Rate limit exceeded: {minute_count} requests in the last minute", {
                    "daily_used": daily_count,
                    "daily_limit": limits["per_day"],
                    "per_minute_used": minute_count,
                    "per_minute_limit": limits["per_minute"]
                }
            
            return True, None, {
                "daily_used": daily_count,
                "daily_limit": limits["per_day"],
                "per_minute_used": minute_count,
                "per_minute_limit": limits["per_minute"]
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            # Fallback to memory
            return await self._check_rate_limit_memory(service_type, user_id, limits, current_minute)
    
    async def _check_rate_limit_memory(
        self,
        service_type: ServiceType,
        user_id: Optional[int],
        limits: Dict[str, int],
        current_minute: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check rate limit using in-memory storage"""
        daily_key = self._get_memory_key(service_type, user_id, "daily")
        minute_key = self._get_memory_key(service_type, user_id, f"minute:{current_minute}")
        
        # Get or initialize counters
        if daily_key not in self._in_memory_storage:
            self._in_memory_storage[daily_key] = {
                "count": 0,
                "date": datetime.utcnow().date()
            }
        
        # Reset daily counter if new day
        stored_date = self._in_memory_storage[daily_key].get("date")
        if stored_date != datetime.utcnow().date():
            self._in_memory_storage[daily_key] = {
                "count": 0,
                "date": datetime.utcnow().date()
            }
        
        daily_count = self._in_memory_storage[daily_key]["count"]
        
        if daily_count >= limits["per_day"]:
            return False, f"Daily rate limit exceeded ({daily_count}/{limits['per_day']})", {
                "daily_used": daily_count,
                "daily_limit": limits["per_day"],
                "per_minute_used": 0,
                "per_minute_limit": limits["per_minute"]
            }
        
        # Per-minute limit
        if minute_key not in self._in_memory_storage:
            self._in_memory_storage[minute_key] = {
                "count": 0,
                "minute": current_minute
            }
        
        # Reset minute counter if new minute
        stored_minute = self._in_memory_storage[minute_key].get("minute")
        if stored_minute != current_minute:
            self._in_memory_storage[minute_key] = {
                "count": 0,
                "minute": current_minute
            }
        
        minute_count = self._in_memory_storage[minute_key]["count"]
        
        if minute_count >= limits["per_minute"]:
            return False, f"Rate limit exceeded: {minute_count} requests in the last minute", {
                "daily_used": daily_count,
                "daily_limit": limits["per_day"],
                "per_minute_used": minute_count,
                "per_minute_limit": limits["per_minute"]
            }
        
        return True, None, {
            "daily_used": daily_count,
            "daily_limit": limits["per_day"],
            "per_minute_used": minute_count,
            "per_minute_limit": limits["per_minute"]
        }
    
    async def record_usage(
        self,
        service_type: ServiceType,
        user_id: Optional[int] = None,
        tokens: int = 0
    ) -> Dict[str, Any]:
        """Record API usage
        
        Args:
            service_type: Type of service (LLM, TTS, STT)
            user_id: Optional user ID for per-user tracking
            tokens: Number of tokens used (for LLM)
        
        Returns:
            Updated usage statistics
        """
        if not self._initialized:
            await self.initialize()
        
        current_time = time.time()
        current_minute = int(current_time / 60)
        
        if self._use_redis and self.redis_client:
            return await self._record_usage_redis(service_type, user_id, tokens, current_minute)
        else:
            return await self._record_usage_memory(service_type, user_id, tokens, current_minute)
    
    async def _record_usage_redis(
        self,
        service_type: ServiceType,
        user_id: Optional[int],
        tokens: int,
        current_minute: int
    ) -> Dict[str, Any]:
        """Record usage in Redis"""
        try:
            # Increment daily counter
            daily_key = self._get_redis_key(service_type, user_id, "daily")
            daily_count = await self.redis_client.incr(daily_key)
            
            # Set expiration to end of day (UTC)
            now = datetime.utcnow()
            end_of_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            ttl = int((end_of_day - now).total_seconds())
            await self.redis_client.expire(daily_key, ttl)
            
            # Increment per-minute counter
            minute_key = self._get_redis_key(service_type, user_id, f"minute:{current_minute}")
            minute_count = await self.redis_client.incr(minute_key)
            await self.redis_client.expire(minute_key, 60)  # Expire after 1 minute
            
            limits = self._rate_limits.get(service_type, {"per_minute": 30, "per_day": 1000})
            
            return {
                "daily_used": daily_count,
                "daily_limit": limits["per_day"],
                "per_minute_used": minute_count,
                "per_minute_limit": limits["per_minute"],
                "tokens_used": tokens
            }
            
        except Exception as e:
            logger.error(f"Redis usage recording error: {e}")
            # Fallback to memory
            return await self._record_usage_memory(service_type, user_id, tokens, current_minute)
    
    async def _record_usage_memory(
        self,
        service_type: ServiceType,
        user_id: Optional[int],
        tokens: int,
        current_minute: int
    ) -> Dict[str, Any]:
        """Record usage in memory"""
        daily_key = self._get_memory_key(service_type, user_id, "daily")
        minute_key = self._get_memory_key(service_type, user_id, f"minute:{current_minute}")
        
        # Initialize if needed
        if daily_key not in self._in_memory_storage:
            self._in_memory_storage[daily_key] = {
                "count": 0,
                "date": datetime.utcnow().date()
            }
        
        # Reset if new day
        stored_date = self._in_memory_storage[daily_key].get("date")
        if stored_date != datetime.utcnow().date():
            self._in_memory_storage[daily_key] = {
                "count": 0,
                "date": datetime.utcnow().date()
            }
        
        # Increment daily counter
        self._in_memory_storage[daily_key]["count"] += 1
        daily_count = self._in_memory_storage[daily_key]["count"]
        
        # Initialize minute counter if needed
        if minute_key not in self._in_memory_storage:
            self._in_memory_storage[minute_key] = {
                "count": 0,
                "minute": current_minute
            }
        
        # Reset if new minute
        stored_minute = self._in_memory_storage[minute_key].get("minute")
        if stored_minute != current_minute:
            self._in_memory_storage[minute_key] = {
                "count": 0,
                "minute": current_minute
            }
        
        # Increment minute counter
        self._in_memory_storage[minute_key]["count"] += 1
        minute_count = self._in_memory_storage[minute_key]["count"]
        
        limits = self._rate_limits.get(service_type, {"per_minute": 30, "per_day": 1000})
        
        return {
            "daily_used": daily_count,
            "daily_limit": limits["per_day"],
            "per_minute_used": minute_count,
            "per_minute_limit": limits["per_minute"],
            "tokens_used": tokens
        }
    
    async def get_usage_stats(
        self,
        service_type: ServiceType,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current usage statistics"""
        if not self._initialized:
            await self.initialize()
        
        allowed, error, stats = await self.check_rate_limit(service_type, user_id)
        return stats
    
    async def reset_daily_limits(self):
        """Reset daily limits (called at midnight UTC)"""
        if not self._initialized:
            return
        
        try:
            if self._use_redis and self.redis_client:
                # Redis keys expire automatically, but we can clean up old keys
                # This is mainly for in-memory cleanup
                pass
            
            # Clean up old in-memory entries
            current_date = datetime.utcnow().date()
            keys_to_remove = []
            
            for key, value in self._in_memory_storage.items():
                if "daily" in key:
                    stored_date = value.get("date")
                    if stored_date and stored_date < current_date:
                        keys_to_remove.append(key)
                elif "minute" in key:
                    # Remove minute entries older than 2 minutes
                    stored_minute = value.get("minute")
                    current_minute = int(time.time() / 60)
                    if stored_minute and stored_minute < current_minute - 2:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._in_memory_storage[key]
            
            logger.info(f"Reset daily limits: cleaned up {len(keys_to_remove)} old entries")
            
        except Exception as e:
            logger.error(f"Error resetting daily limits: {e}")


# Global instance and lock for thread-safe initialization
_groq_rate_limiter: Optional[GroqRateLimiter] = None
_groq_limiter_lock = asyncio.Lock()

async def get_groq_rate_limiter() -> GroqRateLimiter:
    """Get the global Groq rate limiter instance with thread-safe initialization"""
    global _groq_rate_limiter
    if not _groq_rate_limiter:
        async with _groq_limiter_lock:
            if not _groq_rate_limiter:
                _groq_rate_limiter = GroqRateLimiter()
                await _groq_rate_limiter.initialize()
    return _groq_rate_limiter

