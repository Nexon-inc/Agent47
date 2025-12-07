"""
Groq Tier-Based Usage Enforcement

This module provides tier-based usage limits and enforcement for Groq API services.
Tracks usage per user and enforces limits based on their subscription tier.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from ..config import settings
from ..logs import get_logger
from ..database.models import UserTier
from .groq_rate_limiter import ServiceType, get_groq_rate_limiter

logger = get_logger(__name__)


@dataclass
class TierLimits:
    """Usage limits for a specific tier"""
    # LLM limits
    llm_requests_per_day: int
    llm_requests_per_month: int
    llm_tokens_per_month: int
    
    # TTS limits
    tts_requests_per_day: int
    tts_requests_per_month: int
    tts_minutes_per_month: int
    
    # STT limits
    stt_requests_per_day: int
    stt_requests_per_month: int
    stt_minutes_per_month: int
    
    # Combined limits (shared across all services)
    total_requests_per_day: int
    total_requests_per_month: int


class GroqTierEnforcement:
    """Tier-based usage enforcement for Groq API services"""
    
    # Define tier limits
    TIER_LIMITS = {
        UserTier.FREE: TierLimits(
            llm_requests_per_day=50,
            llm_requests_per_month=500,
            llm_tokens_per_month=100000,  # ~100K tokens
            tts_requests_per_day=20,
            tts_requests_per_month=200,
            tts_minutes_per_month=60,  # 60 minutes of audio
            stt_requests_per_day=20,
            stt_requests_per_month=200,
            stt_minutes_per_month=60,  # 60 minutes of transcription
            total_requests_per_day=50,  # Shared across all services
            total_requests_per_month=500
        ),
        UserTier.STARTER: TierLimits(
            llm_requests_per_day=200,
            llm_requests_per_month=5000,
            llm_tokens_per_month=2000000,  # ~2M tokens
            tts_requests_per_day=100,
            tts_requests_per_month=2000,
            tts_minutes_per_month=300,  # 5 hours of audio
            stt_requests_per_day=100,
            stt_requests_per_month=2000,
            stt_minutes_per_month=300,  # 5 hours of transcription
            total_requests_per_day=200,
            total_requests_per_month=5000
        ),
        UserTier.PRO: TierLimits(
            llm_requests_per_day=1000,
            llm_requests_per_month=50000,
            llm_tokens_per_month=10000000,  # ~10M tokens
            tts_requests_per_day=500,
            tts_requests_per_month=10000,
            tts_minutes_per_month=2000,  # ~33 hours of audio
            stt_requests_per_day=500,
            stt_requests_per_month=10000,
            stt_minutes_per_month=2000,  # ~33 hours of transcription
            total_requests_per_day=1000,
            total_requests_per_month=50000
        )
    }
    
    def __init__(self):
        self.rate_limiter = None
        self._initialized = False
        self._redis_client = None
        self._use_redis = False
        
        # In-memory storage as fallback
        self._in_memory_usage: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> bool:
        """Initialize tier enforcement service"""
        try:
            # Initialize rate limiter
            self.rate_limiter = await get_groq_rate_limiter()
            
            # Try to initialize Redis for usage tracking
            try:
                from ..cache.redis_manager import get_redis_client
                self._redis_client = await get_redis_client()
                if self._redis_client:
                    await self._redis_client.ping()
                    self._use_redis = True
                    logger.info("Groq Tier Enforcement initialized with Redis")
            except Exception as e:
                logger.warning(f"Redis not available for tier enforcement: {e}. Using in-memory storage.")
                self._use_redis = False
                self._redis_client = None
            
            self._initialized = True
            logger.info("Groq Tier Enforcement initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq Tier Enforcement: {e}")
            self._initialized = True  # Still allow in-memory operation
            return True
    
    def get_tier_limits(self, tier: Optional[UserTier]) -> TierLimits:
        """Get usage limits for a user tier"""
        user_tier = tier or UserTier.FREE
        return self.TIER_LIMITS.get(user_tier, self.TIER_LIMITS[UserTier.FREE])
    
    def _get_redis_key(self, user_id: int, service_type: ServiceType, period: str) -> str:
        """Generate Redis key for usage tracking"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        month_str = datetime.utcnow().strftime("%Y-%m")
        
        if period == "day":
            return f"groq:usage:{user_id}:{service_type.value}:day:{date_str}"
        elif period == "month":
            return f"groq:usage:{user_id}:{service_type.value}:month:{month_str}"
        elif period == "total_day":
            return f"groq:usage:{user_id}:total:day:{date_str}"
        elif period == "total_month":
            return f"groq:usage:{user_id}:total:month:{month_str}"
        else:
            return f"groq:usage:{user_id}:{service_type.value}:{period}"
    
    def _get_memory_key(self, user_id: int, service_type: ServiceType, period: str) -> str:
        """Generate in-memory key for usage tracking"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        month_str = datetime.utcnow().strftime("%Y-%m")
        
        if period == "day":
            return f"{user_id}:{service_type.value}:day:{date_str}"
        elif period == "month":
            return f"{user_id}:{service_type.value}:month:{month_str}"
        elif period == "total_day":
            return f"{user_id}:total:day:{date_str}"
        elif period == "total_month":
            return f"{user_id}:total:month:{month_str}"
        else:
            return f"{user_id}:{service_type.value}:{period}"
    
    async def check_tier_limit(
        self,
        user_id: int,
        user_tier: Optional[UserTier],
        service_type: ServiceType,
        tokens: int = 0,
        duration_seconds: float = 0.0
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check if user has exceeded their tier limits
        
        Args:
            user_id: User ID
            user_tier: User's subscription tier
            service_type: Type of service (LLM, TTS, STT)
            tokens: Number of tokens (for LLM)
            duration_seconds: Duration in seconds (for TTS/STT)
        
        Returns:
            Tuple of (allowed, error_message, usage_stats)
        """
        if not self._initialized:
            await self.initialize()
        
        limits = self.get_tier_limits(user_tier)
        current_date = datetime.utcnow().date()
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        if self._use_redis and self._redis_client:
            return await self._check_tier_limit_redis(
                user_id, user_tier, service_type, limits, tokens, duration_seconds, current_date, current_month
            )
        else:
            return await self._check_tier_limit_memory(
                user_id, user_tier, service_type, limits, tokens, duration_seconds, current_date, current_month
            )
    
    async def _check_tier_limit_redis(
        self,
        user_id: int,
        user_tier: Optional[UserTier],
        service_type: ServiceType,
        limits: TierLimits,
        tokens: int,
        duration_seconds: float,
        current_date: datetime.date,
        current_month: str
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check tier limits using Redis"""
        try:
            # Get daily usage
            daily_key = self._get_redis_key(user_id, service_type, "day")
            daily_requests = int(await self._redis_client.get(daily_key) or 0)
            daily_tokens = int(await self._redis_client.get(f"{daily_key}:tokens") or 0)
            daily_duration = float(await self._redis_client.get(f"{daily_key}:duration") or 0.0)
            
            # Get monthly usage
            month_key = self._get_redis_key(user_id, service_type, "month")
            month_requests = int(await self._redis_client.get(month_key) or 0)
            month_tokens = int(await self._redis_client.get(f"{month_key}:tokens") or 0)
            month_duration = float(await self._redis_client.get(f"{month_key}:duration") or 0.0)
            
            # Get total daily usage (across all services)
            total_daily_key = self._get_redis_key(user_id, ServiceType.LLM, "total_day")
            total_daily_requests = int(await self._redis_client.get(total_daily_key) or 0)
            
            # Get total monthly usage
            total_month_key = self._get_redis_key(user_id, ServiceType.LLM, "total_month")
            total_month_requests = int(await self._redis_client.get(total_month_key) or 0)
            
            # Check service-specific daily limits
            if service_type == ServiceType.LLM:
                if daily_requests >= limits.llm_requests_per_day:
                    return False, f"Daily LLM request limit exceeded ({daily_requests}/{limits.llm_requests_per_day})", {
                        "daily_requests": daily_requests,
                        "daily_limit": limits.llm_requests_per_day,
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.llm_requests_per_month
                    }
            elif service_type == ServiceType.TTS:
                if daily_requests >= limits.tts_requests_per_day:
                    return False, f"Daily TTS request limit exceeded ({daily_requests}/{limits.tts_requests_per_day})", {
                        "daily_requests": daily_requests,
                        "daily_limit": limits.tts_requests_per_day,
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.tts_requests_per_month
                    }
                # Check duration limit (convert seconds to minutes)
                if (month_duration + duration_seconds) / 60 >= limits.tts_minutes_per_month:
                    return False, f"Monthly TTS duration limit exceeded ({month_duration/60:.1f}/{limits.tts_minutes_per_month} minutes)", {
                        "monthly_duration_minutes": month_duration / 60,
                        "monthly_limit_minutes": limits.tts_minutes_per_month
                    }
            elif service_type == ServiceType.STT:
                if daily_requests >= limits.stt_requests_per_day:
                    return False, f"Daily STT request limit exceeded ({daily_requests}/{limits.stt_requests_per_day})", {
                        "daily_requests": daily_requests,
                        "daily_limit": limits.stt_requests_per_day,
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.stt_requests_per_month
                    }
                # Check duration limit
                if (month_duration + duration_seconds) / 60 >= limits.stt_minutes_per_month:
                    return False, f"Monthly STT duration limit exceeded ({month_duration/60:.1f}/{limits.stt_minutes_per_month} minutes)", {
                        "monthly_duration_minutes": month_duration / 60,
                        "monthly_limit_minutes": limits.stt_minutes_per_month
                    }
            
            # Check monthly limits
            if service_type == ServiceType.LLM:
                if month_requests >= limits.llm_requests_per_month:
                    return False, f"Monthly LLM request limit exceeded ({month_requests}/{limits.llm_requests_per_month})", {
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.llm_requests_per_month
                    }
                if (month_tokens + tokens) >= limits.llm_tokens_per_month:
                    return False, f"Monthly LLM token limit exceeded ({month_tokens}/{limits.llm_tokens_per_month} tokens)", {
                        "monthly_tokens": month_tokens,
                        "monthly_limit": limits.llm_tokens_per_month
                    }
            elif service_type == ServiceType.TTS:
                if month_requests >= limits.tts_requests_per_month:
                    return False, f"Monthly TTS request limit exceeded ({month_requests}/{limits.tts_requests_per_month})", {
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.tts_requests_per_month
                    }
            elif service_type == ServiceType.STT:
                if month_requests >= limits.stt_requests_per_month:
                    return False, f"Monthly STT request limit exceeded ({month_requests}/{limits.stt_requests_per_month})", {
                        "monthly_requests": month_requests,
                        "monthly_limit": limits.stt_requests_per_month
                    }
            
            # Check total daily limit (shared across all services)
            if total_daily_requests >= limits.total_requests_per_day:
                return False, f"Daily total request limit exceeded ({total_daily_requests}/{limits.total_requests_per_day})", {
                    "total_daily_requests": total_daily_requests,
                    "total_daily_limit": limits.total_requests_per_day
                }
            
            # Check total monthly limit
            if total_month_requests >= limits.total_requests_per_month:
                return False, f"Monthly total request limit exceeded ({total_month_requests}/{limits.total_requests_per_month})", {
                    "total_monthly_requests": total_month_requests,
                    "total_monthly_limit": limits.total_requests_per_month
                }
            
            # All checks passed
            return True, None, {
                "daily_requests": daily_requests,
                "monthly_requests": month_requests,
                "total_daily_requests": total_daily_requests,
                "total_monthly_requests": total_month_requests,
                "tier": user_tier.value if user_tier else "free"
            }
            
        except Exception as e:
            logger.error(f"Redis tier limit check error: {e}")
            # Fallback to memory
            return await self._check_tier_limit_memory(
                user_id, user_tier, service_type, limits, tokens, duration_seconds, current_date, current_month
            )
    
    async def _check_tier_limit_memory(
        self,
        user_id: int,
        user_tier: Optional[UserTier],
        service_type: ServiceType,
        limits: TierLimits,
        tokens: int,
        duration_seconds: float,
        current_date: datetime.date,
        current_month: str
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check tier limits using in-memory storage"""
        # Initialize storage if needed
        daily_key = self._get_memory_key(user_id, service_type, "day")
        month_key = self._get_memory_key(user_id, service_type, "month")
        total_daily_key = self._get_memory_key(user_id, ServiceType.LLM, "total_day")
        total_month_key = self._get_memory_key(user_id, ServiceType.LLM, "total_month")
        
        # Initialize daily usage
        if daily_key not in self._in_memory_usage:
            self._in_memory_usage[daily_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "date": current_date
            }
        
        # Reset if new day
        if self._in_memory_usage[daily_key].get("date") != current_date:
            self._in_memory_usage[daily_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "date": current_date
            }
        
        # Initialize monthly usage
        if month_key not in self._in_memory_usage:
            self._in_memory_usage[month_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "month": current_month
            }
        
        # Reset if new month
        if self._in_memory_usage[month_key].get("month") != current_month:
            self._in_memory_usage[month_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "month": current_month
            }
        
        # Initialize total daily
        if total_daily_key not in self._in_memory_usage:
            self._in_memory_usage[total_daily_key] = {
                "requests": 0,
                "date": current_date
            }
        
        if self._in_memory_usage[total_daily_key].get("date") != current_date:
            self._in_memory_usage[total_daily_key] = {"requests": 0, "date": current_date}
        
        # Initialize total monthly
        if total_month_key not in self._in_memory_usage:
            self._in_memory_usage[total_month_key] = {
                "requests": 0,
                "month": current_month
            }
        
        if self._in_memory_usage[total_month_key].get("month") != current_month:
            self._in_memory_usage[total_month_key] = {"requests": 0, "month": current_month}
        
        # Get current usage
        daily_usage = self._in_memory_usage[daily_key]
        month_usage = self._in_memory_usage[month_key]
        total_daily_usage = self._in_memory_usage[total_daily_key]
        total_month_usage = self._in_memory_usage[total_month_key]
        
        # Check service-specific daily limits
        if service_type == ServiceType.LLM:
            if daily_usage["requests"] >= limits.llm_requests_per_day:
                return False, f"Daily LLM request limit exceeded ({daily_usage['requests']}/{limits.llm_requests_per_day})", {
                    "daily_requests": daily_usage["requests"],
                    "daily_limit": limits.llm_requests_per_day
                }
        elif service_type == ServiceType.TTS:
            if daily_usage["requests"] >= limits.tts_requests_per_day:
                return False, f"Daily TTS request limit exceeded ({daily_usage['requests']}/{limits.tts_requests_per_day})", {
                    "daily_requests": daily_usage["requests"],
                    "daily_limit": limits.tts_requests_per_day
                }
            if (month_usage["duration"] + duration_seconds) / 60 >= limits.tts_minutes_per_month:
                return False, f"Monthly TTS duration limit exceeded ({month_usage['duration']/60:.1f}/{limits.tts_minutes_per_month} minutes)", {
                    "monthly_duration_minutes": month_usage["duration"] / 60,
                    "monthly_limit_minutes": limits.tts_minutes_per_month
                }
        elif service_type == ServiceType.STT:
            if daily_usage["requests"] >= limits.stt_requests_per_day:
                return False, f"Daily STT request limit exceeded ({daily_usage['requests']}/{limits.stt_requests_per_day})", {
                    "daily_requests": daily_usage["requests"],
                    "daily_limit": limits.stt_requests_per_day
                }
            if (month_usage["duration"] + duration_seconds) / 60 >= limits.stt_minutes_per_month:
                return False, f"Monthly STT duration limit exceeded ({month_usage['duration']/60:.1f}/{limits.stt_minutes_per_month} minutes)", {
                    "monthly_duration_minutes": month_usage["duration"] / 60,
                    "monthly_limit_minutes": limits.stt_minutes_per_month
                }
        
        # Check monthly limits
        if service_type == ServiceType.LLM:
            if month_usage["requests"] >= limits.llm_requests_per_month:
                return False, f"Monthly LLM request limit exceeded ({month_usage['requests']}/{limits.llm_requests_per_month})", {
                    "monthly_requests": month_usage["requests"],
                    "monthly_limit": limits.llm_requests_per_month
                }
            if (month_usage["tokens"] + tokens) >= limits.llm_tokens_per_month:
                return False, f"Monthly LLM token limit exceeded ({month_usage['tokens']}/{limits.llm_tokens_per_month} tokens)", {
                    "monthly_tokens": month_usage["tokens"],
                    "monthly_limit": limits.llm_tokens_per_month
                }
        elif service_type == ServiceType.TTS:
            if month_usage["requests"] >= limits.tts_requests_per_month:
                return False, f"Monthly TTS request limit exceeded ({month_usage['requests']}/{limits.tts_requests_per_month})", {
                    "monthly_requests": month_usage["requests"],
                    "monthly_limit": limits.tts_requests_per_month
                }
        elif service_type == ServiceType.STT:
            if month_usage["requests"] >= limits.stt_requests_per_month:
                return False, f"Monthly STT request limit exceeded ({month_usage['requests']}/{limits.stt_requests_per_month})", {
                    "monthly_requests": month_usage["requests"],
                    "monthly_limit": limits.stt_requests_per_month
                }
        
        # Check total daily limit
        if total_daily_usage["requests"] >= limits.total_requests_per_day:
            return False, f"Daily total request limit exceeded ({total_daily_usage['requests']}/{limits.total_requests_per_day})", {
                "total_daily_requests": total_daily_usage["requests"],
                "total_daily_limit": limits.total_requests_per_day
            }
        
        # Check total monthly limit
        if total_month_usage["requests"] >= limits.total_requests_per_month:
            return False, f"Monthly total request limit exceeded ({total_month_usage['requests']}/{limits.total_requests_per_month})", {
                "total_monthly_requests": total_month_usage["requests"],
                "total_monthly_limit": limits.total_requests_per_month
            }
        
        # All checks passed
        return True, None, {
            "daily_requests": daily_usage["requests"],
            "monthly_requests": month_usage["requests"],
            "total_daily_requests": total_daily_usage["requests"],
            "total_monthly_requests": total_month_usage["requests"],
            "tier": user_tier.value if user_tier else "free"
        }
    
    async def record_usage(
        self,
        user_id: int,
        user_tier: Optional[UserTier],
        service_type: ServiceType,
        tokens: int = 0,
        duration_seconds: float = 0.0
    ) -> Dict[str, Any]:
        """Record API usage for a user
        
        Args:
            user_id: User ID
            user_tier: User's subscription tier
            service_type: Type of service (LLM, TTS, STT)
            tokens: Number of tokens used (for LLM)
            duration_seconds: Duration in seconds (for TTS/STT)
        
        Returns:
            Updated usage statistics
        """
        if not self._initialized:
            await self.initialize()
        
        current_date = datetime.utcnow().date()
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        if self._use_redis and self._redis_client:
            return await self._record_usage_redis(
                user_id, service_type, tokens, duration_seconds, current_date, current_month
            )
        else:
            return await self._record_usage_memory(
                user_id, service_type, tokens, duration_seconds, current_date, current_month
            )
    
    async def _record_usage_redis(
        self,
        user_id: int,
        service_type: ServiceType,
        tokens: int,
        duration_seconds: float,
        current_date: datetime.date,
        current_month: str
    ) -> Dict[str, Any]:
        """Record usage in Redis"""
        try:
            # Daily usage
            daily_key = self._get_redis_key(user_id, service_type, "day")
            await self._redis_client.incr(daily_key)
            if tokens > 0:
                await self._redis_client.incrby(f"{daily_key}:tokens", tokens)
            if duration_seconds > 0:
                await self._redis_client.incrbyfloat(f"{daily_key}:duration", duration_seconds)
            
            # Set expiration to end of day
            now = datetime.utcnow()
            end_of_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            ttl = int((end_of_day - now).total_seconds())
            await self._redis_client.expire(daily_key, ttl)
            if tokens > 0:
                await self._redis_client.expire(f"{daily_key}:tokens", ttl)
            if duration_seconds > 0:
                await self._redis_client.expire(f"{daily_key}:duration", ttl)
            
            # Monthly usage
            month_key = self._get_redis_key(user_id, service_type, "month")
            await self._redis_client.incr(month_key)
            if tokens > 0:
                await self._redis_client.incrby(f"{month_key}:tokens", tokens)
            if duration_seconds > 0:
                await self._redis_client.incrbyfloat(f"{month_key}:duration", duration_seconds)
            
            # Set expiration to end of month
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            month_ttl = int((next_month - now).total_seconds())
            await self._redis_client.expire(month_key, month_ttl)
            if tokens > 0:
                await self._redis_client.expire(f"{month_key}:tokens", month_ttl)
            if duration_seconds > 0:
                await self._redis_client.expire(f"{month_key}:duration", month_ttl)
            
            # Total daily usage
            total_daily_key = self._get_redis_key(user_id, ServiceType.LLM, "total_day")
            await self._redis_client.incr(total_daily_key)
            await self._redis_client.expire(total_daily_key, ttl)
            
            # Total monthly usage
            total_month_key = self._get_redis_key(user_id, ServiceType.LLM, "total_month")
            await self._redis_client.incr(total_month_key)
            await self._redis_client.expire(total_month_key, month_ttl)
            
            # Get updated stats
            daily_requests = int(await self._redis_client.get(daily_key) or 0)
            month_requests = int(await self._redis_client.get(month_key) or 0)
            total_daily_requests = int(await self._redis_client.get(total_daily_key) or 0)
            total_month_requests = int(await self._redis_client.get(total_month_key) or 0)
            
            return {
                "daily_requests": daily_requests,
                "monthly_requests": month_requests,
                "total_daily_requests": total_daily_requests,
                "total_monthly_requests": total_month_requests,
                "tokens_used": tokens,
                "duration_seconds": duration_seconds
            }
            
        except Exception as e:
            logger.error(f"Redis usage recording error: {e}")
            # Fallback to memory
            return await self._record_usage_memory(
                user_id, service_type, tokens, duration_seconds, current_date, current_month
            )
    
    async def _record_usage_memory(
        self,
        user_id: int,
        service_type: ServiceType,
        tokens: int,
        duration_seconds: float,
        current_date: datetime.date,
        current_month: str
    ) -> Dict[str, Any]:
        """Record usage in memory"""
        daily_key = self._get_memory_key(user_id, service_type, "day")
        month_key = self._get_memory_key(user_id, service_type, "month")
        total_daily_key = self._get_memory_key(user_id, ServiceType.LLM, "total_day")
        total_month_key = self._get_memory_key(user_id, ServiceType.LLM, "total_month")
        
        # Initialize if needed (same logic as check)
        if daily_key not in self._in_memory_usage:
            self._in_memory_usage[daily_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "date": current_date
            }
        
        if self._in_memory_usage[daily_key].get("date") != current_date:
            self._in_memory_usage[daily_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "date": current_date
            }
        
        if month_key not in self._in_memory_usage:
            self._in_memory_usage[month_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "month": current_month
            }
        
        if self._in_memory_usage[month_key].get("month") != current_month:
            self._in_memory_usage[month_key] = {
                "requests": 0,
                "tokens": 0,
                "duration": 0.0,
                "month": current_month
            }
        
        if total_daily_key not in self._in_memory_usage:
            self._in_memory_usage[total_daily_key] = {"requests": 0, "date": current_date}
        
        if self._in_memory_usage[total_daily_key].get("date") != current_date:
            self._in_memory_usage[total_daily_key] = {"requests": 0, "date": current_date}
        
        if total_month_key not in self._in_memory_usage:
            self._in_memory_usage[total_month_key] = {"requests": 0, "month": current_month}
        
        if self._in_memory_usage[total_month_key].get("month") != current_month:
            self._in_memory_usage[total_month_key] = {"requests": 0, "month": current_month}
        
        # Increment counters
        self._in_memory_usage[daily_key]["requests"] += 1
        self._in_memory_usage[daily_key]["tokens"] += tokens
        self._in_memory_usage[daily_key]["duration"] += duration_seconds
        
        self._in_memory_usage[month_key]["requests"] += 1
        self._in_memory_usage[month_key]["tokens"] += tokens
        self._in_memory_usage[month_key]["duration"] += duration_seconds
        
        self._in_memory_usage[total_daily_key]["requests"] += 1
        self._in_memory_usage[total_month_key]["requests"] += 1
        
        return {
            "daily_requests": self._in_memory_usage[daily_key]["requests"],
            "monthly_requests": self._in_memory_usage[month_key]["requests"],
            "total_daily_requests": self._in_memory_usage[total_daily_key]["requests"],
            "total_monthly_requests": self._in_memory_usage[total_month_key]["requests"],
            "tokens_used": tokens,
            "duration_seconds": duration_seconds
        }
    
    async def get_usage_stats(
        self,
        user_id: int,
        user_tier: Optional[UserTier]
    ) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a user"""
        if not self._initialized:
            await self.initialize()
        
        limits = self.get_tier_limits(user_tier)
        current_date = datetime.utcnow().date()
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        stats = {
            "user_id": user_id,
            "tier": user_tier.value if user_tier else "free",
            "limits": {
                "llm": {
                    "daily_requests": limits.llm_requests_per_day,
                    "monthly_requests": limits.llm_requests_per_month,
                    "monthly_tokens": limits.llm_tokens_per_month
                },
                "tts": {
                    "daily_requests": limits.tts_requests_per_day,
                    "monthly_requests": limits.tts_requests_per_month,
                    "monthly_minutes": limits.tts_minutes_per_month
                },
                "stt": {
                    "daily_requests": limits.stt_requests_per_day,
                    "monthly_requests": limits.stt_requests_per_month,
                    "monthly_minutes": limits.stt_minutes_per_month
                },
                "total": {
                    "daily_requests": limits.total_requests_per_day,
                    "monthly_requests": limits.total_requests_per_month
                }
            },
            "usage": {}
        }
        
        # Get usage for each service
        for service_type in [ServiceType.LLM, ServiceType.TTS, ServiceType.STT]:
            _, _, usage = await self.check_tier_limit(user_id, user_tier, service_type)
            stats["usage"][service_type.value] = usage
        
        return stats


# Global instance
_groq_tier_enforcement: Optional[GroqTierEnforcement] = None

async def get_groq_tier_enforcement() -> GroqTierEnforcement:
    """Get the global Groq tier enforcement instance"""
    global _groq_tier_enforcement
    if not _groq_tier_enforcement:
        _groq_tier_enforcement = GroqTierEnforcement()
        await _groq_tier_enforcement.initialize()
    return _groq_tier_enforcement

