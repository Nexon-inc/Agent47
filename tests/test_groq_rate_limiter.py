"""
Unit tests for Groq Rate Limiter
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.groq_rate_limiter import GroqRateLimiter, ServiceType


class TestGroqRateLimiter:
    """Test suite for Groq Rate Limiter"""
    
    @pytest.fixture
    def limiter(self):
        """Create a Groq Rate Limiter instance"""
        return GroqRateLimiter()
    
    @pytest.mark.asyncio
    async def test_initialize_with_redis(self, limiter):
        """Test initialization with Redis"""
        mock_redis = AsyncMock()
        mock_redis.is_connected = AsyncMock(return_value=True)
        
        with patch('backend.core.ai.groq_rate_limiter.get_redis_manager', return_value=mock_redis):
            await limiter.initialize()
            assert limiter._initialized is True
            assert limiter._use_redis is True
    
    @pytest.mark.asyncio
    async def test_initialize_without_redis(self, limiter):
        """Test initialization without Redis (in-memory fallback)"""
        with patch('backend.core.ai.groq_rate_limiter.get_redis_manager', return_value=None):
            await limiter.initialize()
            assert limiter._initialized is True
            assert limiter._use_redis is False
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, limiter):
        """Test rate limit check when allowed"""
        await limiter.initialize()
        limiter._use_redis = False  # Use in-memory
        
        # First request should be allowed
        allowed, error, stats = await limiter.check_rate_limit(ServiceType.LLM, user_id=1)
        assert allowed is True
        assert error is None
        assert stats["daily_count"] == 0
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded_daily(self, limiter):
        """Test rate limit check when daily limit exceeded"""
        await limiter.initialize()
        limiter._use_redis = False  # Use in-memory
        
        # Set daily count to limit
        key = limiter._get_memory_key(ServiceType.LLM, 1, "usage")
        limiter._memory_usage[key] = {
            "count_minute": 0,
            "timestamps_minute": [],
            "count_day": 1000,  # At daily limit
            "last_reset_day": limiter._memory_usage.get(key, {}).get("last_reset_day", None) or limiter._memory_usage.setdefault(key, {}).setdefault("last_reset_day", None)
        }
        
        allowed, error, stats = await limiter.check_rate_limit(ServiceType.LLM, user_id=1)
        assert allowed is False
        assert "daily limit" in error.lower()
    
    @pytest.mark.asyncio
    async def test_record_usage(self, limiter):
        """Test recording usage"""
        await limiter.initialize()
        limiter._use_redis = False  # Use in-memory
        
        await limiter.record_usage(ServiceType.LLM, user_id=1, tokens=100)
        
        key = limiter._get_memory_key(ServiceType.LLM, 1, "usage")
        usage = limiter._memory_usage.get(key, {})
        assert usage["count_day"] == 1
        assert usage["tokens_daily"] == 100
    
    @pytest.mark.asyncio
    async def test_get_usage_stats(self, limiter):
        """Test getting usage statistics"""
        await limiter.initialize()
        limiter._use_redis = False  # Use in-memory
        
        # Record some usage
        await limiter.record_usage(ServiceType.LLM, user_id=1, tokens=500)
        
        stats = await limiter.get_usage_stats(ServiceType.LLM, user_id=1)
        
        assert stats["service_type"] == "llm"
        assert stats["user_id"] == 1
        assert stats["daily_requests"] == 1
        assert stats["daily_tokens"] == 500
    
    @pytest.mark.asyncio
    async def test_multiple_services(self, limiter):
        """Test rate limiting for multiple services"""
        await limiter.initialize()
        limiter._use_redis = False  # Use in-memory
        
        # Record usage for different services
        await limiter.record_usage(ServiceType.LLM, user_id=1, tokens=100)
        await limiter.record_usage(ServiceType.TTS, user_id=1, tokens=0, duration_seconds=10.0)
        await limiter.record_usage(ServiceType.STT, user_id=1, tokens=0, duration_seconds=5.0)
        
        # Check stats for each service
        llm_stats = await limiter.get_usage_stats(ServiceType.LLM, user_id=1)
        tts_stats = await limiter.get_usage_stats(ServiceType.TTS, user_id=1)
        stt_stats = await limiter.get_usage_stats(ServiceType.STT, user_id=1)
        
        assert llm_stats["daily_requests"] == 1
        assert llm_stats["daily_tokens"] == 100
        assert tts_stats["daily_requests"] == 1
        assert tts_stats["daily_duration_seconds"] == 10.0
        assert stt_stats["daily_requests"] == 1
        assert stt_stats["daily_duration_seconds"] == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

