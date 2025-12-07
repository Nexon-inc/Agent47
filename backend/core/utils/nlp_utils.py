import json
import re
import asyncio
import aiohttp
import ssl
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# OllamaLLMClient for Llama 3 8B

class OllamaLLMClient:
    """Production-ready Ollama LLM client with Llama 3 8B for Agent47"""
    
    def __init__(self):
        self.api_url = settings.ollama.ollama_api_url
        self.model_name = "llama3:8b"
        self.timeout = settings.ollama.ollama_request_timeout  # Use configured timeout
        self.max_retries = 3
        self.retry_delay = 2
        self.session = None
        self._health_status = "unknown"
        self._last_health_check = 0
        self._concurrent_requests = 0
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        
    async def initialize(self):
        """Initialize HTTP session and verify Ollama service connection"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Agent47-Ollama-Client/1.0"
                }
            )
            
            # Test connection
            health_result = await self.health_check()
            if health_result["healthy"]:
                self._health_status = "healthy"
                logger.info("Ollama LLM client initialized successfully")
                return True
            else:
                raise Exception(f"Ollama service health check failed: {health_result['error']}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM client: {e}")
            self._health_status = "unhealthy"
            raise
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health with caching"""
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
            
            # Detect if using wrapper service (port 8008) or native Ollama (port 11434)
            is_wrapper_service = "8008" in self.api_url or "/health" in self.api_url
            
            # Use appropriate health check endpoint
            if is_wrapper_service:
                # Wrapper service uses /health endpoint
                health_endpoint = f"{self.api_url}/health"
            else:
                # Native Ollama uses /api/tags endpoint
                health_endpoint = f"{self.api_url}/api/tags"
            
            async with self.session.get(health_endpoint, timeout=5) as response:
                if response.status == 200:
                    self._health_status = "healthy"
                    self._last_health_check = current_time
                    return {"healthy": True, "status": "healthy"}
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
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Ollama LLM with comprehensive error handling
        
        Supports both prompt/system_prompt format and messages format (like OpenAI)"""
        
        # Check health before proceeding
        health_check = await self.health_check()
        if not health_check["healthy"]:
            # Build prompt from messages if provided
            if messages and not prompt:
                prompt = self._messages_to_prompt(messages)
            return await self._handle_unhealthy_service(prompt, system_prompt, max_tokens, temperature)
        
        # Rate limiting check (Ollama typically doesn't need strict rate limiting)
        max_concurrent = kwargs.get("max_concurrent_requests", 10)
        if self._concurrent_requests >= max_concurrent:
            return {"success": False, "error": "Rate limit exceeded", "retry_after": 60}
        
        self._concurrent_requests += 1
        self._total_requests += 1
        
        try:
            # Convert messages to prompt if messages format is used
            if messages and not prompt:
                prompt, system_prompt = self._extract_from_messages(messages)
            
            # Build the prompt with system prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Detect if using wrapper service (port 8008) or native Ollama (port 11434)
            is_wrapper_service = "8008" in self.api_url
            
            # Prepare request payload based on service type
            if is_wrapper_service:
                # Wrapper service uses /chat endpoint with different format
                payload = {
                    "message": full_prompt,
                    "max_tokens": max_tokens or settings.ollama.ollama_max_tokens,
                    "temperature": temperature if temperature is not None else 0.7,
                    "top_p": 0.9  # Default top_p for wrapper service
                }
                endpoint = f"{self.api_url}/chat"
            else:
                # Native Ollama uses /api/generate endpoint
                payload = {
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {}
                }
                
                # Add optional parameters in options
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
                else:
                    # Use default from settings if not specified
                    payload["options"]["num_predict"] = settings.ollama.ollama_max_tokens
                if temperature is not None:
                    payload["options"]["temperature"] = temperature
                # Don't stop on newlines - let it complete naturally
                payload["options"]["stop"] = ["</s>"]
                endpoint = f"{self.api_url}/api/generate"
            
            # Make request with retries
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
                            response_time = time.time() - start_time
                            
                            # Update metrics
                            self._successful_requests += 1
                            
                            # Extract response text based on service type
                            if is_wrapper_service:
                                # Wrapper service returns response in 'response' field
                                response_text = result.get("response", "")
                                # Wrapper service returns usage info differently
                                usage_info = result.get("usage", {})
                                tokens_used = usage_info.get("completion_tokens", 0) if usage_info else 0
                            else:
                                # Native Ollama returns response in 'response' field
                                response_text = result.get("response", "")
                                tokens_used = result.get("eval_count", 0)
                            
                            return {
                                "success": True,
                                "text": response_text,
                                "content": response_text,  # Also provide 'content' for compatibility
                                "response_time": response_time,
                                "response_time_ms": int(response_time * 1000),
                                "tokens_used": tokens_used,
                                "usage": result.get("usage", {
                                    "prompt_tokens": result.get("prompt_eval_count", 0),
                                    "completion_tokens": tokens_used,
                                    "total_tokens": tokens_used
                                }) if not is_wrapper_service else result.get("usage", {}),
                                "model": self.model_name
                            }
                        
                        elif response.status >= 500:  # Server error
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                                continue
                            else:
                                error_text = await response.text()
                                return {"success": False, "error": f"Server error: {response.status}: {error_text}"}
                        
                        else:
                            error_text = await response.text()
                            return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                            
                except asyncio.TimeoutError:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return {"success": False, "error": "Request timeout"}
                        
        except Exception as e:
            logger.error(f"Ollama LLM request failed: {e}")
            self._failed_requests += 1
            return {"success": False, "error": str(e)}
            
        finally:
            self._concurrent_requests -= 1
    
    def _extract_from_messages(self, messages: List[Dict[str, str]]) -> Tuple[str, Optional[str]]:
        """Extract prompt and system_prompt from messages format"""
        system_prompt = None
        user_messages = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                user_messages.append(content)
            elif role == "assistant":
                # Skip assistant messages for now
                pass
        
        # Combine all user messages
        prompt = "\n".join(user_messages) if user_messages else ""
        
        return prompt, system_prompt
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(content)
        return "\n".join(prompt_parts)
    
    async def _handle_unhealthy_service(
        self, 
        prompt: str = None, 
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """Handle requests when Ollama service is unhealthy"""
        
        # Return error with retry suggestion
        return {
            "success": False,
            "error": "Ollama service unavailable",
            "retry_after": 60
        }
    
    async def _openai_fallback(
        self, 
        prompt: str, 
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """OpenAI fallback when Grok is unavailable"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.grok.grok_fallback_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=settings.grok.grok_fallback_model,
                messages=messages,
                max_tokens=max_tokens or 1000,
                temperature=temperature or 0.7
            )
            
            if response.choices and response.choices[0].message.content:
                return {
                    "success": True,
                    "text": response.choices[0].message.content,
                    "model": "openai-fallback",
                    "fallback_used": True
                }
            else:
                return {"success": False, "error": "OpenAI fallback failed"}
                
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            return {"success": False, "error": f"Fallback failed: {str(e)}"}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        return {
            "health_status": self._health_status,
            "concurrent_requests": self._concurrent_requests,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": self._successful_requests / max(self._total_requests, 1),
            "last_health_check": self._last_health_check
        }

class NLPUtils:
    """Production-ready NLP utilities using unified AI service manager"""
    
    def __init__(self):
        self.ai_service_manager = None
        self._initialized = False
        self._fallback_enabled = True
        self._performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
    async def initialize(self):
        """Initialize AI service manager and verify connection"""
        try:
            from ..ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("NLP utilities initialized successfully with AI Service Manager")
                
        except Exception as e:
            logger.error(f"Failed to initialize NLP utilities: {e}")
            if not self._fallback_enabled:
                raise
            else:
                logger.warning("Continuing with fallback mode enabled")
    
    async def detect_intent(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Detect user intent using unified AI service manager"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = self._build_intent_detection_prompt(context)
            
            # Prepare messages for AI service manager
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Generate response using AI service manager
            response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            
            if response.success:
                intent_data = self._parse_intent_response(response.text_content)
                self._update_metrics(True, response.response_time_ms or 0)
                
                return {
                    "success": True,
                    "intent": intent_data,
                    "raw_response": response.text_content,
                    "model": response.service_used,
                    "response_time": response.response_time_ms,
                    "fallback_used": response.fallback_used
                }
            else:
                self._update_metrics(False, 0)
                return {
                    "success": False,
                    "error": response.error
                }
                
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            self._update_metrics(False, 0)
            return {"success": False, "error": str(e)}
    
    def _build_intent_detection_prompt(self, context: Dict[str, Any] = None) -> str:
        """Build system prompt for intent detection optimized for Grok LLM"""
        base_prompt = """You are an AI assistant that analyzes user requests to determine their intent and route them to appropriate agents in the Agent47 system.

Available agents and their capabilities:
- Aria: Social media management (posting, scheduling, analytics)
- Clara: Customer support (ticket management, FAQ, live chat)
- Eric: Sales (lead generation, CRM, sales automation)
- Joe: Research (web search, data analysis, market research)
- Jackie: Marketing (campaign management, email marketing, SEO)
- Shakes: Content creation (writing, design, video editing)
- Purity: Business and finance (accounting, invoicing, financial analysis)

For each user request, analyze the intent and return a JSON response with:
{
    "primary_agent": "agent_name",
    "secondary_agents": ["agent_name1", "agent_name2"],
    "intent_type": "task_type",
    "confidence": 0.95,
    "extracted_entities": {
        "platforms": ["twitter", "instagram"],
        "content_type": "post",
        "urgency": "high/medium/low",
        "target_audience": "description"
    },
    "task_complexity": "simple/medium/complex",
    "estimated_duration": "time_estimate",
    "required_features": ["feature1", "feature2"]
}

Be specific and accurate. Only return valid JSON."""
        
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
            base_prompt += context_str
        
        return base_prompt
    
    def _parse_intent_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Grok LLM response to extract intent data with enhanced error handling"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                intent_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["primary_agent", "intent_type", "confidence"]
                for field in required_fields:
                    if field not in intent_data:
                        intent_data[field] = "unknown" if field == "primary_agent" else 0.0
                
                return intent_data
            else:
                # Fallback parsing
                return self._fallback_intent_parsing(cleaned_text)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response from Grok: {e}")
            return self._fallback_intent_parsing(response_text)
        except Exception as e:
            logger.error(f"Intent response parsing failed: {e}")
            return {
                "primary_agent": "unknown",
                "intent_type": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _fallback_intent_parsing(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback intent parsing when JSON parsing fails"""
        text_lower = text.lower()
        
        # Simple keyword-based intent detection
        intent_data = {
            "primary_agent": "unknown",
            "secondary_agents": [],
            "intent_type": "unknown",
            "confidence": 0.5,
            "extracted_entities": {},
            "task_complexity": "medium",
            "estimated_duration": "unknown",
            "required_features": []
        }
        
        # Enhanced agent detection with more keywords
        agent_keywords = {
            "aria": ["social", "post", "tweet", "instagram", "facebook", "linkedin", "social media"],
            "clara": ["support", "help", "customer", "ticket", "chat", "faq", "assistance"],
            "eric": ["sales", "lead", "crm", "deal", "prospect", "conversion", "revenue"],
            "joe": ["research", "search", "analyze", "market", "data", "insights", "trends"],
            "jackie": ["marketing", "campaign", "email", "seo", "advertising", "promotion"],
            "shakes": ["content", "write", "create", "design", "video", "graphic", "creative"],
            "purity": ["finance", "accounting", "invoice", "business", "money", "budget", "planning"]
        }
        
        for agent, keywords in agent_keywords.items():
            if any(word in text_lower for word in keywords):
                intent_data["primary_agent"] = agent
                intent_data["intent_type"] = f"{agent}_task"
                intent_data["confidence"] = 0.7
                break
        
        return intent_data
    
    async def route_task(self, user_input: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route user task to appropriate agent(s) with enhanced validation"""
        try:
            # Detect intent
            intent_result = await self.detect_intent(user_input, user_context)
            
            if not intent_result["success"]:
                return intent_result
            
            intent_data = intent_result["intent"]
            
            # Validate agent availability
            agent_validation = await self._validate_agent_availability(intent_data["primary_agent"])
            
            if not agent_validation["available"]:
                # Try secondary agents
                for secondary_agent in intent_data.get("secondary_agents", []):
                    secondary_validation = await self._validate_agent_availability(secondary_agent)
                    if secondary_validation["available"]:
                        intent_data["primary_agent"] = secondary_agent
                        break
                else:
                    return {
                        "success": False,
                        "error": "No suitable agents available for this task"
                    }
            
            # Build routing response
            routing_response = {
                "success": True,
                "routed_to": intent_data["primary_agent"],
                "intent": intent_data,
                "routing_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_input": user_input,
                    "confidence": intent_data.get("confidence", 0.0),
                    "estimated_completion": intent_data.get("estimated_duration", "unknown"),
                    "model_used": intent_result.get("model", "unknown"),
                    "response_time": intent_result.get("response_time", 0)
                }
            }
            
            return routing_response
            
        except Exception as e:
            logger.error(f"Task routing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_agent_availability(self, agent_name: str) -> Dict[str, Any]:
        """Enhanced agent availability validation with health checks"""
        try:
            # Check agent status, health, and user permissions
            available_agents = ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]
            
            if agent_name.lower() not in available_agents:
                return {
                    "available": False,
                    "agent_name": agent_name,
                    "status": "unknown",
                    "health": "unknown",
                    "error": f"Agent '{agent_name}' not found in available agents"
                }
            
            # Check agent health by making a health check request
            agent_health = await self._check_agent_health(agent_name)
            
            if not agent_health["healthy"]:
                return {
                    "available": False,
                    "agent_name": agent_name,
                    "status": "unhealthy",
                    "health": "unhealthy",
                    "error": agent_health.get("error", "Agent health check failed")
                }
            
            # Check if agent is currently processing requests (load balancing)
            agent_load = await self._check_agent_load(agent_name)
            
            if agent_load["overloaded"]:
                return {
                    "available": False,
                    "agent_name": agent_name,
                    "status": "overloaded",
                    "health": "healthy",
                    "error": "Agent is currently overloaded, please try again later"
                }
            
            return {
                "available": True,
                "agent_name": agent_name,
                "status": "active",
                "health": "healthy",
                "load": agent_load["current_load"],
                "max_capacity": agent_load["max_capacity"]
            }
                
        except Exception as e:
            logger.error(f"Agent availability validation failed: {e}")
            return {
                "available": False,
                "agent_name": agent_name,
                "status": "error",
                "health": "error",
                "error": str(e)
            }
    
    async def _check_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Check agent health by making a health check request"""
        try:
            import aiohttp
            
            # Map agent names to their health check endpoints
            agent_endpoints = {
                "aria": "http://localhost:8000/aria/health",
                "clara": "http://localhost:8001/clara/health", 
                "eric": "http://localhost:8002/eric/health",
                "joe": "http://localhost:8003/joe/health",
                "jackie": "http://localhost:8004/jackie/health",
                "shakes": "http://localhost:8005/shakes/health",
                "purity": "http://localhost:8006/purity/health"
            }
            
            endpoint = agent_endpoints.get(agent_name.lower())
            if not endpoint:
                return {"healthy": False, "error": f"No health endpoint configured for agent {agent_name}"}
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            return {
                                "healthy": True,
                                "status": health_data.get("status", "unknown"),
                                "uptime": health_data.get("uptime", 0),
                                "version": health_data.get("version", "unknown")
                            }
                        else:
                            return {"healthy": False, "error": f"Health check returned status {response.status}"}
                except asyncio.TimeoutError:
                    return {"healthy": False, "error": "Health check timeout"}
                except Exception as e:
                    return {"healthy": False, "error": f"Health check failed: {str(e)}"}
                    
        except Exception as e:
            logger.error(f"Agent health check failed for {agent_name}: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def _check_agent_load(self, agent_name: str) -> Dict[str, Any]:
        """Check agent current load and capacity"""
        try:
            import aiohttp
            
            # Map agent names to their load check endpoints
            agent_endpoints = {
                "aria": "http://localhost:8000/aria/load",
                "clara": "http://localhost:8001/clara/load",
                "eric": "http://localhost:8002/eric/load", 
                "joe": "http://localhost:8003/joe/load",
                "jackie": "http://localhost:8004/jackie/load",
                "shakes": "http://localhost:8005/shakes/load",
                "purity": "http://localhost:8006/purity/load"
            }
            
            endpoint = agent_endpoints.get(agent_name.lower())
            if not endpoint:
                # If no load endpoint, assume healthy load
                return {
                    "overloaded": False,
                    "current_load": 0,
                    "max_capacity": 100,
                    "load_percentage": 0
                }
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=3)) as response:
                        if response.status == 200:
                            load_data = await response.json()
                            current_load = load_data.get("current_load", 0)
                            max_capacity = load_data.get("max_capacity", 100)
                            load_percentage = (current_load / max_capacity) * 100 if max_capacity > 0 else 0
                            
                            return {
                                "overloaded": load_percentage > 80,  # Overloaded if > 80%
                                "current_load": current_load,
                                "max_capacity": max_capacity,
                                "load_percentage": load_percentage
                            }
                        else:
                            # If load check fails, assume healthy load
                            return {
                                "overloaded": False,
                                "current_load": 0,
                                "max_capacity": 100,
                                "load_percentage": 0
                            }
                except Exception:
                    # If load check fails, assume healthy load
                    return {
                        "overloaded": False,
                        "current_load": 0,
                        "max_capacity": 100,
                        "load_percentage": 0
                    }
                    
        except Exception as e:
            logger.error(f"Agent load check failed for {agent_name}: {e}")
            # If load check fails, assume healthy load
            return {
                "overloaded": False,
                "current_load": 0,
                "max_capacity": 100,
                "load_percentage": 0
            }
    
    async def extract_entities(self, text: str, entity_types: List[str] = None) -> Dict[str, Any]:
        """Extract named entities from text using Grok LLM"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            if not entity_types:
                entity_types = ["platforms", "content_type", "urgency", "target_audience", "keywords"]
            
            system_prompt = f"""Extract the following entities from the user text:
{', '.join(entity_types)}

Return the results as a JSON object with each entity type as a key.
For example:
{{
    "platforms": ["twitter", "instagram"],
    "content_type": "social_post",
    "urgency": "medium",
    "target_audience": "young professionals",
    "keywords": ["marketing", "automation"]
}}

Only return valid JSON."""
            
            response = await self.ollama_client.generate_text(
                prompt=text,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.1
            )
            
            if response["success"]:
                try:
                    entities = json.loads(response["text"])
                    self._update_metrics(True, response.get("response_time", 0))
                    
                    return {
                        "success": True,
                        "entities": entities,
                        "raw_response": response["text"],
                        "model": response["model"]
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse entity extraction response"
                    }
            else:
                self._update_metrics(False, 0)
                return response
                
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            self._update_metrics(False, 0)
            return {"success": False, "error": str(e)}
    
    async def generate_response(self, context: str, user_input: str, response_type: str = "general") -> Dict[str, Any]:
        """Generate contextual response using Grok LLM"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = self._build_response_generation_prompt(response_type, context)
            
            response = await self.ollama_client.generate_text(
                prompt=user_input,
                system_prompt=system_prompt,
                max_tokens=settings.grok.grok_max_tokens,
                temperature=0.7
            )
            
            if response["success"]:
                self._update_metrics(True, response.get("response_time", 0))
                
                return {
                    "success": True,
                    "response": response["text"],
                    "model": response["model"],
                    "tokens_used": response.get("tokens_used", 0),
                    "response_time": response.get("response_time", 0)
                }
            else:
                self._update_metrics(False, 0)
                return response
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            self._update_metrics(False, 0)
            return {"success": False, "error": str(e)}
    
    def _build_response_generation_prompt(self, response_type: str, context: str) -> str:
        """Build system prompt for response generation optimized for Grok LLM"""
        base_prompt = f"You are an AI assistant in the Agent47 system. Context: {context}\n\n"
        
        if response_type == "task_confirmation":
            base_prompt += "Confirm the user's task and provide next steps clearly and professionally."
        elif response_type == "error_explanation":
            base_prompt += "Explain any errors or issues clearly and suggest solutions."
        elif response_type == "progress_update":
            base_prompt += "Provide a clear progress update on ongoing tasks."
        else:
            base_prompt += "Provide helpful, accurate, and professional responses."
        
        return base_prompt
    
    def _update_metrics(self, success: bool, response_time: float):
        """Update performance metrics"""
        self._performance_metrics["total_requests"] += 1
        
        if success:
            self._performance_metrics["successful_requests"] += 1
        else:
            self._performance_metrics["failed_requests"] += 1
        
        # Update average response time
        current_avg = self._performance_metrics["average_response_time"]
        total_successful = self._performance_metrics["successful_requests"]
        
        if total_successful > 0:
            self._performance_metrics["average_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for NLP utilities"""
        try:
            if not self._initialized:
                return {
                    "healthy": False,
                    "status": "not_initialized",
                    "error": "NLP utilities not initialized"
                }
            
            # Check Grok client health
            ollama_health = await self.ollama_client.health_check()
            
            # Get performance metrics
            performance_metrics = self.get_performance_metrics()
            
            # Determine overall health
            overall_healthy = (
                grok_health["healthy"] and 
                performance_metrics["success_rate"] >= 0.8 and
                performance_metrics["average_response_time"] <= 10.0
            )
            
            return {
                "healthy": overall_healthy,
                "status": "healthy" if overall_healthy else "degraded",
                "ollama_client": ollama_health,
                "performance": performance_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"NLP utilities health check failed: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        total = self._performance_metrics["total_requests"]
        successful = self._performance_metrics["successful_requests"]
        
        return {
            **self._performance_metrics,
            "success_rate": successful / max(total, 1),
            "failure_rate": (total - successful) / max(total, 1),
            "ollama_metrics": self.ollama_client.get_metrics() if self._initialized else {}
        }
    
    async def close(self):
        """Cleanup resources"""
        if self.ollama_client:
            await self.ollama_client.close()

# Global instances
ollama_client = OllamaLLMClient()
nlp_utils = NLPUtils()

# Provide backward-compatible alias for legacy imports
try:
    NLPProcessor
except NameError:
    NLPProcessor = NLPUtils

try:
    __all__.append("NLPProcessor")
except NameError:
    __all__ = getattr(globals(), "__all__", [])
    __all__.append("NLPProcessor")

# Convenience functions
async def get_ollama_client() -> OllamaLLMClient:
    return ollama_client

async def get_nlp_utils() -> NLPUtils:
    return nlp_utils

async def init_nlp_utils():
    await nlp_utils.initialize()

async def close_nlp_utils():
    await nlp_utils.close()
