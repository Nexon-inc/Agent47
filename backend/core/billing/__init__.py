from .billing_manager import BillingManager, get_billing, init_billing
from .paystack_integration import PaystackIntegration, get_paystack
from .subscription_manager import SubscriptionManager, get_subscription_manager
from .usage_tracker import UsageTracker, get_usage_tracker
from .billing_plans import BillingPlans, get_billing_plans

__all__ = [
    "BillingManager",
    "get_billing", 
    "init_billing",
    "PaystackIntegration",
    "get_paystack",
    "SubscriptionManager",
    "get_subscription_manager",
    "UsageTracker",
    "get_usage_tracker",
    "BillingPlans",
    "get_billing_plans"
]

# Backwards-compatible alias used by some admin modules
def get_billing_manager():
    return get_billing()

__all__.append("get_billing_manager")
