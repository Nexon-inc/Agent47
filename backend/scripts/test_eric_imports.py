"""
Quick diagnostic to test if Eric model imports work correctly
"""

import sys
sys.path.insert(0, '/app')  # Cloud Run path

try:
    # Test 1: Import the models module
    from agents.eric.app import models
    print("✅ Successfully imported agents.eric.app.models")
    
    # Test 2: Check if EricCustomerProfile exists
    if hasattr(models, 'EricCustomerProfile'):
        print("✅ EricCustomerProfile exists in models")
    else:
        print("❌ EricCustomerProfile NOT FOUND in models")
    
    # Test 3: Check if EricDealClosing exists
    if hasattr(models, 'EricDealClosing'):
        print("✅ EricDealClosing exists in models")
    else:
        print("❌ EricDealClosing NOT FOUND in models")
    
    # Test 4: Try the aliased import
    from agents.eric.app.models import EricCustomerProfile as CustomerProfile
    print(f"✅ Successfully imported EricCustomerProfile as CustomerProfile: {CustomerProfile}")
    
    # Test 5: Try the deal closing import
    from agents.eric.app.models import EricDealClosing as DealClosing
    print(f"✅ Successfully imported EricDealClosing as DealClosing: {DealClosing}")
    
    print("\n✅ ALL TESTS PASSED - Imports are working correctly!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
