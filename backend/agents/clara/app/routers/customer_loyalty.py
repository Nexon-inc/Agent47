from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.customer_loyalty_service import CustomerLoyaltyService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class LoyaltyRewardRequest(BaseModel):
    reward_type: str = "automatic"

class TrustScoreResponse(BaseModel):
    customer_id: int
    trust_score: float
    churn_risk: float
    loyalty_level: str
    analysis: Dict[str, Any]

async def get_loyalty_service() -> CustomerLoyaltyService:
    """Dependency to get customer loyalty service"""
    service = CustomerLoyaltyService()
    await service.initialize()
    return service

@router.get("/trust-score/{customer_id}", response_model=Dict[str, Any])
async def calculate_trust_score(
    customer_id: int,
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Calculate customer trust score and loyalty prediction"""
    try:
        result = await loyalty_service.calculate_trust_score(customer_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rewards/{customer_id}", response_model=Dict[str, Any])
async def generate_loyalty_reward(
    customer_id: int,
    request: LoyaltyRewardRequest,
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Generate loyalty reward for customer"""
    try:
        result = await loyalty_service.generate_loyalty_rewards(
            customer_id=customer_id,
            reward_type=request.reward_type
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=Dict[str, Any])
async def get_loyalty_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Get loyalty program analytics"""
    try:
        result = await loyalty_service.get_loyalty_analytics(
            date_from=date_from,
            date_to=date_to
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/rewards", response_model=Dict[str, Any])
async def get_customer_rewards(
    customer_id: int,
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Get all rewards for a specific customer"""
    try:
        # Get customer rewards from the service
        rewards_result = await loyalty_service.get_customer_rewards(customer_id)
        
        if not rewards_result["success"]:
            raise HTTPException(status_code=400, detail=rewards_result["error"])
        
        return rewards_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/loyalty-status", response_model=Dict[str, Any])
async def get_customer_loyalty_status(
    customer_id: int,
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Get detailed loyalty status for a customer"""
    try:
        # Get trust score first
        trust_result = await loyalty_service.calculate_trust_score(customer_id)
        
        if not trust_result["success"]:
            raise HTTPException(status_code=400, detail=trust_result["error"])
        
        # Get rewards
        rewards_result = await get_customer_rewards(customer_id, loyalty_service)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "loyalty_status": {
                "trust_score": trust_result["trust_score"],
                "churn_risk": trust_result["churn_risk"],
                "loyalty_level": trust_result["loyalty_level"],
                "total_rewards": rewards_result["total_rewards"],
                "active_rewards": rewards_result["active_rewards"],
                "analysis": trust_result["analysis"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/loyalty-levels", response_model=Dict[str, Any])
async def get_loyalty_levels_info():
    """Get information about different loyalty levels"""
    try:
        return {
            "success": True,
            "loyalty_levels": {
                "new": {
                    "name": "New Customer",
                    "description": "Recently joined customers",
                    "trust_score_range": "0.0 - 0.39",
                    "benefits": ["5% discount on first purchase"],
                    "requirements": "New customer"
                },
                "returning": {
                    "name": "Returning Customer",
                    "description": "Customers with some support history",
                    "trust_score_range": "0.4 - 0.59",
                    "benefits": ["10% discount", "Priority support"],
                    "requirements": "Trust score 0.4+"
                },
                "loyal": {
                    "name": "Loyal Customer",
                    "description": "Regular customers with good history",
                    "trust_score_range": "0.6 - 0.79",
                    "benefits": ["15% discount", "Priority support", "Free shipping"],
                    "requirements": "Trust score 0.6+"
                },
                "vip": {
                    "name": "VIP Customer",
                    "description": "Top-tier customers with excellent history",
                    "trust_score_range": "0.8 - 1.0",
                    "benefits": ["20% discount", "Priority support", "Free shipping", "Dedicated support"],
                    "requirements": "Trust score 0.8+"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/churn-risk/{customer_id}", response_model=Dict[str, Any])
async def get_customer_churn_risk(
    customer_id: int,
    loyalty_service: CustomerLoyaltyService = Depends(get_loyalty_service)
):
    """Get detailed churn risk analysis for a customer"""
    try:
        result = await loyalty_service.calculate_trust_score(customer_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        churn_risk = result["churn_risk"]
        
        # Determine risk level
        if churn_risk < 0.2:
            risk_level = "low"
            recommendation = "Continue current engagement strategy"
        elif churn_risk < 0.5:
            risk_level = "medium"
            recommendation = "Increase engagement and offer incentives"
        else:
            risk_level = "high"
            recommendation = "Immediate intervention required - offer special incentives"
        
        return {
            "success": True,
            "customer_id": customer_id,
            "churn_risk": {
                "score": churn_risk,
                "level": risk_level,
                "recommendation": recommendation,
                "factors": result["analysis"].get("factors", {}),
                "last_updated": result["analysis"].get("last_updated")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rewards/types", response_model=Dict[str, Any])
async def get_available_reward_types():
    """Get available reward types and their descriptions"""
    try:
        return {
            "success": True,
            "reward_types": {
                "discount": {
                    "name": "Discount",
                    "description": "Percentage discount on purchases",
                    "value_range": "5% - 25%",
                    "expiry_range": "30-90 days"
                },
                "free_shipping": {
                    "name": "Free Shipping",
                    "description": "Free shipping on next order",
                    "value_range": "N/A",
                    "expiry_range": "30-60 days"
                },
                "priority_support": {
                    "name": "Priority Support",
                    "description": "Faster response times for support",
                    "value_range": "N/A",
                    "expiry_range": "90-180 days"
                },
                "exclusive_access": {
                    "name": "Exclusive Access",
                    "description": "Early access to new features/products",
                    "value_range": "N/A",
                    "expiry_range": "30-90 days"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
