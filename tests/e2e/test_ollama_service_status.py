#!/usr/bin/env python3
"""
Ollama Service Status Checker
Checks if Ollama service is running and provides diagnostic information
"""

import asyncio
import aiohttp
import subprocess
import json
import time
from datetime import datetime

async def check_ollama_service():
    """Check Ollama service status and provide diagnostics"""
    
    print("🔍 Ollama LLM Service Status Checker")
    print("=" * 50)
    
    # Check 1: Docker Container Status
    print("\n1. Docker Container Status:")
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=agent47-ollama-llm", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Docker command successful:")
            print(result.stdout)
        else:
            print("❌ Docker command failed:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Docker check error: {e}")
    
    # Check 2: Port Availability
    print("\n2. Port 8008 Availability:")
    try:
        result = subprocess.run(
            ["netstat", "-an", "|", "findstr", ":8008"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if ":8008" in result.stdout:
            print("✅ Port 8008 is in use:")
            print(result.stdout)
        else:
            print("⚠️  Port 8008 appears to be free")
    except Exception as e:
        print(f"❌ Port check error: {e}")
    
    # Check 3: HTTP Service Check
    print("\n3. HTTP Service Check:")
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8008/health", timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Ollama service is responding!")
                        print(f"   Status: {data.get('status', 'unknown')}")
                        print(f"   Model loaded: {data.get('model_loaded', False)}")
                        print(f"   Ollama available: {data.get('ollama_available', False)}")
                        return True
                    else:
                        print(f"❌ Service responded with status: {response.status}")
                        return False
            except asyncio.TimeoutError:
                print("⏰ Service request timed out (5s)")
                return False
            except aiohttp.ClientConnectorError:
                print("❌ Cannot connect to service (connection refused)")
                return False
    except Exception as e:
        print(f"❌ HTTP check error: {e}")
        return False

async def test_basic_functionality():
    """Test basic Ollama functionality if service is running"""
    print("\n4. Basic Functionality Test:")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test simple chat
            test_message = "Hello! Can you tell me about AI in business automation?"
            
            start_time = time.time()
            async with session.post(
                "http://localhost:8008/chat",
                json={
                    "message": test_message,
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
                    print("✅ Basic chat test successful!")
                    print(f"   Response time: {response_time:.2f} seconds")
                    print(f"   Response length: {len(response_text)} characters")
                    print(f"   Tokens used: {data.get('usage', {}).get('total_tokens', 0)}")
                    print(f"   Response preview: {response_text[:150]}...")
                    return True
                else:
                    print(f"❌ Chat test failed with status: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
    except asyncio.TimeoutError:
        print("⏰ Chat test timed out (600s)")
        return False
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False

def provide_troubleshooting_tips():
    """Provide troubleshooting tips"""
    print("\n🔧 Troubleshooting Tips:")
    print("=" * 30)
    
    print("\nIf the service is not running:")
    print("1. Start Docker Desktop")
    print("2. Run: docker-compose up ollama-llm -d")
    print("3. Wait 2-5 minutes for initialization")
    print("4. Check logs: docker logs agent47-ollama-llm")
    
    print("\nIf the service is slow:")
    print("1. First request is always slow (model loading)")
    print("2. Ensure 8GB+ RAM allocated to Docker")
    print("3. Check system resources")
    
    print("\nIf you get connection errors:")
    print("1. Verify port 8008 is not blocked")
    print("2. Check firewall settings")
    print("3. Restart the container")
    
    print("\nExpected startup sequence:")
    print("1. Container starts (30 seconds)")
    print("2. Ollama daemon starts (1-2 minutes)")
    print("3. Llama 3 8B model downloads (5-15 minutes, first time only)")
    print("4. FastAPI service starts (30 seconds)")
    print("5. Service ready for requests")

async def main():
    """Main status check"""
    service_running = await check_ollama_service()
    
    if service_running:
        functionality_working = await test_basic_functionality()
        
        if functionality_working:
            print("\n🎉 SUCCESS: Ollama LLM service is ready!")
            print("You can now run the comprehensive tests:")
            print("  python tests/e2e/test_ollama_llm_comprehensive.py")
        else:
            print("\n⚠️  Service is running but functionality test failed")
            provide_troubleshooting_tips()
    else:
        print("\n❌ Ollama LLM service is not running")
        provide_troubleshooting_tips()
    
    print(f"\n📊 Status check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
