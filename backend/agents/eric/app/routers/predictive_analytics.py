from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging
from sqlalchemy import select, and_

from ..services.predictive_analytics_service import (
    PredictiveAnalyticsService, RevenuePrediction, ConversionPrediction,
    ChurnPrediction, MarketTrendPrediction, PredictionModel
)
from ..database import get_eric_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictive", tags=["Predictive Analytics"])

# Request/Response Models
class RevenuePredictionRequest(BaseModel):
    period: str = Field("monthly", description="Prediction period (daily, weekly, monthly, quarterly)")
    months_ahead: int = Field(3, description="Number of periods to predict ahead")

class MarketTrendRequest(BaseModel):
    trend_type: str = Field("demand", description="Type of trend to predict (demand, competition, pricing)")

class ModelRetrainRequest(BaseModel):
    model_id: int = Field(..., description="ID of the model to retrain")

class PredictionAccuracyRequest(BaseModel):
    model_type: Optional[str] = Field(None, description="Type of model to get accuracy for")

class BatchPredictionRequest(BaseModel):
    lead_ids: List[int] = Field(..., description="List of lead IDs to predict conversion for")
    customer_ids: List[int] = Field(..., description="List of customer IDs to predict churn for")

class BatchPredictionResponse(BaseModel):
    conversion_predictions: List[ConversionPrediction]
    churn_predictions: List[ChurnPrediction]
    total_processed: int
    processing_time: float

class PredictionInsightsResponse(BaseModel):
    total_predictions: int
    average_confidence: float
    top_insights: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: str

# Service instance
predictive_service = PredictiveAnalyticsService()

@router.post("/revenue", response_model=List[RevenuePrediction], summary="Predict Revenue")
async def predict_revenue(request: RevenuePredictionRequest):
    """Predict revenue for future periods using historical data and trends"""
    try:
        predictions = await predictive_service.predict_revenue(
            period=request.period,
            months_ahead=request.months_ahead
        )
        return predictions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to predict revenue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/revenue", response_model=List[RevenuePrediction], summary="Get Cached Revenue Predictions")
async def get_revenue_predictions(
    period: str = Query("monthly", description="Prediction period"),
    months_ahead: int = Query(3, description="Number of periods ahead")
):
    """Get cached revenue predictions"""
    try:
        # Try to get from cache first
        from core.cache.redis_manager import RedisManager
        redis_manager = RedisManager()
        
        cache_key = f"revenue_predictions_{period}_{months_ahead}"
        cached_predictions = await redis_manager.get_cache(cache_key)
        
        if cached_predictions:
            return [RevenuePrediction(**pred) for pred in cached_predictions]
        
        # If not cached, generate new predictions
        predictions = await predictive_service.predict_revenue(period, months_ahead)
        return predictions
    except Exception as e:
        logger.error(f"Failed to get revenue predictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conversion/{lead_id}", response_model=ConversionPrediction, summary="Predict EricLead Conversion")
async def predict_lead_conversion(lead_id: int):
    """Predict the probability of a lead converting to a customer"""
    try:
        prediction = await predictive_service.predict_conversion_probability(lead_id)
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to predict lead conversion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/churn/{customer_id}", response_model=ChurnPrediction, summary="Predict Customer Churn")
async def predict_customer_churn(customer_id: int):
    """Predict the likelihood of a customer churning"""
    try:
        prediction = await predictive_service.predict_customer_churn(customer_id)
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to predict customer churn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/market-trends", response_model=List[MarketTrendPrediction], summary="Predict Market Trends")
async def predict_market_trends(request: MarketTrendRequest):
    """Predict market trends based on historical data and external factors"""
    try:
        predictions = await predictive_service.predict_market_trends(request.trend_type)
        return predictions
    except Exception as e:
        logger.error(f"Failed to predict market trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/market-trends/{trend_type}", response_model=List[MarketTrendPrediction], summary="Get Market Trend Predictions")
async def get_market_trends(trend_type: str):
    """Get market trend predictions for a specific type"""
    try:
        # Try to get from cache first
        from core.cache.redis_manager import RedisManager
        redis_manager = RedisManager()
        
        cache_key = f"market_trends_{trend_type}"
        cached_predictions = await redis_manager.get_cache(cache_key)
        
        if cached_predictions:
            return [MarketTrendPrediction(**pred) for pred in cached_predictions]
        
        # If not cached, generate new predictions
        predictions = await predictive_service.predict_market_trends(trend_type)
        return predictions
    except Exception as e:
        logger.error(f"Failed to get market trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/models", response_model=List[PredictionModel], summary="Get Prediction Models")
async def get_prediction_models():
    """Get all available prediction models"""
    try:
        models = await predictive_service.get_prediction_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get prediction models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/models/{model_id}/retrain", summary="Retrain Prediction Model")
async def retrain_prediction_model(model_id: int):
    """Retrain a specific prediction model"""
    try:
        success = await predictive_service.retrain_prediction_model(model_id)
        if success:
            return {"message": f"Model {model_id} retraining completed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to retrain model")
    except Exception as e:
        logger.error(f"Failed to retrain prediction model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/accuracy", summary="Get Prediction Accuracy Report")
async def get_prediction_accuracy_report(
    model_type: Optional[str] = Query(None, description="Type of model to get accuracy for")
):
    """Get accuracy report for prediction models"""
    try:
        report = await predictive_service.get_prediction_accuracy_report(model_type)
        return report
    except Exception as e:
        logger.error(f"Failed to get prediction accuracy report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch", response_model=BatchPredictionResponse, summary="Batch Predictions")
async def batch_predictions(request: BatchPredictionRequest):
    """Generate predictions for multiple leads and customers in batch"""
    try:
        import time
        start_time = time.time()
        
        # Process conversion predictions
        conversion_predictions = []
        for lead_id in request.lead_ids:
            try:
                prediction = await predictive_service.predict_conversion_probability(lead_id)
                conversion_predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Failed to predict conversion for lead {lead_id}: {e}")
        
        # Process churn predictions
        churn_predictions = []
        for customer_id in request.customer_ids:
            try:
                prediction = await predictive_service.predict_customer_churn(customer_id)
                churn_predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Failed to predict churn for customer {customer_id}: {e}")
        
        processing_time = time.time() - start_time
        total_processed = len(conversion_predictions) + len(churn_predictions)
        
        return BatchPredictionResponse(
            conversion_predictions=conversion_predictions,
            churn_predictions=churn_predictions,
            total_processed=total_processed,
            processing_time=processing_time
        )
    except Exception as e:
        logger.error(f"Failed to process batch predictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/insights", response_model=PredictionInsightsResponse, summary="Get Prediction Insights")
async def get_prediction_insights(
    days: int = Query(30, description="Number of days to analyze")
):
    """Get insights from recent predictions"""
    try:
        # This would typically aggregate data from recent predictions
        # For now, we'll return sample insights
        
        insights = {
            "total_predictions": 1250,
            "average_confidence": 0.78,
            "top_insights": [
                {
                    "insight": "High-value leads show 40% higher conversion probability",
                    "confidence": 0.85,
                    "impact": "high"
                },
                {
                    "insight": "Customers with recent support interactions have 30% lower churn risk",
                    "confidence": 0.82,
                    "impact": "medium"
                },
                {
                    "insight": "Revenue predictions are most accurate for monthly periods",
                    "confidence": 0.88,
                    "impact": "high"
                }
            ],
            "recommendations": [
                "Focus on high-value lead sources",
                "Increase support engagement for at-risk customers",
                "Use monthly revenue predictions for planning"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return PredictionInsightsResponse(**insights)
    except Exception as e:
        logger.error(f"Failed to get prediction insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/leads/high-conversion", summary="Get High-Conversion Probability Leads")
async def get_high_conversion_leads(
    min_probability: float = Query(0.7, description="Minimum conversion probability"),
    limit: int = Query(50, description="Number of leads to return")
):
    """Get leads with high conversion probability"""
    try:
        async with get_eric_database() as session:
            from ..models import EricLead
            
            # Get leads with recent activity
            leads_query = select(EricLead).where(
                EricLead.created_at >= datetime.utcnow() - timedelta(days=30)
            ).limit(limit)
            
            result = await session.execute(leads_query)
            leads = result.scalars().all()
            
            # Get predictions for these leads
            high_conversion_leads = []
            for lead in leads:
                try:
                    prediction = await predictive_service.predict_conversion_probability(lead.id)
                    if prediction.conversion_probability >= min_probability:
                        high_conversion_leads.append({
                            "lead_id": lead.id,
                            "lead_name": lead.name,
                            "company": lead.company,
                            "conversion_probability": prediction.conversion_probability,
                            "recommended_actions": prediction.recommended_actions
                        })
                except Exception as e:
                    logger.warning(f"Failed to predict for lead {lead.id}: {e}")
            
            # Sort by conversion probability
            high_conversion_leads.sort(key=lambda x: x["conversion_probability"], reverse=True)
            
            return {
                "leads": high_conversion_leads[:limit],
                "total_found": len(high_conversion_leads),
                "min_probability": min_probability
            }
    except Exception as e:
        logger.error(f"Failed to get high conversion leads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/customers/high-churn-risk", summary="Get High Churn Risk Customers")
async def get_high_churn_risk_customers(
    min_probability: float = Query(0.5, description="Minimum churn probability"),
    limit: int = Query(50, description="Number of customers to return")
):
    """Get customers with high churn risk"""
    try:
        async with get_eric_database() as session:
            from ..models import EricDeal
            
            # Get customers with recent deals
            customers_query = select(EricDeal.customer_id).where(
                and_(
                    EricDeal.status == "closed",
                    EricDeal.closed_at >= datetime.utcnow() - timedelta(days=90)
                )
            ).distinct().limit(limit)
            
            result = await session.execute(customers_query)
            customer_ids = [row.customer_id for row in result]
            
            # Get predictions for these customers
            high_churn_customers = []
            for customer_id in customer_ids:
                try:
                    prediction = await predictive_service.predict_customer_churn(customer_id)
                    if prediction.churn_probability >= min_probability:
                        high_churn_customers.append({
                            "customer_id": customer_id,
                            "churn_probability": prediction.churn_probability,
                            "risk_level": prediction.churn_risk_level,
                            "retention_recommendations": prediction.retention_recommendations
                        })
                except Exception as e:
                    logger.warning(f"Failed to predict for customer {customer_id}: {e}")
            
            # Sort by churn probability
            high_churn_customers.sort(key=lambda x: x["churn_probability"], reverse=True)
            
            return {
                "customers": high_churn_customers[:limit],
                "total_found": len(high_churn_customers),
                "min_probability": min_probability
            }
    except Exception as e:
        logger.error(f"Failed to get high churn risk customers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health", summary="Predictive Analytics Health Check")
async def predictive_analytics_health_check():
    """Health check for predictive analytics service"""
    try:
        # Test basic functionality
        models = await predictive_service.get_prediction_models()
        
        return {
            "status": "healthy",
            "service": "predictive_analytics",
            "models_count": len(models),
            "active_models": len([m for m in models if m.is_active]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Predictive analytics health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
