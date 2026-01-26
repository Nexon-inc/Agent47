from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .billing_manager import get_billing
from .models import BillingTier
from ..authentication.auth_manager import get_current_user
from ..database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

class SubscribeRequest(BaseModel):
    tier: str
    payment_method: str = "paystack"
    billing_period: str = "monthly"

class CancelRequest(BaseModel):
    reason: str = "User requested cancellation"

@router.get("/plans")
async def get_plans():
    """Get all available billing plans"""
    try:
        billing = await get_billing()
        return await billing.get_billing_plans()
    except Exception as e:
        logger.error(f"Error fetching billing plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)):
    """Get current user subscription"""
    try:
        billing = await get_billing()
        sub = await billing.get_user_subscription(current_user.id)
        if not sub:
            return {"tier": "free", "status": "active"}
        return sub
    except Exception as e:
        logger.error(f"Error fetching user subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def create_subscription(
    request: SubscribeRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription"""
    try:
        billing = await get_billing()
        # Convert string tier to enum
        try:
            tier_enum = BillingTier(request.tier.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {request.tier}")
            
        result = await billing.create_subscription(
            user_id=current_user.id,
            tier=tier_enum,
            payment_method=request.payment_method,
            billing_period=request.billing_period
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_subscription(
    request: CancelRequest,
    current_user: User = Depends(get_current_user)
):
    """Cancel current subscription"""
    try:
        billing = await get_billing()
        success = await billing.cancel_subscription(current_user.id, request.reason)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage")
async def get_usage(current_user: User = Depends(get_current_user)):
    """Get user usage stats"""
    try:
        billing = await get_billing()
        return await billing.get_user_usage(current_user.id)
    except Exception as e:
        logger.error(f"Error fetching usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/paystack")
async def paystack_webhook(request: Request, response: Response):
    """Handle Paystack webhooks"""
    try:
        payload = await request.body()
        signature = request.headers.get("x-paystack-signature")
        
        if not signature:
            logger.warning("Missing Paystack signature")
            raise HTTPException(status_code=400, detail="Missing signature")
            
        billing = await get_billing()
        result = await billing.handle_webhook(payload, signature, source="paystack")
        return result
    except ValueError as e:
        logger.warning(f"Invalid Paystack webhook value: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Paystack Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
