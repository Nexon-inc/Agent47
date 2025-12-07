#!/usr/bin/env python3
"""
Ollama LLM Service for Agent47
Provides powerful Llama 3 8B capabilities for all agents
"""

import os
import sys
import logging
import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = 20000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

class ChatResponse(BaseModel):
    response: str
    model: str
    usage: Dict[str, int]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    ollama_available: bool
    memory_usage: Dict[str, Any]

class OllamaLLMService:
    """Ollama LLM Service for Agent47 with Llama 3 8B"""
    
    def __init__(self):
        self.ollama_url = f"http://{os.getenv('OLLAMA_HOST', 'localhost')}:{os.getenv('OLLAMA_PORT', '11434')}"
        self.model_name = "llama3.2:3b"  # Smaller model that fits in available memory
        self.model_loaded = False
        self.ollama_available = False
        
    async def initialize(self):
        """Initialize the Ollama LLM service"""
        try:
            logger.info("Initializing Ollama LLM service...")
            
            # Check if Ollama is available
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.ollama_url}/api/tags") as response:
                        if response.status == 200:
                            self.ollama_available = True
                            logger.info("Ollama service is available")
                        else:
                            logger.error("Ollama service not responding")
                            raise Exception("Ollama service not available")
                except Exception as e:
                    logger.error(f"Failed to connect to Ollama: {e}")
                    raise
            
            # Check if Llama 3 8B model is available
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.ollama_url}/api/tags") as response:
                        if response.status == 200:
                            models_data = await response.json()
                            models = models_data.get("models", [])
                            model_names = [model.get("name", "") for model in models]
                            
                            if self.model_name in model_names:
                                self.model_loaded = True
                                logger.info(f"Llama 3 8B model is available")
                            else:
                                logger.info(f"Llama 3 8B model not found, will download automatically")
                                # Model will be downloaded on first use
                                self.model_loaded = True
                        else:
                            logger.error("Failed to check available models")
                            raise Exception("Failed to check models")
                except Exception as e:
                    logger.error(f"Failed to check models: {e}")
                    raise
            
            logger.info("Ollama LLM service initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM service: {e}")
            raise
    
    async def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 20000,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> ChatResponse:
        """Generate a response using Ollama Llama 3 8B"""
        
        if not self.ollama_available:
            raise HTTPException(status_code=503, detail="Ollama service not available")
        
        try:
            # Prepare input
            input_text = message
            if context:
                input_text = f"Context: {context}\nMessage: {message}"
            
            # Prepare Ollama request
            ollama_request = {
                "model": self.model_name,
                "prompt": input_text,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens,
                    "stop": ["</s>"],  # Only stop on end-of-sequence token, not on newlines
                    "repeat_penalty": 1.05,
                    "repeat_last_n": 128,
                    "top_k": 40,
                    "tfs_z": 1.0,
                    "typical_p": 1.0
                }
            }
            
            # Send request to Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=ollama_request,
                    timeout=aiohttp.ClientTimeout(total=1800)  # 30 minute timeout for long responses
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="Ollama request failed")
                    
                    result = await response.json()
                    
                    # Extract response
                    response_text = result.get("response", "")
                    
                    # Calculate usage (approximate)
                    prompt_tokens = len(input_text.split())  # Rough estimate
                    completion_tokens = len(response_text.split())  # Rough estimate
                    total_tokens = prompt_tokens + completion_tokens
            
            return ChatResponse(
                        response=response_text,
                        model="llama3:8b",
                usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        memory_info = {}
        
        # System memory
        import psutil
        memory_info["system"] = {
            "total": psutil.virtual_memory().total / 1024**3,  # GB
            "available": psutil.virtual_memory().available / 1024**3,  # GB
            "used": psutil.virtual_memory().used / 1024**3,  # GB
            "percent": psutil.virtual_memory().percent
        }
        
        return memory_info

# Initialize FastAPI app
app = FastAPI(
    title="Ollama LLM Service",
    description="Powerful Llama 3 8B LLM service for Agent47",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
ollama_service = OllamaLLMService()

@app.on_event("startup")
async def startup_event():
    """Initialize the service on startup"""
    await ollama_service.initialize()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if ollama_service.model_loaded else "unhealthy",
        model_loaded=ollama_service.model_loaded,
        ollama_available=ollama_service.ollama_available,
        memory_usage=ollama_service.get_memory_usage()
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for generating responses"""
    return await ollama_service.generate_response(
        message=request.message,
        context=request.context,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p
    )

@app.get("/chat")
async def chat_get(message: str = "Hello, how are you?"):
    """GET endpoint for testing chat functionality"""
    request = ChatRequest(message=message)
    return await ollama_service.generate_response(
        message=request.message,
        context=request.context,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Ollama LLM Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": ollama_service.model_loaded,
        "model": "llama3.2:3b",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=False,
        log_level="info"
    )
