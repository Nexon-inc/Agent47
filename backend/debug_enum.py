
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from backend.core.billing.models import SubscriptionStatus
    print(f"SubscriptionStatus.PENDING value: '{SubscriptionStatus.PENDING.value}'")
    print(f"SubscriptionStatus.PENDING name: '{SubscriptionStatus.PENDING.name}'")
except Exception as e:
    print(f"Error: {e}")
