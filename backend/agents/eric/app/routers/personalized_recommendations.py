from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from ..services.personalized_recommendations_service import (
    PersonalizedRecommendationsService, ProductRecommendation, PricingRecommendation,
    SalesStrategyRecommendation, CustomerProfile
)
from ..database import get_eric_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Personalized Recommendations"])

# Request/Response Models
class ProductRecommendationRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID to generate recommendations for")
    context: str = Field("general", description="Context for recommendations (general, renewal, upsell)")

class PricingRecommendationRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID")
    product_id: str = Field(..., description="Product ID to get pricing for")

class SalesStrategyRequest(BaseModel):
    customer_id: int = Field(..., description="Customer ID")
    deal_id: Optional[int] = Field(None, description="Optional deal ID for context")

class BatchRecommendationRequest(BaseModel):
    customer_ids: List[int] = Field(..., description="List of customer IDs")
    recommendation_types: List[str] = Field(["products", "pricing", "strategy"], description="Types of recommendations to generate")

class BatchRecommendationResponse(BaseModel):
    customer_recommendations: Dict[int, Dict[str, Any]]
    total_customers: int
    processing_time: float

class RecommendationInsightsResponse(BaseModel):
    total_recommendations: int
    average_confidence: float
    top_recommendations: List[Dict[str, Any]]
    conversion_rates: Dict[str, float]
    generated_at: str

# Service instance
recommendations_service = PersonalizedRecommendationsService()

@router.post("/products", response_model=List[ProductRecommendation], summary="Get Product Recommendations")
async def get_product_recommendations(request: ProductRecommendationRequest):
    """Generate personalized product recommendations for a customer"""
    try:
        recommendations = await recommendations_service.get_product_recommendations(
            customer_id=request.customer_id,
            context=request.context
        )
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get product recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/{customer_id}", response_model=List[ProductRecommendation], summary="Get Cached Product Recommendations")
async def get_cached_product_recommendations(
    customer_id: int,
    context: str = Query("general", description="Recommendation context")
):
    """Get cached product recommendations for a customer"""
    try:
        # Try to get from cache first
        from core.cache.redis_manager import RedisManager
        redis_manager = RedisManager()
        
        cache_key = f"product_recommendations_{customer_id}_{context}"
        cached_recommendations = await redis_manager.get_cache(cache_key)
        
        if cached_recommendations:
            return [ProductRecommendation(**rec) for rec in cached_recommendations]
        
        # If not cached, generate new recommendations
        recommendations = await recommendations_service.get_product_recommendations(customer_id, context)
        return recommendations
    except Exception as e:
        logger.error(f"Failed to get cached product recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/pricing", response_model=PricingRecommendation, summary="Get Pricing Recommendations")
async def get_pricing_recommendations(request: PricingRecommendationRequest):
    """Generate personalized pricing recommendations for a customer and product"""
    try:
        recommendation = await recommendations_service.get_pricing_recommendations(
            customer_id=request.customer_id,
            product_id=request.product_id
        )
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get pricing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/pricing/{customer_id}/{product_id}", response_model=PricingRecommendation, summary="Get Cached Pricing Recommendations")
async def get_cached_pricing_recommendations(customer_id: int, product_id: str):
    """Get cached pricing recommendations"""
    try:
        # Try to get from cache first
        from core.cache.redis_manager import RedisManager
        redis_manager = RedisManager()
        
        cache_key = f"pricing_recommendation_{customer_id}_{product_id}"
        cached_recommendation = await redis_manager.get_cache(cache_key)
        
        if cached_recommendation:
            return PricingRecommendation(**cached_recommendation)
        
        # If not cached, generate new recommendation
        recommendation = await recommendations_service.get_pricing_recommendations(customer_id, product_id)
        return recommendation
    except Exception as e:
        logger.error(f"Failed to get cached pricing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/strategy", response_model=List[SalesStrategyRecommendation], summary="Get Sales Strategy Recommendations")
async def get_sales_strategy_recommendations(request: SalesStrategyRequest):
    """Generate personalized sales strategy recommendations"""
    try:
        recommendations = await recommendations_service.get_sales_strategy_recommendations(
            customer_id=request.customer_id,
            deal_id=request.deal_id
        )
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get sales strategy recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/strategy/{customer_id}", response_model=List[SalesStrategyRecommendation], summary="Get Cached Sales Strategy Recommendations")
async def get_cached_sales_strategy_recommendations(customer_id: int):
    """Get cached sales strategy recommendations"""
    try:
        # Try to get from cache first
        from core.cache.redis_manager import RedisManager
        redis_manager = RedisManager()
        
        cache_key = f"sales_strategy_recommendations_{customer_id}"
        cached_recommendations = await redis_manager.get_cache(cache_key)
        
        if cached_recommendations:
            return [SalesStrategyRecommendation(**rec) for rec in cached_recommendations]
        
        # If not cached, generate new recommendations
        recommendations = await recommendations_service.get_sales_strategy_recommendations(customer_id)
        return recommendations
    except Exception as e:
        logger.error(f"Failed to get cached sales strategy recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/profile/{customer_id}", response_model=CustomerProfile, summary="Get Customer Profile")
async def get_customer_profile(customer_id: int):
    """Get comprehensive customer profile for personalization"""
    try:
        profile = await recommendations_service.get_customer_profile(customer_id)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get customer profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch", response_model=BatchRecommendationResponse, summary="Batch Recommendations")
async def batch_recommendations(request: BatchRecommendationRequest):
    """Generate recommendations for multiple customers in batch"""
    try:
        import time
        start_time = time.time()
        
        customer_recommendations = {}
        
        for customer_id in request.customer_ids:
            try:
                customer_data = {}
                
                if "products" in request.recommendation_types:
                    product_recs = await recommendations_service.get_product_recommendations(customer_id)
                    customer_data["products"] = [rec.dict() for rec in product_recs]
                
                if "pricing" in request.recommendation_types:
                    # Get pricing for first product recommendation if available
                    if "products" in customer_data and customer_data["products"]:
                        first_product = customer_data["products"][0]
                        pricing_rec = await recommendations_service.get_pricing_recommendations(
                            customer_id, first_product["product_id"]
                        )
                        customer_data["pricing"] = pricing_rec.dict()
                
                if "strategy" in request.recommendation_types:
                    strategy_recs = await recommendations_service.get_sales_strategy_recommendations(customer_id)
                    customer_data["strategy"] = [rec.dict() for rec in strategy_recs]
                
                customer_recommendations[customer_id] = customer_data
                
            except Exception as e:
                logger.warning(f"Failed to generate recommendations for customer {customer_id}: {e}")
                customer_recommendations[customer_id] = {"error": str(e)}
        
        processing_time = time.time() - start_time
        
        return BatchRecommendationResponse(
            customer_recommendations=customer_recommendations,
            total_customers=len(request.customer_ids),
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Failed to process batch recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/insights", response_model=RecommendationInsightsResponse, summary="Get Recommendation Insights")
async def get_recommendation_insights(
    days: int = Query(30, description="Number of days to analyze")
):
    """Get insights from recent recommendations"""
    try:
        # This would typically aggregate data from recent recommendations
        # For now, we'll return sample insights
        
        insights = {
            "total_recommendations": 850,
            "average_confidence": 0.76,
            "top_recommendations": [
                {
                    "type": "product",
                    "recommendation": "Premium Business Suite",
                    "conversion_rate": 0.35,
                    "avg_value": 15000.0
                },
                {
                    "type": "pricing",
                    "recommendation": "Enterprise discount",
                    "conversion_rate": 0.42,
                    "avg_value": 25000.0
                },
                {
                    "type": "strategy",
                    "recommendation": "Executive consultative approach",
                    "conversion_rate": 0.28,
                    "avg_value": 18000.0
                }
            ],
            "conversion_rates": {
                "products": 0.32,
                "pricing": 0.38,
                "strategy": 0.25
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return RecommendationInsightsResponse(**insights)
    except Exception as e:
        logger.error(f"Failed to get recommendation insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/customers/high-value", summary="Get High-Value Customer Recommendations")
async def get_high_value_customer_recommendations(
    min_lifetime_value: float = Query(10000.0, description="Minimum lifetime value"),
    limit: int = Query(50, description="Number of customers to return")
):
    """Get recommendations for high-value customers"""
    try:
        async with get_eric_database() as session:
            from sqlalchemy import select
            from ..models import EricDeal
            
            # Get high-value customers
            customers_query = select(EricDeal.customer_id).where(
                and_(
                    EricDeal.status == "closed",
                    EricDeal.value >= min_lifetime_value
                )
            ).group_by(EricDeal.customer_id).having(
                func.sum(EricDeal.value) >= min_lifetime_value
            ).limit(limit)
            
            result = await session.execute(customers_query)
            customer_ids = [row.customer_id for row in result]
            
            # Get recommendations for these customers
            high_value_recommendations = []
            for customer_id in customer_ids:
                try:
                    # Get customer profile
                    profile = await recommendations_service.get_customer_profile(customer_id)
                    
                    # Get product recommendations
                    product_recs = await recommendations_service.get_product_recommendations(customer_id)
                    
                    high_value_recommendations.append({
                        "customer_id": customer_id,
                        "segment": profile.segment,
                        "lifetime_value": profile.lifetime_value,
                        "recommendations": [rec.dict() for rec in product_recs[:3]]  # Top 3
                    })
                except Exception as e:
                    logger.warning(f"Failed to get recommendations for customer {customer_id}: {e}")
            
            # Sort by lifetime value
            high_value_recommendations.sort(key=lambda x: x["lifetime_value"], reverse=True)
            
            return {
                "customers": high_value_recommendations[:limit],
                "total_found": len(high_value_recommendations),
                "min_lifetime_value": min_lifetime_value
            }
    except Exception as e:
        logger.error(f"Failed to get high-value customer recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products/popular", summary="Get Popular Product Recommendations")
async def get_popular_product_recommendations(
    days: int = Query(30, description="Number of days to analyze"),
    limit: int = Query(10, description="Number of products to return")
):
    """Get most popular product recommendations"""
    try:
        # This would typically analyze recommendation data
        # For now, return sample popular recommendations
        
        popular_products = [
            {
                "product_id": "premium_suite",
                "product_name": "Premium Business Suite",
                "recommendation_count": 125,
                "conversion_rate": 0.35,
                "avg_value": 15000.0
            },
            {
                "product_id": "growth_package",
                "product_name": "Growth Acceleration Package",
                "recommendation_count": 98,
                "conversion_rate": 0.28,
                "avg_value": 5000.0
            },
            {
                "product_id": "advanced_analytics",
                "product_name": "Advanced Analytics Platform",
                "recommendation_count": 87,
                "conversion_rate": 0.32,
                "avg_value": 3000.0
            },
            {
                "product_id": "enterprise_integration",
                "product_name": "Enterprise Integration Hub",
                "recommendation_count": 65,
                "conversion_rate": 0.45,
                "avg_value": 25000.0
            },
            {
                "product_id": "startup_essentials",
                "product_name": "Startup Essentials Bundle",
                "recommendation_count": 142,
                "conversion_rate": 0.22,
                "avg_value": 1500.0
            }
        ]
        
        return {
            "popular_products": popular_products[:limit],
            "analysis_period_days": days,
            "total_recommendations": sum(p["recommendation_count"] for p in popular_products)
        }
    except Exception as e:
        logger.error(f"Failed to get popular product recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/segments/{segment}", summary="Get Segment-Based Recommendations")
async def get_segment_recommendations(
    segment: str,
    limit: int = Query(20, description="Number of customers to analyze")
):
    """Get recommendations for a specific customer segment"""
    try:
        async with get_eric_database() as session:
            from sqlalchemy import select
            from ..models import EricDeal
            
            # Get customers in the segment (simplified - would need customer segmentation data)
            # For now, we'll simulate based on deal values
            segment_filters = {
                "enterprise": EricDeal.value >= 10000,
                "business": and_(EricDeal.value >= 5000, EricDeal.value < 10000),
                "professional": and_(EricDeal.value >= 1000, EricDeal.value < 5000),
                "startup": EricDeal.value < 1000
            }
            
            if segment not in segment_filters:
                raise HTTPException(status_code=400, detail=f"Invalid segment: {segment}")
            
            customers_query = select(EricDeal.customer_id).where(
                and_(
                    EricDeal.status == "closed",
                    segment_filters[segment]
                )
            ).distinct().limit(limit)
            
            result = await session.execute(customers_query)
            customer_ids = [row.customer_id for row in result]
            
            # Get recommendations for these customers
            segment_recommendations = []
            for customer_id in customer_ids:
                try:
                    product_recs = await recommendations_service.get_product_recommendations(customer_id)
                    segment_recommendations.extend([rec.dict() for rec in product_recs])
                except Exception as e:
                    logger.warning(f"Failed to get recommendations for customer {customer_id}: {e}")
            
            # Aggregate recommendations
            product_counts = {}
            for rec in segment_recommendations:
                product_id = rec["product_id"]
                if product_id not in product_counts:
                    product_counts[product_id] = {
                        "product_name": rec["product_name"],
                        "category": rec["category"],
                        "count": 0,
                        "avg_confidence": 0.0,
                        "avg_value": 0.0
                    }
                
                product_counts[product_id]["count"] += 1
                product_counts[product_id]["avg_confidence"] += rec["confidence_score"]
                product_counts[product_id]["avg_value"] += rec["estimated_value"]
            
            # Calculate averages
            for product_id, data in product_counts.items():
                data["avg_confidence"] /= data["count"]
                data["avg_value"] /= data["count"]
            
            # Sort by count
            top_recommendations = sorted(
                product_counts.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
            
            return {
                "segment": segment,
                "total_customers": len(customer_ids),
                "top_recommendations": [
                    {"product_id": pid, **data} for pid, data in top_recommendations[:10]
                ]
            }
    except Exception as e:
        logger.error(f"Failed to get segment recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health", summary="Personalized Recommendations Health Check")
async def recommendations_health_check():
    """Health check for personalized recommendations service"""
    try:
        # Test basic functionality
        # This would typically test recommendation generation
        return {
            "status": "healthy",
            "service": "personalized_recommendations",
            "features": [
                "product_recommendations",
                "pricing_recommendations", 
                "sales_strategy_recommendations",
                "customer_profiles"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Personalized recommendations health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
