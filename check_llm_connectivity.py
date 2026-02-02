
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from core.ai.llm_service_pool import get_llm_service_pool, LLMRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_llm():
    print("Checking LLM connectivity...")
    try:
        pool = await get_llm_service_pool()
        print("LLM Pool initialized.")
        
        status = pool.get_service_status()
        print(f"Service Status: {status}")
        
        request = LLMRequest(
            messages=[{"role": "user", "content": "Say hello!"}],
            max_tokens=50
        )
        
        print("Sending test request...")
        response = await pool.generate_text(request)
        
        if response.success:
            print(f"✅ LLM SUCCESS: {response.content}")
            print(f"Service Used: {response.service_used}")
        else:
            print(f"❌ LLM FAILURE: {response.error}")
            
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_llm())
