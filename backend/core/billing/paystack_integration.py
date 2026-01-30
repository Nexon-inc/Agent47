import httpx
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..config import settings
from .models import Payment, PaymentStatus, Subscription, SubscriptionStatus
from ..database.connection import get_database
from sqlalchemy import select
from ..utils.validation import ValidationUtils

# Alias for backward compatibility
DataValidator = ValidationUtils

logger = logging.getLogger(__name__)

class PaystackIntegration:
    """Integration with Paystack payment gateway for Agent47 billing."""
    
    def __init__(self):
        self.secret_key = settings.billing.paystack_secret_key
        self.public_key = settings.billing.paystack_public_key
        self.base_url = "https://api.paystack.co"
        self.webhook_secret = settings.billing.paystack_webhook_secret
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Paystack integration."""
        if self._initialized:
            return
        
        if not self.secret_key or not self.public_key:
            logger.error("Paystack credentials not configured")
            raise ValueError("Paystack credentials not configured")
        
        # Unblock flow: Set initialized to True immediately if keys are present.
        # Real-time error handling will happen during actual transaction calls.
        self._initialized = True
        logger.info("Paystack integration initialized (credentials present)")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Paystack API requests."""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def create_customer(self, email: str, first_name: str, last_name: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Create a customer in Paystack."""
        if not DataValidator.validate_email(email):
            raise ValueError("Invalid email address")
        
        customer_data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        
        if phone:
            customer_data["phone"] = phone
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/customer",
                json=customer_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created Paystack customer: {email}")
                return data["data"]
            else:
                error_msg = f"Failed to create customer: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def create_subscription(self, customer_code: str, plan_code: str, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a subscription in Paystack."""
        subscription_data = {
            "customer": customer_code,
            "plan": plan_code
        }
        
        if start_date:
            subscription_data["start"] = start_date.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subscription",
                json=subscription_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created Paystack subscription for customer: {customer_code}")
                return data["data"]
            else:
                error_msg = f"Failed to create subscription: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def create_plan(self, name: str, amount: int, interval: str = "monthly", description: Optional[str] = None) -> Dict[str, Any]:
        """Create a subscription plan in Paystack."""
        # Convert USD amount to kobo (Paystack uses kobo for Nigerian Naira)
        # Since we're using USD, we'll store the amount in cents
        amount_in_cents = int(amount * 100)
        
        plan_data = {
            "name": name,
            "amount": amount_in_cents,
            "interval": interval,
            "currency": "USD"
        }
        
        if description:
            plan_data["description"] = description
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/plan",
                json=plan_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created Paystack plan: {name}")
                return data["data"]
            else:
                error_msg = f"Failed to create plan: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def initialize_transaction(self, email: str, amount: float, reference: str, callback_url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize a transaction for payment."""
        if not DataValidator.validate_email(email):
            raise ValueError("Invalid email address")
        
        # Convert USD amount to kobo (cents)
        amount_in_cents = int(amount * 100)
        
        transaction_data = {
            "email": email,
            "amount": amount_in_cents,
            "reference": reference,
            "callback_url": callback_url,
            "currency": "USD"
        }
        
        if metadata:
            transaction_data["metadata"] = metadata
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transaction/initialize",
                json=transaction_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Initialized transaction: {reference}")
                return data["data"]
            else:
                error_msg = f"Failed to initialize transaction: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a transaction status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transaction/verify/{reference}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Verified transaction: {reference}")
                return data["data"]
            else:
                error_msg = f"Failed to verify transaction: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def charge_card(self, email: str, amount: float, authorization_code: str, reference: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Charge a card using saved authorization."""
        amount_in_cents = int(amount * 100)
        
        charge_data = {
            "email": email,
            "amount": amount_in_cents,
            "authorization_code": authorization_code,
            "reference": reference,
            "currency": "USD"
        }
        
        if metadata:
            charge_data["metadata"] = metadata
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transaction/charge_authorization",
                json=charge_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Charged card: {reference}")
                return data["data"]
            else:
                error_msg = f"Failed to charge card: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def refund_transaction(self, transaction_id: str, amount: Optional[float] = None, reason: Optional[str] = None) -> Dict[str, Any]:
        """Refund a transaction."""
        refund_data = {}
        
        if amount:
            refund_data["amount"] = int(amount * 100)  # Convert to cents
        
        if reason:
            refund_data["reason"] = reason
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/refund",
                json=refund_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Refunded transaction: {transaction_id}")
                return data["data"]
            else:
                error_msg = f"Failed to refund transaction: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def get_transaction_history(self, customer_email: Optional[str] = None, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get transaction history."""
        params = {
            "page": page,
            "perPage": per_page
        }
        
        if customer_email:
            params["customer"] = customer_email
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transaction",
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                error_msg = f"Failed to get transaction history: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process webhook from Paystack."""
        # Verify webhook signature
        if not self._verify_webhook_signature(payload, signature):
            raise ValueError("Invalid webhook signature")
        
        try:
            data = json.loads(payload.decode('utf-8'))
            event = data.get("event")
            
            if event == "charge.success":
                return await self._handle_successful_charge(data["data"])
            elif event == "subscription.create":
                return await self._handle_subscription_created(data["data"])
            elif event == "subscription.disable":
                return await self._handle_subscription_disabled(data["data"])
            elif event == "transfer.success":
                return await self._handle_transfer_success(data["data"])
            else:
                logger.info(f"Unhandled webhook event: {event}")
                return {"status": "ignored", "event": event}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode webhook payload: {e}")
            raise ValueError("Invalid webhook payload")
    
    def _verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Paystack."""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def _handle_successful_charge(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful charge webhook."""
        reference = charge_data.get("reference")
        amount = charge_data.get("amount", 0) / 100  # Convert from kobo to USD
        transaction_id = charge_data.get("id")
        metadata = charge_data.get("metadata", {})
        
        # Get subscription_id from metadata
        subscription_id = metadata.get("subscription_id")
        
        db = get_database()
        async with db.get_session() as session:
            # Find subscription by reference or subscription_id
            if subscription_id:
                subscription = await session.execute(
                    select(Subscription).where(Subscription.id == subscription_id)
                )
                subscription = subscription.scalar_one_or_none()
            else:
                # Fallback: find by reference
                subscription = await session.execute(
                    select(Subscription).where(Subscription.paystack_reference == reference)
                )
                subscription = subscription.scalar_one_or_none()
            
            if subscription:
                # Activate subscription
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.paystack_reference = reference
                subscription.paystack_transaction_id = str(transaction_id)
                subscription.updated_at = datetime.utcnow()
                
                # Create or update payment record
                payment = await session.execute(
                    select(Payment).where(Payment.paystack_reference == reference)
                )
                payment = payment.scalar_one_or_none()
                
                if not payment:
                    # Create new payment record
                    payment = Payment(
                        subscription_id=subscription.id,
                        amount_usd=amount,
                        currency="USD",
                        status=PaymentStatus.SUCCESSFUL,
                        payment_method="paystack",
                        paystack_reference=reference,
                        paystack_transaction_id=str(transaction_id),
                        metadata=metadata
                    )
                    session.add(payment)
                else:
                    payment.status = PaymentStatus.SUCCESSFUL
                    payment.paystack_transaction_id = str(transaction_id)
                    payment.updated_at = datetime.utcnow()
                
                session.add(subscription)
                await session.commit()
                
                # Update user tier
                try:
                    from ..user_management.user_manager import UserManager
                    from ..database.models import UserTier
                    user_manager = UserManager()
                    tier_value = metadata.get("tier", "starter")
                    user_tier = UserTier(tier_value)
                    await user_manager.update_user_tier(subscription.user_id, user_tier)
                    logger.info(f"Updated user {subscription.user_id} tier to {tier_value}")
                except Exception as e:
                    logger.warning(f"Failed to update user tier: {e}")
                
                logger.info(f"Activated subscription {subscription.id} after successful payment: {reference}")
                return {"status": "success", "subscription_id": subscription.id, "payment_id": payment.id}
            else:
                logger.warning(f"Subscription not found for reference: {reference}")
                return {"status": "error", "message": "Subscription not found"}
    
    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created webhook."""
        subscription_code = subscription_data.get("subscription_code")
        customer_code = subscription_data.get("customer", {}).get("customer_code")
        
        logger.info(f"Subscription created: {subscription_code} for customer: {customer_code}")
        return {"status": "success", "subscription_code": subscription_code}
    
    async def _handle_subscription_disabled(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription disabled webhook."""
        subscription_code = subscription_data.get("subscription_code")
        
        # Update subscription status in database
        db = get_database()
        async with db.get_session() as session:
            subscription = await session.execute(
                select(Subscription).where(Subscription.paystack_subscription_code == subscription_code)
            )
            subscription = subscription.scalar_one_or_none()
            
            if subscription:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.updated_at = datetime.utcnow()
                session.add(subscription)
                await session.commit()
                
                logger.info(f"Updated subscription status to cancelled: {subscription_code}")
                return {"status": "success", "subscription_id": subscription.id}
            else:
                logger.warning(f"Subscription not found for code: {subscription_code}")
                return {"status": "error", "message": "Subscription not found"}
    
    async def _handle_transfer_success(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful transfer webhook."""
        transfer_code = transfer_data.get("transfer_code")
        amount = transfer_data.get("amount", 0) / 100  # Convert from kobo to USD
        
        logger.info(f"Transfer successful: {transfer_code} for amount: ${amount}")
        return {"status": "success", "transfer_code": transfer_code}
    
    async def get_bank_list(self) -> List[Dict[str, Any]]:
        """Get list of supported banks for transfers."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bank",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["data"]
            else:
                error_msg = f"Failed to get bank list: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def initiate_transfer(self, recipient_code: str, amount: float, reason: str) -> Dict[str, Any]:
        """Initiate a transfer to a recipient."""
        amount_in_cents = int(amount * 100)
        
        transfer_data = {
            "source": "balance",
            "recipient": recipient_code,
            "amount": amount_in_cents,
            "reason": reason,
            "currency": "USD"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transfer",
                json=transfer_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Initiated transfer: {data['data']['transfer_code']}")
                return data["data"]
            else:
                error_msg = f"Failed to initiate transfer: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/balance",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["data"]
            else:
                error_msg = f"Failed to get account balance: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

# Global instance
paystack_integration = PaystackIntegration()

async def get_paystack() -> PaystackIntegration:
    """Get the global Paystack integration instance."""
    if not paystack_integration._initialized:
        await paystack_integration.initialize()
    return paystack_integration
