"""
Google Gemini LLM Client

This module provides a lightweight, async client for Google Gemini API text generation.
It is designed to be a drop-in replacement/fallback for other LLMs.
"""

import aiohttp
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import settings
from ..logs import get_logger

logger = get_logger(__name__)

class GeminiLLMClient:
    """Async Client for Google Gemini API (Text Generation)"""
    
    def __init__(self):
        self.settings = settings.google_gemini_llm
        self.api_key = self.settings.google_gemini_api_key
        self.base_url = self.settings.google_gemini_api_base_url
        self.model = self.settings.default_model
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_status = "unknown"
        self._last_health_check = 0
        
    async def initialize(self):
        """Initialize the client session"""
        try:
            if not self.api_key:
                logger.warning("Google Gemini API Key not found. Gemini fallback will be unavailable.")
                return False
                
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout),
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            # Simple validation
            self._health_status = "initialized"
            logger.info(f"Gemini LLM Client initialized with model: {self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM Client: {e}")
            return False

    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def health_check(self) -> Dict[str, Any]:
        """Check if Gemini API is reachable"""
        # We can simulate a health check by checking API key presence 
        # or making a dummy call (which costs money/quota), so we'll stick to basic connectivity or checks.
        # For now, we'll try to list models if possible, or just check init status.
        # The 'models' endpoint is free to query.
        
        if not self.session:
             return {"healthy": False, "error": "Session not initialized"}
        
        if not self.api_key:
             return {"healthy": False, "error": "API Key missing"}

        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return {"healthy": True, "status": "available"}
                else:
                    return {"healthy": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def generate_text(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Gemini.
        Adapts OpenAI-style messages to Gemini's 'contents' format.
        Supports multi-modal content parts if content is passed as a list.
        """
        if not self.session:
            return {"success": False, "error": "Gemini Client not initialized"}

        # 1. Adapt Messages
        # OpenAI: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        # Gemini: contents=[{"parts": [{"text": "..."}], "role": "user"}]
        
        gemini_contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # System instructions can be plain text or parts
                if isinstance(content, list):
                    system_instruction = {"parts": content}
                else:
                    system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                if isinstance(content, list):
                    gemini_contents.append({"role": "user", "parts": content})
                else:
                    gemini_contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                if isinstance(content, list):
                    gemini_contents.append({"role": "model", "parts": content})
                else:
                    gemini_contents.append({"role": "model", "parts": [{"text": content}]})
        
        # 2. Build Request
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.settings.max_tokens,
                "temperature": temperature if temperature is not None else self.settings.temperature,
                "topP": self.settings.top_p,
                "topK": self.settings.top_k
            }
        }
        
        # Inject extra parameters into generationConfig (e.g. stopSequences, responseMimeType)
        if kwargs:
            payload["generationConfig"].update(kwargs)
        
        if system_instruction:
            payload["system_instruction"] = system_instruction

        start_time = time.time()
        
        try:
            async with self.session.post(url, json=payload) as response:
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    # Parse response
                    # Expected: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
                    try:
                        candidate = data["candidates"][0]
                        parts = candidate.get("content", {}).get("parts", [])
                        text_content = "".join([p.get("text", "") for p in parts])
                        
                        finish_reason = candidate.get("finishReason")
                        
                        return {
                            "success": True,
                            "content": text_content,
                            "text": text_content, # Compatibility
                            "model": self.model,
                            "response_time_ms": elapsed_ms,
                            "finish_reason": finish_reason,
                            "usage": data.get("usageMetadata", {})
                        }
                    except (KeyError, IndexError) as e:
                         return {
                            "success": False, 
                            "error": f"Failed to parse Gemini response: {str(e)}",
                            "raw": data
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API Error {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Gemini Request Exception: {e}")
            return {"success": False, "error": str(e)}
