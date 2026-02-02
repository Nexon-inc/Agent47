
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import select
from core.database import get_db, async_session_maker
from core.integrations.integration_manager import get_integration_manager, IntegrationManager
from core.integrations.models import Integration, IntegrationCredentials, IntegrationStatus, CredentialStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_fix():
    print("Verifying IntegrationManager fix...")
    
    try:
        manager = await get_integration_manager()
        
        # We need a user ID. We'll try to find one or use a dummy.
        # But first let's check if the method exists
        if not hasattr(manager, 'get_user_integration_usage'):
            print("❌ FAILURE: get_user_integration_usage method missing on IntegrationManager!")
            return
            
        print("✅ SUCCESS: get_user_integration_usage method exists.")
        
        # Test calling it (it requires DB access)
        # We'll mock a user_id = 1
        print("Testing method execution...")
        results = await manager.get_user_integration_usage(user_id=1)
        
        print(f"Method returned: {results}")
        
        # Check if results are iterable and have expected attributes
        if isinstance(results, list):
            print("✅ Method returned a list.")
            if len(results) > 0:
                item = results[0]
                try:
                    # Check attribute access
                    print(f"Sample Item attributes: id={item.integration_id}, name={item.integration_name}, status={item.status}, cred_status={item.credentials_status}")
                    print("✅ SUCCESS: Result items support attribute access.")
                except AttributeError as e:
                    print(f"❌ FAILURE: Result items missing attributes: {e}")
            else:
                print("⚠️ List is empty (no integrations found for user 1), but method execution worked.")
        else:
             print(f"❌ FAILURE: Method returned {type(results)}, expected list.")

    except Exception as e:
        print(f"❌ CRITICAL FAILURE during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_fix())
