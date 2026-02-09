"""
Groq LLM Client

This module provides a production-ready Groq API client for LLM text generation.
Groq API is OpenAI-compatible, making integration straightforward.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import settings
from ..logs import get_logger
from .groq_rate_limiter import get_groq_rate_limiter, ServiceType

logger = get_logger(__name__)


class GroqLLMClient:
    """Production-ready Groq LLM client for Agent47"""
    
    def __init__(self):
        self.api_key = settings.groq.groq_api_key
        self.api_base_url = settings.groq.groq_api_base_url
        self.default_model = settings.groq.groq_default_model
        self.max_tokens = settings.groq.groq_max_tokens
        self.temperature = settings.groq.groq_temperature
        self.top_p = settings.groq.groq_top_p
        self.timeout = settings.groq.groq_request_timeout
        self.max_retries = settings.groq.groq_max_retries
        self.retry_delay = settings.groq.groq_retry_delay
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_status = "unknown"
        self._last_health_check = 0
        self._concurrent_requests = 0
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._daily_requests = 0
        self._last_daily_reset = datetime.utcnow().date()
        self._rate_limiter = None
        
    async def initialize(self):
        """Initialize HTTP session and verify Groq API connection"""
        try:
            if not self.api_key:
                raise ValueError("Groq API key not configured. Set GROQ_API_KEY in environment variables.")
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key.strip()}",
                    "Content-Type": "application/json",
                    "User-Agent": "Agent47-Groq-Client/1.0"
                }
            )
            
            # Test connection with a simple health check
            health_result = await self.health_check()
            if health_result["healthy"]:
                self._health_status = "healthy"
                # Initialize rate limiter (optional, falls back to client-side if unavailable)
                try:
                    self._rate_limiter = await get_groq_rate_limiter()
                except Exception as e:
                    logger.warning(f"Rate limiter not available, using client-side rate limiting: {e}")
                    self._rate_limiter = None
                logger.info("Groq LLM client initialized successfully")
                return True
            else:
                raise Exception(f"Groq API health check failed: {health_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM client: {e}")
            self._health_status = "unhealthy"
            raise
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Groq API health with caching"""
        current_time = time.time()
        
        # Cache health check results for 30 seconds
        if current_time - self._last_health_check < 30:
            return {
                "healthy": self._health_status == "healthy",
                "status": self._health_status,
                "cached": True
            }
        
        try:
            if not self.session:
                return {"healthy": False, "error": "Session not initialized"}
            
            if not self.api_key:
                return {"healthy": False, "error": "API key not configured"}
            
            # Use models endpoint as health check (lightweight)
            health_endpoint = f"{self.api_base_url}/models"
            
            async with self.session.get(health_endpoint, timeout=5) as response:
                if response.status == 200:
                    self._health_status = "healthy"
                    self._last_health_check = current_time
                    return {"healthy": True, "status": "healthy"}
                elif response.status == 401:
                    self._health_status = "unauthorized"
                    return {"healthy": False, "error": "Invalid API key"}
                elif response.status == 429:
                    self._health_status = "rate_limited"
                    return {"healthy": False, "error": "Rate limit exceeded"}
                else:
                    self._health_status = "unhealthy"
                    return {"healthy": False, "error": f"HTTP {response.status}"}
                    
        except asyncio.TimeoutError:
            self._health_status = "timeout"
            return {"healthy": False, "error": "Health check timeout"}
        except Exception as e:
            self._health_status = "error"
            return {"healthy": False, "error": str(e)}
    
    async def generate_text(
        self,
        prompt: str = None,
        system_prompt: str = None,
        messages: List[Dict[str, str]] = None,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Groq API with comprehensive error handling
        
        Supports both prompt/system_prompt format and messages format (OpenAI-compatible)"""
        
        # Check health before proceeding
        health_check = await self.health_check()
        if not health_check["healthy"]:
            return {
                "success": False,
                "error": f"Groq API is unhealthy: {health_check.get('error', 'Unknown error')}",
                "health_status": self._health_status
            }
        
        # Rate limiting check (use centralized limiter if available, otherwise client-side)
        if self._rate_limiter:
            try:
                allowed, error_msg, usage_stats = await self._rate_limiter.check_rate_limit(
                    ServiceType.LLM, user_id=None
                )
                if not allowed:
                    return {
                        "success": False,
                        "error": error_msg or "Rate limit exceeded",
                        "usage_stats": usage_stats
                    }
            except Exception as e:
                logger.warning(f"Rate limiter check failed, using client-side: {e}")
                # Fall through to client-side rate limiting
        
        # Client-side rate limiting (fallback or primary if limiter unavailable)
        max_concurrent = settings.groq.groq_max_concurrent_requests
        if self._concurrent_requests >= max_concurrent:
            return {
                "success": False,
                "error": "Rate limit exceeded: too many concurrent requests",
                "retry_after": 60
            }
        
        # Reset daily counter if needed
        self._reset_daily_counter_if_needed()
        
        # Check daily limit
        if self._daily_requests >= settings.groq.groq_rate_limit_per_day:
            return {
                "success": False,
                "error": "Daily rate limit exceeded",
                "daily_requests": self._daily_requests,
                "daily_limit": settings.groq.groq_rate_limit_per_day
            }
        
        self._concurrent_requests += 1
        self._total_requests += 1
        
        try:
            # Convert messages format if needed
            if messages and not prompt:
                # Messages format (OpenAI-compatible)
                formatted_messages = messages
            else:
                # Convert prompt/system_prompt to messages format
                formatted_messages = []
                if system_prompt:
                    formatted_messages.append({"role": "system", "content": system_prompt})
                if prompt:
                    formatted_messages.append({"role": "user", "content": prompt})
            
            if not formatted_messages:
                return {
                    "success": False,
                    "error": "No prompt or messages provided"
                }
            
            # Prepare request payload
            payload = {
                "model": self.default_model,
                "messages": formatted_messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "top_p": top_p if top_p is not None else self.top_p,
                "stream": False
            }
            
            endpoint = f"{self.api_base_url}/chat/completions"
            
            # Make request with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    async with self.session.post(
                        endpoint,
                        json=payload,
                        timeout=self.timeout
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            response_time = int((time.time() - start_time) * 1000)
                            
                            # Extract response
                            if "choices" in result and len(result["choices"]) > 0:
                                choice = result["choices"][0]
                                content = choice.get("message", {}).get("content", "")
                                finish_reason = choice.get("finish_reason", "unknown")
                                
                                # Log if response was truncated
                                if finish_reason == "length":
                                    logger.warning(f"Groq response truncated due to max_tokens limit. Consider increasing max_tokens. Current: {payload.get('max_tokens', self.max_tokens)}")
                                
                                # Extract usage information
                                usage = result.get("usage", {})
                                completion_tokens = usage.get("completion_tokens", 0)
                                
                                # Log token usage for debugging
                                if completion_tokens >= (payload.get("max_tokens", self.max_tokens) * 0.95):
                                    logger.warning(f"Groq response may be truncated. Used {completion_tokens}/{payload.get('max_tokens', self.max_tokens)} tokens")
                                
                                # Update metrics
                                self._successful_requests += 1
                                self._daily_requests += 1
                                
                                # Record usage in centralized rate limiter
                                if self._rate_limiter:
                                    try:
                                        tokens_used = usage.get("total_tokens", 0) if usage else 0
                                        await self._rate_limiter.record_usage(
                                            ServiceType.LLM, user_id=None, tokens=tokens_used
                                        )
                                    except Exception as e:
                                        logger.warning(f"Failed to record usage in rate limiter: {e}")
                                
                                return {
                                    "success": True,
                                    "content": content,
                                    "text": content,  # For compatibility
                                    "usage": {
                                        "prompt_tokens": usage.get("prompt_tokens", 0),
                                        "completion_tokens": completion_tokens,
                                        "total_tokens": usage.get("total_tokens", 0)
                                    },
                                    "model": result.get("model", self.default_model),
                                    "response_time_ms": response_time,
                                    "daily_requests": self._daily_requests,
                                    "finish_reason": finish_reason,
                                    "truncated": finish_reason == "length"
                                }
                            else:
                                last_error = "No choices in response"
                                
                        elif response.status == 401:
                            last_error = "Invalid API key"
                            break  # Don't retry auth errors
                            
                        elif response.status == 429:
                            # Rate limited - check retry-after header
                            retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(retry_after)
                                continue
                            last_error = f"Rate limit exceeded (HTTP 429)"
                            
                        elif response.status == 400:
                            error_data = await response.json()
                            last_error = f"Bad request: {error_data.get('error', {}).get('message', 'Unknown error')}"
                            break  # Don't retry bad requests
                            
                        else:
                            last_error = f"HTTP {response.status}"
                            
                except asyncio.TimeoutError:
                    last_error = "Request timeout"
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                        
                except Exception as e:
                    last_error = str(e)
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
            
            # All retries failed
            self._failed_requests += 1
            return {
                "success": False,
                "error": last_error or "Unknown error",
                "retries": self.max_retries
            }
            
        except Exception as e:
            logger.error(f"Groq API generation error: {e}")
            self._failed_requests += 1
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            self._concurrent_requests -= 1
    
    def _reset_daily_counter_if_needed(self):
        """Reset daily request counter if a new day has started"""
        today = datetime.utcnow().date()
        if today > self._last_daily_reset:
            self._daily_requests = 0
            self._last_daily_reset = today
            logger.info(f"Reset Groq daily request counter (new day: {today})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            "health_status": self._health_status,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "daily_requests": self._daily_requests,
            "daily_limit": settings.groq.groq_rate_limit_per_day,
            "concurrent_requests": self._concurrent_requests,
            "last_health_check": self._last_health_check
        }

