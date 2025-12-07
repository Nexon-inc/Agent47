#!/usr/bin/env python3
"""
Simple Ollama LLM Test
Quick test to verify Ollama service is working
"""

import asyncio
import aiohttp
import json
import time

async def test_ollama_simple():
    """Simple test for Ollama LLM"""
    base_url = "http://localhost:8008"
    
    print("🧪 Testing Ollama LLM Service...")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health Check
        print("\n1. Health Check...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return
        
        # Test 2: Simple Chat
        print("\n2. Simple Chat Test...")
        try:
            start_time = time.time()
            async with session.post(
                f"{base_url}/chat",
                json={
                    "message": "Hello! Can you tell me about AI in business, also how they can assist automate business?",
                    "max_tokens": 15000,
                    "temperature": 3.0
                },
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    print(f"✅ Chat successful ({(response_time):.2f}s)")
                    print(f"Response length: {len(response_text)} characters")
                    print(f"Response preview: {response_text[:700]}...")
                    print(f"Tokens used: {data.get('usage', {}).get('total_tokens', 0)}")
                else:
                    print(f"❌ Chat failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
        except Exception as e:
            print(f"❌ Chat error: {e}")
        
        # Test 3: Business Question
        print("\n3. Business Question Test...")
        try:
            start_time = time.time()
            async with session.post(
                f"{base_url}/chat",
                json={
                    "message": "I run a SaaS company with 1000 customers. How can I scale to 10,000 customers?",
                    "max_tokens": 18000,
                    "temperature": 3.0
                },
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "")
                    print(f"✅ Business question successful ({(response_time):.2f}s)")
                    print(f"Response length: {len(response_text)} characters")
                    print(f"Response preview: {response_text[:800]}...")
                else:
                    print(f"❌ Business question failed: {response.status}")
        except Exception as e:
            print(f"❌ Business question error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_simple())
