import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from ..database.models import User
from .models import (
    Subscription, SubscriptionStatus, Payment, PaymentStatus, 
    BillingPlan, BillingTier, Usage
)
from ..database.connection import get_database
from .paystack_integration import get_paystack
from .billing_plans import get_billing_plans

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Manages user subscriptions and billing cycles for Agent47."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize the subscription manager."""
        if self._initialized:
            return
        
        # Initialize dependencies
        await get_paystack()
        await get_billing_plans()
        
        self._initialized = True
        logger.info("Subscription manager initialized successfully")
    
    async def create_subscription(self, user_id: int, tier: BillingTier, payment_method: str = "paystack", billing_period: str = "monthly") -> Dict[str, Any]:
        """Create a new subscription for a user."""
        db = get_database()
        paystack = await get_paystack()
        billing_plans = await get_billing_plans()
        
        # Get user and plan details
        async with db.get_session() as session:
            user = await session.execute(select(User).where(User.id == user_id))
            user = user.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")
            
            plan = await billing_plans.get_plan_by_tier(tier)
            if not plan:
                raise ValueError("Billing plan not found")
            
            # Check if user already has an active subscription
            existing_subscription = await self.get_active_subscription(user_id)
            if existing_subscription:
                # If they already have this tier, block it. If it's a different tier, we'll allow the "pending" one to replace it
                existing_plan_id = existing_subscription.plan_id
                # (Simple check: we'll allow replacing any active subscription for now to facilitate upgrades)
                logger.info(f"User {user_id} has existing subscription {existing_subscription.id}. Proceeding with new subscription for tier {tier.value}.")
            
            # Calculate subscription dates based on billing period
            start_date = datetime.utcnow()
            if billing_period == "yearly":
                end_date = start_date + timedelta(days=365)
                # Use yearly price if available
                price = getattr(plan, 'yearly_price_usd', None) or (plan.price_usd * 12 * 0.9)  # 10% discount
            else:
                end_date = start_date + timedelta(days=30)  # Monthly billing
                price = plan.price_usd
            
            # Create subscription record
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                status=SubscriptionStatus.PENDING,
                start_date=start_date,
                end_date=end_date,
                auto_renew=True
            )
            
            session.add(subscription)
            await session.commit()
            
            # Create Paystack payment if using Paystack AND price > 0
            if payment_method == "paystack" and price > 0:
                try:
                    from ..config import settings
                    
                    # Initialize Paystack transaction to get payment URL
                    reference = f"SUB_{subscription.id}_{int(datetime.utcnow().timestamp())}"
                    callback_url = f"{settings.frontend_url}/billing/verify"
                    
                    # Initialize transaction with Paystack
                    transaction = await paystack.initialize_transaction(
                        email=user.email,
                        amount=price,
                        reference=reference,
                        callback_url=callback_url,
                        metadata={
                            "subscription_id": subscription.id,
                            "user_id": user_id,
                            "tier": tier.value,
                            "plan_id": plan.id,
                            "billing_period": billing_period
                        }
                    )
                    
                    # Update subscription with Paystack reference
                    subscription.paystack_reference = reference
                    subscription.paystack_customer_code = transaction.get("customer", {}).get("customer_code", "")
                    
                    session.add(subscription)
                    await session.commit()
                    
                    logger.info(f"Initialized Paystack transaction for subscription {subscription.id}, tier {tier.value}")
                    
                    # Return payment URL for frontend redirect
                    payment_url = transaction.get("authorization_url")
                    if not payment_url:
                        raise ValueError("Paystack did not return authorization URL")
                    
                    return {
                        "subscription_id": subscription.id,
                        "status": "pending",
                        "tier": tier.value,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "authorization_url": payment_url,
                        "reference": reference
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to initialize Paystack transaction: {e}")
                    # Rollback subscription creation
                    await session.rollback()
                    raise Exception(f"Failed to initialize payment: {e}")
            
            # For Free tier or non-Paystack subscriptions (manual/offline)
            subscription.status = SubscriptionStatus.ACTIVE
            
            # Update user tier directly if it's Free (paid tiers update upon verification)
            if tier == BillingTier.FREE:
                user.tier = tier.value
                session.add(user)
                
            session.add(subscription)
            await session.commit()
            
            return {
                "subscription_id": subscription.id,
                "status": "active",
                "tier": tier.value,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
    
    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get the active subscription for a user."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Subscription).where(
                    and_(
                        Subscription.user_id == user_id,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user subscription details with plan information."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Subscription, BillingPlan).join(
                    BillingPlan, Subscription.plan_id == BillingPlan.id
                ).where(Subscription.user_id == user_id)
            )
            
            subscription_data = result.first()
            if subscription_data:
                subscription, plan = subscription_data
                return {
                    "id": subscription.id,
                    "tier": plan.tier.value,
                    "status": subscription.status.value,
                    "start_date": subscription.start_date.isoformat(),
                    "end_date": subscription.end_date.isoformat(),
                    "auto_renew": subscription.auto_renew,
                    "plan_name": plan.name,
                    "price_usd": plan.price_usd,
                    "features": plan.features
                }
            return None
    
    async def cancel_subscription(self, user_id: int, reason: str = "User requested cancellation") -> bool:
        """Cancel a user's subscription."""
        db = get_database()
        paystack = await get_paystack()
        
        async with db.get_session() as session:
            subscription = await self.get_active_subscription(user_id)
            if not subscription:
                raise ValueError("No active subscription found")
            
            # Cancel in Paystack if applicable
            if subscription.paystack_subscription_code:
                try:
                    # Cancel subscription through Paystack API
                    from core.billing.paystack_integration import PaystackIntegration
                    paystack = PaystackIntegration()
                    
                    # Disable the subscription in Paystack
                    cancel_result = await paystack.disable_subscription(subscription.paystack_subscription_code)
                    
                    if cancel_result.get("success"):
                        logger.info(f"Subscription {subscription.paystack_subscription_code} successfully cancelled in Paystack")
                    else:
                        logger.warning(f"Failed to cancel Paystack subscription: {cancel_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.warning(f"Failed to cancel Paystack subscription: {e}")
            
            # Update subscription status
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.updated_at = datetime.utcnow()
            
            session.add(subscription)
            await session.commit()
            
            logger.info(f"Cancelled subscription for user {user_id}: {reason}")
            return True
    
    async def renew_subscription(self, user_id: int) -> bool:
        """Renew a user's subscription."""
        db = get_database()
        
        async with db.get_session() as session:
            subscription = await self.get_active_subscription(user_id)
            if not subscription:
                raise ValueError("No active subscription found")
            
            # Calculate new dates
            current_end = subscription.end_date
            new_end = current_end + timedelta(days=30)
            
            subscription.end_date = new_end
            subscription.updated_at = datetime.utcnow()
            
            session.add(subscription)
            await session.commit()
            
            logger.info(f"Renewed subscription for user {user_id} until {new_end}")
            return True
    
    async def upgrade_subscription(self, user_id: int, new_tier: BillingTier) -> Dict[str, Any]:
        """Upgrade a user's subscription to a higher tier."""
        db = get_database()
        billing_plans = await get_billing_plans()
        
        async with db.get_session() as session:
            current_subscription = await self.get_active_subscription(user_id)
            if not current_subscription:
                raise ValueError("No active subscription found")
            
            current_plan = await session.execute(
                select(BillingPlan).where(BillingPlan.id == current_subscription.plan_id)
            )
            current_plan = current_plan.scalar_one_or_none()
            
            new_plan = await billing_plans.get_plan_by_tier(new_tier)
            if not new_plan:
                raise ValueError("New billing plan not found")
            
            # Check if this is actually an upgrade
            tier_hierarchy = [BillingTier.FREE, BillingTier.STARTER, BillingTier.PRO]
            current_index = tier_hierarchy.index(current_plan.tier)
            new_index = tier_hierarchy.index(new_tier)
            
            if new_index <= current_index:
                raise ValueError("Can only upgrade to a higher tier")
            
            # Calculate pro-rated amount for the upgrade
            days_remaining = (current_subscription.end_date - datetime.utcnow()).days
            if days_remaining > 0:
                daily_rate_current = current_plan.price_usd / 30
                daily_rate_new = new_plan.price_usd / 30
                upgrade_cost = (daily_rate_new - daily_rate_current) * days_remaining
            else:
                upgrade_cost = new_plan.price_usd
            
            # Create payment record for upgrade
            payment = Payment(
                subscription_id=current_subscription.id,
                amount_usd=upgrade_cost,
                currency="USD",
                status=PaymentStatus.PENDING,
                payment_method="upgrade",
                metadata={
                    "upgrade_from": current_plan.tier.value,
                    "upgrade_to": new_tier.value,
                    "days_remaining": days_remaining,
                    "upgrade_type": "tier_upgrade"
                }
            )
            
            session.add(payment)
            
            # Update subscription plan
            current_subscription.plan_id = new_plan.id
            current_subscription.updated_at = datetime.utcnow()
            
            session.add(current_subscription)
            await session.commit()
            
            logger.info(f"Upgraded subscription for user {user_id} from {current_plan.tier.value} to {new_tier.value}")
            
            return {
                "subscription_id": current_subscription.id,
                "new_tier": new_tier.value,
                "upgrade_cost": upgrade_cost,
                "days_remaining": days_remaining,
                "payment_id": payment.id
            }
    
    async def downgrade_subscription(self, user_id: int, new_tier: BillingTier) -> bool:
        """Downgrade a user's subscription to a lower tier."""
        db = get_database()
        billing_plans = await get_billing_plans()
        
        async with db.get_session() as session:
            current_subscription = await self.get_active_subscription(user_id)
            if not current_subscription:
                raise ValueError("No active subscription found")
            
            current_plan = await session.execute(
                select(BillingPlan).where(BillingPlan.id == current_subscription.plan_id)
            )
            current_plan = current_plan.scalar_one_or_none()
            
            new_plan = await billing_plans.get_plan_by_tier(new_tier)
            if not new_plan:
                raise ValueError("New billing plan not found")
            
            # Check if this is actually a downgrade
            tier_hierarchy = [BillingTier.FREE, BillingTier.STARTER, BillingTier.PRO]
            current_index = tier_hierarchy.index(current_plan.tier)
            new_index = tier_hierarchy.index(new_tier)
            
            if new_index >= current_index:
                raise ValueError("Can only downgrade to a lower tier")
            
            # Update subscription plan
            current_subscription.plan_id = new_plan.id
            current_subscription.updated_at = datetime.utcnow()
            
            session.add(current_subscription)
            await session.commit()
            
            logger.info(f"Downgraded subscription for user {user_id} from {current_plan.tier.value} to {new_tier.value}")
            return True
    
    async def get_subscription_payments(self, subscription_id: int) -> List[Dict[str, Any]]:
        """Get all payments for a subscription."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(Payment).where(Payment.subscription_id == subscription_id)
                .order_by(Payment.created_at.desc())
            )
            
            payments = result.scalars().all()
            return [
                {
                    "id": payment.id,
                    "amount_usd": payment.amount_usd,
                    "currency": payment.currency,
                    "status": payment.status.value,
                    "payment_method": payment.payment_method,
                    "created_at": payment.created_at.isoformat(),
                    "paystack_reference": payment.paystack_reference
                }
                for payment in payments
            ]
    
    async def check_subscription_expiry(self) -> List[Dict[str, Any]]:
        """Check for subscriptions that are expiring soon."""
        db = get_database()
        warning_days = 7  # Warn 7 days before expiry
        
        async with db.get_session() as session:
            warning_date = datetime.utcnow() + timedelta(days=warning_days)
            
            result = await session.execute(
                select(Subscription, User, BillingPlan).join(
                    User, Subscription.user_id == User.id
                ).join(
                    BillingPlan, Subscription.plan_id == BillingPlan.id
                ).where(
                    and_(
                        Subscription.status == SubscriptionStatus.ACTIVE,
                        Subscription.end_date <= warning_date,
                        Subscription.end_date > datetime.utcnow()
                    )
                )
            )
            
            expiring_subscriptions = []
            for subscription, user, plan in result:
                days_until_expiry = (subscription.end_date - datetime.utcnow()).days
                expiring_subscriptions.append({
                    "user_id": user.id,
                    "user_email": user.email,
                    "subscription_id": subscription.id,
                    "tier": plan.tier.value,
                    "days_until_expiry": days_until_expiry,
                    "end_date": subscription.end_date.isoformat(),
                    "auto_renew": subscription.auto_renew
                })
            
            return expiring_subscriptions
    
    async def process_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """Process expired subscriptions and update their status."""
        db = get_database()
        
        async with db.get_session() as session:
            expired_subscriptions = await session.execute(
                select(Subscription, User, BillingPlan).join(
                    User, Subscription.user_id == User.id
                ).join(
                    BillingPlan, Subscription.plan_id == BillingPlan.id
                ).where(
                    and_(
                        Subscription.status == SubscriptionStatus.ACTIVE,
                        Subscription.end_date <= datetime.utcnow()
                    )
                )
            )
            
            processed = []
            for subscription, user, plan in expired_subscriptions:
                if subscription.auto_renew:
                    # Attempt to renew
                    try:
                        await self.renew_subscription(user.id)
                        subscription.status = SubscriptionStatus.ACTIVE
                        processed.append({
                            "user_id": user.id,
                            "subscription_id": subscription.id,
                            "action": "renewed",
                            "new_end_date": subscription.end_date.isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Failed to renew subscription {subscription.id}: {e}")
                        subscription.status = SubscriptionStatus.EXPIRED
                        processed.append({
                            "user_id": user.id,
                            "subscription_id": subscription.id,
                            "action": "expired",
                            "error": str(e)
                        })
                else:
                    # Mark as expired
                    subscription.status = SubscriptionStatus.EXPIRED
                    processed.append({
                        "user_id": user.id,
                        "subscription_id": subscription.id,
                        "action": "expired",
                        "reason": "Auto-renewal disabled"
                    })
                
                subscription.updated_at = datetime.utcnow()
                session.add(subscription)
            
            await session.commit()
            logger.info(f"Processed {len(processed)} expired subscriptions")
            return processed
    
    async def get_subscription_statistics(self) -> Dict[str, Any]:
        """Get subscription statistics for the system."""
        db = get_database()
        
        async with db.get_session() as session:
            # Total subscriptions by status
            status_counts = await session.execute(
                select(Subscription.status, db.func.count(Subscription.id))
                .group_by(Subscription.status)
            )
            
            status_stats = {}
            for status, count in status_counts:
                status_stats[status.value] = count
            
            # Total subscriptions by tier
            tier_counts = await session.execute(
                select(BillingPlan.tier, db.func.count(Subscription.id))
                .join(BillingPlan, Subscription.plan_id == BillingPlan.id)
                .group_by(BillingPlan.tier)
            )
            
            tier_stats = {}
            for tier, count in tier_counts:
                tier_stats[tier.value] = count
            
            # Revenue statistics
            total_revenue = await session.execute(
                select(db.func.sum(Payment.amount_usd))
                .where(Payment.status == PaymentStatus.SUCCESSFUL)
            )
            total_revenue = total_revenue.scalar() or 0
            
            # Monthly recurring revenue
            current_month = datetime.utcnow().strftime("%Y-%m")
            monthly_revenue = await session.execute(
                select(db.func.sum(Payment.amount_usd))
                .where(
                    and_(
                        Payment.status == PaymentStatus.SUCCESSFUL,
                        db.func.date_trunc('month', Payment.created_at) == current_month
                    )
                )
            )
            monthly_revenue = monthly_revenue.scalar() or 0
            
            return {
                "total_subscriptions": sum(status_stats.values()),
                "subscriptions_by_status": status_stats,
                "subscriptions_by_tier": tier_stats,
                "total_revenue_usd": total_revenue,
                "monthly_recurring_revenue_usd": monthly_revenue,
                "current_month": current_month
            }

# Global instance
subscription_manager = SubscriptionManager()

async def get_subscription_manager() -> SubscriptionManager:
    """Get the global subscription manager instance."""
    if not subscription_manager._initialized:
        await subscription_manager.initialize()
    return subscription_manager
