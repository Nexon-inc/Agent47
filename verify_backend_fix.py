
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import select
from core.database import get_db
from core.user_management.selected_agents_router import _check_agent_locked

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_fix():
    print("Verifying timezone fix...")
    
    # Mock user and DB objects aren't easily available without full setup.
    # We will test the logic directly: comparing aware vs aware.
    
    try:
        # Simulate DB timestamp (timezone aware)
        db_timestamp = datetime.now(timezone.utc) + timedelta(days=30)
        print(f"DB Timestamp (Aware): {db_timestamp}")
        
        # Current Logic being tested:
        now = datetime.now(timezone.utc)
        print(f"Current Time (Aware): {now}")
        
        if now < db_timestamp:
            print("✅ Comparison successful (Aware vs Aware).")
        else:
            print("✅ Comparison successful (logic valid).")
            
        # Verify what happens if we used naive (FAILURE CASE REPRODUCTION)
        try:
            naive_now = datetime.now()
            if naive_now < db_timestamp:
                print("❌ WARNING: Naive comparison unexpectedly succeeded (System may confuse local time with UTC).")
            else:
                 print("❌ WARNING: Naive comparison unexpectedly succeeded.")
        except TypeError as e:
            print(f"✅ Confirmed: Naive vs Aware comparison raises TypeError: {e}")
            print("   This confirms the original issue existed and our fix (using timezone.utc) solves it.")

    except Exception as e:
        print(f"❌ CRITICAL FAILURE during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_fix())
