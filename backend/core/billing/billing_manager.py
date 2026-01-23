import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, case
from ..database.models import User, BillingRecord
from .models import (
    Subscription, SubscriptionStatus, Payment, PaymentStatus, 
    BillingPlan, BillingTier, Usage
)
from ..database.connection import get_database
from .paystack_integration import get_paystack
from .billing_plans import get_billing_plans
from .subscription_manager import get_subscription_manager
from .usage_tracker import get_usage_tracker
from ..config import settings

logger = logging.getLogger(__name__)

class BillingManager:
    """Main billing manager that orchestrates all billing operations for Agent47."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize the billing manager and all its components."""
        if self._initialized:
            return
        
        # Initialize all billing components
        await get_paystack()
        await get_billing_plans()
        await get_subscription_manager()
        await get_usage_tracker()
        
        self._initialized = True
        logger.info("Billing manager initialized successfully")
    
    async def create_subscription(self, user_id: int, tier: BillingTier, payment_method: str = "paystack", billing_period: str = "monthly") -> Dict[str, Any]:
        """Create a new subscription for a user."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.create_subscription(user_id, tier, payment_method, billing_period)
    
    async def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's current subscription details."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.get_user_subscription(user_id)
    
    async def cancel_subscription(self, user_id: int, reason: str = "User requested cancellation") -> bool:
        """Cancel a user's subscription."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.cancel_subscription(user_id, reason)
    
    async def upgrade_subscription(self, user_id: int, new_tier: BillingTier) -> Dict[str, Any]:
        """Upgrade a user's subscription to a higher tier."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.upgrade_subscription(user_id, new_tier)
    
    async def downgrade_subscription(self, user_id: int, new_tier: BillingTier) -> bool:
        """Downgrade a user's subscription to a lower tier."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.downgrade_subscription(user_id, new_tier)
    
    async def process_payment(self, user_id: int, amount_usd: float, payment_method: str = "paystack", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a payment for a user."""
        db = get_database()
        paystack = await get_paystack()
        
        try:
            async with db.get_session() as session:
                # Get user details
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                if not user:
                    raise ValueError("User not found")
                
                # Get active subscription
                subscription = await session.execute(
                    select(Subscription).where(
                        and_(
                            Subscription.user_id == user_id,
                            Subscription.status == SubscriptionStatus.ACTIVE
                        )
                    )
                )
                subscription = subscription.scalar_one_or_none()
                
                if not subscription:
                    raise ValueError("No active subscription found")
                
                # Create payment record
                payment = Payment(
                    subscription_id=subscription.id,
                    amount_usd=amount_usd,
                    currency="USD",
                    status=PaymentStatus.PENDING,
                    payment_method=payment_method,
                    metadata=metadata or {}
                )
                
                session.add(payment)
                await session.commit()
                
                # Process payment through Paystack if applicable
                if payment_method == "paystack":
                    try:
                        # Initialize transaction
                        reference = f"PAY_{payment.id}_{int(datetime.utcnow().timestamp())}"
                        callback_url = f"{settings.billing.webhook_base_url}/billing/webhook/paystack"
                        
                        transaction = await paystack.initialize_transaction(
                            email=user.email,
                            amount=amount_usd,
                            reference=reference,
                            callback_url=callback_url,
                            metadata={
                                "payment_id": payment.id,
                                "user_id": user_id,
                                "subscription_id": subscription.id
                            }
                        )
                        
                        # Update payment with Paystack reference
                        payment.paystack_reference = reference
                        payment.metadata["paystack_authorization_url"] = transaction.get("authorization_url")
                        payment.metadata["paystack_access_code"] = transaction.get("access_code")
                        
                        session.add(payment)
                        await session.commit()
                        
                        return {
                            "payment_id": payment.id,
                            "status": "pending",
                            "authorization_url": transaction.get("authorization_url"),
                            "reference": reference,
                            "amount_usd": amount_usd
                        }
                        
                    except Exception as e:
                        logger.error(f"Failed to process Paystack payment: {e}")
                        payment.status = PaymentStatus.FAILED
                        payment.metadata["error"] = str(e)
                        session.add(payment)
                        await session.commit()
                        
                        raise Exception(f"Payment processing failed: {e}")
                
                # For non-Paystack payments, mark as successful
                payment.status = PaymentStatus.SUCCESSFUL
                session.add(payment)
                await session.commit()
                
                return {
                    "payment_id": payment.id,
                    "status": "successful",
                    "amount_usd": amount_usd
                }
                
        except Exception as e:
            logger.error(f"Failed to process payment for user {user_id}: {e}")
            raise
    
    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a payment using its reference."""
        paystack = await get_paystack()
        
        try:
            # Verify with Paystack
            transaction_data = await paystack.verify_transaction(reference)
            
            # Update payment status in database
            db = get_database()
            async with db.get_session() as session:
                payment = await session.execute(
                    select(Payment).where(Payment.paystack_reference == reference)
                )
                payment = payment.scalar_one_or_none()
                
                if payment:
                    if transaction_data.get("status") == "success":
                        payment.status = PaymentStatus.SUCCESSFUL
                        payment.paystack_transaction_id = str(transaction_data.get("id"))
                    else:
                        payment.status = PaymentStatus.FAILED
                    
                    payment.metadata["verification_response"] = transaction_data
                    payment.updated_at = datetime.utcnow()
                    
                    session.add(payment)
                    await session.commit()
                    
                    return {
                        "payment_id": payment.id,
                        "status": payment.status.value,
                        "transaction_data": transaction_data
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Payment not found"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to verify payment {reference}: {e}")
            raise
    
    async def get_payment_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get payment history for a user."""
        db = get_database()
        
        async with db.get_session() as session:
            result = await session.execute(
                select(Payment).join(
                    Subscription, Payment.subscription_id == Subscription.id
                ).where(
                    Subscription.user_id == user_id
                ).order_by(
                    Payment.created_at.desc()
                ).limit(limit)
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
                    "paystack_reference": payment.paystack_reference,
                    "metadata": payment.metadata
                }
                for payment in payments
            ]
    
    async def get_user_usage(self, user_id: int, month: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a user."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.get_user_usage(user_id, month)
    
    async def check_usage_limits(self, user_id: int) -> Dict[str, Any]:
        """Check if user has exceeded usage limits."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.check_usage_limits(user_id)
    
    async def track_api_call(self, user_id: int, endpoint: str, response_time: float, success: bool = True) -> bool:
        """Track an API call made by a user."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.track_api_call(user_id, endpoint, response_time, success)
    
    async def track_agent_usage(self, user_id: int, agent_name: str, usage_type: str, duration_seconds: Optional[float] = None, data_processed_mb: Optional[float] = None) -> bool:
        """Track agent usage by a user."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.track_agent_usage(user_id, agent_name, usage_type, duration_seconds, data_processed_mb)
    
    async def track_storage_usage(self, user_id: int, storage_mb: float, operation: str = "add") -> bool:
        """Track storage usage by a user."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.track_storage_usage(user_id, storage_mb, operation)
    
    async def get_billing_plans(self) -> List[Dict[str, Any]]:
        """Get all available billing plans."""
        billing_plans = await get_billing_plans()
        plans = await billing_plans.get_all_plans()
        
        return [
            {
                "id": plan.id,
                "tier": plan.tier.value,
                "name": plan.name,
                "description": plan.description,
                "price_usd": plan.price_usd,
                "billing_cycle": plan.billing_cycle,
                "max_agents": plan.max_agents,
                "max_api_calls_per_month": plan.max_api_calls_per_month,
                "features": plan.features,
                "is_active": plan.is_active
            }
            for plan in plans
        ]
    
    async def get_plan_features(self, tier: BillingTier) -> Dict[str, Any]:
        """Get features for a specific billing tier."""
        billing_plans = await get_billing_plans()
        return await billing_plans.get_plan_features(tier)
    
    async def check_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if a user has access to a specific feature."""
        user_subscription = await self.get_user_subscription(user_id)
        if not user_subscription:
            return False
        
        tier = BillingTier(user_subscription["tier"])
        billing_plans = await get_billing_plans()
        return await billing_plans.check_feature_access(tier, feature)
    
    async def get_agent_limits(self, user_id: int) -> Dict[str, Any]:
        """Get agent limits for a user."""
        user_subscription = await self.get_user_subscription(user_id)
        if not user_subscription:
            return {"max_count": 0, "excluded_agents": [], "available_agents": []}
        
        tier = BillingTier(user_subscription["tier"])
        billing_plans = await get_billing_plans()
        return await billing_plans.get_agent_limits(tier)
    
    async def can_access_agent(self, user_id: int, agent_name: str) -> bool:
        """Check if a user can access a specific agent."""
        user_subscription = await self.get_user_subscription(user_id)
        if not user_subscription:
            return False
        
        tier = BillingTier(user_subscription["tier"])
        billing_plans = await get_billing_plans()
        return await billing_plans.can_access_agent(tier, agent_name)
    
    async def get_subscription_statistics(self) -> Dict[str, Any]:
        """Get subscription statistics for the system."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.get_subscription_statistics()
    
    async def get_usage_statistics(self, month: Optional[str] = None) -> Dict[str, Any]:
        """Get system-wide usage statistics."""
        usage_tracker = await get_usage_tracker()
        return await usage_tracker.get_system_usage_statistics(month)
    
    async def process_subscription_renewals(self) -> List[Dict[str, Any]]:
        """Process expired subscriptions and attempt renewals."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.process_expired_subscriptions()
    
    async def get_expiring_subscriptions(self) -> List[Dict[str, Any]]:
        """Get subscriptions that are expiring soon."""
        subscription_manager = await get_subscription_manager()
        return await subscription_manager.check_subscription_expiry()
    
    async def create_billing_record(self, user_id: int, amount: float, description: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a billing record for tracking purposes."""
        db = get_database()
        
        async with db.get_session() as session:
            billing_record = BillingRecord(
                user_id=user_id,
                amount=amount,
                currency="USD",
                description=description,
                transaction_id=transaction_id,
                payment_method="system",
                status="recorded"
            )
            
            session.add(billing_record)
            await session.commit()
            
            logger.info(f"Created billing record for user {user_id}: {description}")
            
            return {
                "id": billing_record.id,
                "amount": billing_record.amount,
                "currency": billing_record.currency,
                "description": billing_record.description,
                "transaction_id": billing_record.transaction_id,
                "created_at": billing_record.created_at.isoformat()
            }
    
    async def get_billing_summary(self, user_id: int, months: int = 6) -> Dict[str, Any]:
        """Get comprehensive billing summary for a user."""
        # Get subscription details
        subscription = await self.get_user_subscription(user_id)
        
        # Get usage summary
        usage_summary = await self.get_user_usage(user_id)
        
        # Get payment history
        payment_history = await self.get_payment_history(user_id, limit=months * 2)
        
        # Get usage over time
        usage_over_time = await self.get_user_usage(user_id)
        if usage_over_time:
            usage_tracker = await get_usage_tracker()
            usage_history = await usage_tracker.get_usage_summary(user_id, months)
        else:
            usage_history = []
        
        # Calculate totals
        total_paid = sum(payment["amount_usd"] for payment in payment_history if payment["status"] == "successful")
        total_payments = len(payment_history)
        successful_payments = len([p for p in payment_history if p["status"] == "successful"])
        
        return {
            "subscription": subscription,
            "current_usage": usage_summary,
            "usage_history": usage_history,
            "payment_summary": {
                "total_paid_usd": total_paid,
                "total_payments": total_payments,
                "successful_payments": successful_payments,
                "payment_success_rate": (successful_payments / total_payments * 100) if total_payments > 0 else 0
            },
            "payment_history": payment_history,
            "summary_period_months": months
        }

    async def get_all_subscriptions(self) -> Dict[str, Any]:
        """Get all subscriptions for admin dashboard."""
        db = get_database()
        
        async with db.get_session() as session:
            result = await session.execute("""
                SELECT 
                    s.id,
                    u.email,
                    bp.tier,
                    s.status,
                    s.created_at,
                    s.updated_at,
                    s.next_billing_date,
                    COALESCE(SUM(p.amount_usd), 0) as total_paid
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                JOIN billing_plans bp ON s.plan_id = bp.id
                LEFT JOIN payments p ON s.id = p.subscription_id AND p.status = 'successful'
                GROUP BY s.id, u.email, bp.tier, s.status, s.created_at, s.updated_at, s.next_billing_date
                ORDER BY s.created_at DESC
            """)
            
            subscriptions = []
            for row in result.fetchall():
                subscriptions.append({
                    "id": row[0],
                    "user_email": row[1],
                    "tier": row[2],
                    "status": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None,
                    "next_billing_date": row[6].isoformat() if row[6] else None,
                    "total_paid": float(row[7])
                })
            
            return {"subscriptions": subscriptions}

    async def get_all_payments(self) -> Dict[str, Any]:
        """Get all payments for admin dashboard."""
        db = get_database()
        
        async with db.get_session() as session:
            result = await session.execute("""
                SELECT 
                    p.id,
                    u.email,
                    p.amount_usd,
                    p.currency,
                    p.status,
                    p.payment_method,
                    p.created_at,
                    bp.tier
                FROM payments p
                JOIN subscriptions s ON p.subscription_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN billing_plans bp ON s.plan_id = bp.id
                ORDER BY p.created_at DESC
                LIMIT 100
            """)
            
            payments = []
            for row in result.fetchall():
                payments.append({
                    "id": row[0],
                    "user_email": row[1],
                    "amount_usd": float(row[2]),
                    "currency": row[3],
                    "status": row[4],
                    "payment_method": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "tier": row[7]
                })
            
            return {"payments": payments}

    async def get_recent_payment_activity(self) -> List[Dict[str, Any]]:
        """Get recent payment activity for admin dashboard."""
        db = get_database()
        
        async with db.get_session() as session:
            result = await session.execute("""
                SELECT 
                    u.email,
                    p.amount_usd,
                    p.status,
                    p.created_at,
                    bp.tier
                FROM payments p
                JOIN subscriptions s ON p.subscription_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN billing_plans bp ON s.plan_id = bp.id
                ORDER BY p.created_at DESC
                LIMIT 20
            """)
            
            activities = []
            for row in result.fetchall():
                activities.append({
                    "user": row[0],
                    "amount": f"${row[1]:.2f}",
                    "status": row[2],
                    "time": row[3].strftime("%Y-%m-%d %H:%M") if row[3] else None,
                    "action": f"{row[4].title()} Plan Payment"
                })
            
            return activities
    
    async def handle_webhook(self, payload: bytes, signature: str, source: str = "paystack") -> Dict[str, Any]:
        """Handle webhooks from payment providers."""
        if source == "paystack":
            paystack = await get_paystack()
            return await paystack.process_webhook(payload, signature)
        else:
            raise ValueError(f"Unsupported webhook source: {source}")
    
    async def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get comprehensive revenue analytics for admin dashboard."""
        db = get_database()
        
        async with db.get_session() as session:
            # Get total revenue
            total_revenue_result = await session.execute(
                select(db.func.sum(Payment.amount_usd))
                .where(Payment.status == PaymentStatus.SUCCESSFUL)
            )
            total_revenue = float(total_revenue_result.scalar() or 0)
            
            # Get monthly recurring revenue
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue_result = await session.execute(
                select(db.func.sum(Payment.amount_usd))
                .where(
                    and_(
                        Payment.status == PaymentStatus.SUCCESSFUL,
                        Payment.created_at >= current_month_start
                    )
                )
            )
            monthly_recurring_revenue = float(monthly_revenue_result.scalar() or 0)
            
            # Get annual recurring revenue (last 12 months)
            annual_start = current_month_start - timedelta(days=365)
            annual_revenue_result = await session.execute(
                select(db.func.sum(Payment.amount_usd))
                .where(
                    and_(
                        Payment.status == PaymentStatus.SUCCESSFUL,
                        Payment.created_at >= annual_start
                    )
                )
            )
            annual_recurring_revenue = float(annual_revenue_result.scalar() or 0)
            
            # Get subscription counts by tier
            tier_counts_result = await session.execute(
                select(
                    BillingPlan.tier,
                    db.func.count(Subscription.id).label('count'),
                    db.func.sum(Payment.amount_usd).label('monthly_revenue'),
                    db.func.sum(
                        case(
                            (Payment.created_at >= annual_start, Payment.amount_usd),
                            else_=0
                        )
                    ).label('yearly_revenue')
                )
                .join(Subscription, BillingPlan.id == Subscription.plan_id)
                .join(Payment, Subscription.id == Payment.subscription_id)
                .where(
                    and_(
                        Payment.status == PaymentStatus.SUCCESSFUL,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                )
                .group_by(BillingPlan.tier)
            )
            
            tier_distribution = {
                "free": {"count": 0, "monthly_revenue": 0, "yearly_revenue": 0},
                "starter": {"count": 0, "monthly_revenue": 0, "yearly_revenue": 0},
                "pro": {"count": 0, "monthly_revenue": 0, "yearly_revenue": 0}
            }
            
            for tier, count, monthly_rev, yearly_rev in tier_counts_result:
                tier_distribution[tier.value] = {
                    "count": count,
                    "monthly_revenue": float(monthly_rev or 0),
                    "yearly_revenue": float(yearly_rev or 0)
                }
            
            # Get total subscriptions
            total_subscriptions_result = await session.execute(
                select(db.func.count(Subscription.id))
            )
            total_subscriptions = total_subscriptions_result.scalar() or 0
            
            # Get active subscriptions
            active_subscriptions_result = await session.execute(
                select(db.func.count(Subscription.id))
                .where(Subscription.status == SubscriptionStatus.ACTIVE)
            )
            active_subscriptions = active_subscriptions_result.scalar() or 0
            
            # Calculate churn rate (simplified)
            churn_rate = 0.0
            if total_subscriptions > 0:
                churn_rate = ((total_subscriptions - active_subscriptions) / total_subscriptions) * 100
            
            # Calculate average revenue per user
            average_revenue_per_user = 0.0
            if active_subscriptions > 0:
                average_revenue_per_user = monthly_recurring_revenue / active_subscriptions
            
            return {
                "total_revenue": total_revenue,
                "monthly_recurring_revenue": monthly_recurring_revenue,
                "annual_recurring_revenue": annual_recurring_revenue,
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions,
                "churn_rate": churn_rate,
                "average_revenue_per_user": average_revenue_per_user,
                "tier_distribution": tier_distribution
            }

    async def cleanup_old_data(self, months_to_keep: int = 24) -> Dict[str, int]:
        """Clean up old billing and usage data."""
        usage_tracker = await get_usage_tracker()
        
        # Clean up old usage records
        usage_cleaned = await usage_tracker.cleanup_old_usage_records(months_to_keep)
        
        # Clean up old billing records
        db = get_database()
        cutoff_date = datetime.utcnow() - timedelta(days=months_to_keep * 30)
        
        async with db.get_session() as session:
            # Clean up old billing records
            old_billing_records = await session.execute(
                select(BillingRecord).where(BillingRecord.created_at < cutoff_date)
            )
            billing_cleaned = len(old_billing_records.scalars().all())
            
            for record in old_billing_records.scalars():
                await session.delete(record)
            
            # Clean up old payments (keep successful ones longer)
            payment_cutoff = datetime.utcnow() - timedelta(days=months_to_keep * 30)
            old_payments = await session.execute(
                select(Payment).where(
                    and_(
                        Payment.created_at < payment_cutoff,
                        Payment.status != PaymentStatus.SUCCESSFUL
                    )
                )
            )
            payments_cleaned = len(old_payments.scalars().all())
            
            for payment in old_payments.scalars():
                await session.delete(payment)
            
            await session.commit()
        
        logger.info(f"Cleaned up billing data: {billing_cleaned} billing records, {payments_cleaned} payments, {usage_cleaned} usage records")
        
        return {
            "billing_records_cleaned": billing_cleaned,
            "payments_cleaned": payments_cleaned,
            "usage_records_cleaned": usage_cleaned
        }

# Global instance
billing_manager = BillingManager()

async def get_billing() -> BillingManager:
    """Get the global billing manager instance."""
    if not billing_manager._initialized:
        await billing_manager.initialize()
    return billing_manager

async def init_billing():
    """Initialize the billing system."""
    await billing_manager.initialize()
