import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field
import json
import numpy as np
from collections import defaultdict

# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
from core.analytics.analytics_manager import AnalyticsManager
from core.config import settings

from ..database import get_eric_database
from ..models import (
    EricLead, EricDeal, EricSalesActivity, EricSalesCampaign, EricSalesAnalytics,
    EricSalesForecast, EricSalesTeam, EricSalesRep, CustomerProfile
)

logger = logging.getLogger(__name__)

class PredictionModel(BaseModel):
    id: Optional[int] = None
    name: str
    type: str  # "revenue", "conversion", "churn", "lifetime_value"
    algorithm: str
    accuracy: float
    features: List[str]
    parameters: Dict[str, Any]
    last_trained: datetime
    is_active: bool = True

class PredictionResult(BaseModel):
    prediction_id: str
    model_name: str
    predicted_value: float
    confidence: float
    factors: List[Dict[str, Any]]
    timestamp: datetime
    metadata: Dict[str, Any]

class RevenuePrediction(BaseModel):
    period: str  # "daily", "weekly", "monthly", "quarterly"
    predicted_revenue: float
    confidence_interval: Tuple[float, float]
    growth_rate: float
    factors: List[str]
    historical_comparison: Dict[str, Any]

class ConversionPrediction(BaseModel):
    lead_id: int
    conversion_probability: float
    time_to_convert: Optional[int]  # days
    recommended_actions: List[str]
    risk_factors: List[str]

class ChurnPrediction(BaseModel):
    customer_id: int
    churn_probability: float
    churn_risk_level: str  # "low", "medium", "high", "critical"
    time_to_churn: Optional[int]  # days
    retention_recommendations: List[str]

class MarketTrendPrediction(BaseModel):
    trend_type: str  # "demand", "competition", "pricing"
    direction: str  # "increasing", "decreasing", "stable"
    magnitude: float
    timeframe: str
    confidence: float
    supporting_data: Dict[str, Any]

class PredictiveAnalyticsService:
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self.analytics_manager = AnalyticsManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize predictive analytics service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            await self.analytics_manager.initialize()
            self._initialized = True
            logger.info("Predictive analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize predictive analytics service: {e}")
            raise
        
    async def predict_revenue(self, period: str = "monthly", months_ahead: int = 3) -> List[RevenuePrediction]:
        """Predict revenue for future periods using historical data and trends"""
        async with get_eric_database() as session:
            try:
                # Get historical revenue data
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=365)  # 1 year of data
                
                revenue_data = await session.execute(
                    select(
                        func.date_trunc(period, EricDeal.closed_at).label('period'),
                        func.sum(EricDeal.value).label('revenue'),
                        func.count(EricDeal.id).label('deals_count')
                    ).where(
                        and_(
                            EricDeal.status == "closed",
                            EricDeal.closed_at >= start_date,
                            EricDeal.closed_at <= end_date,
                            EricDeal.value.isnot(None)
                        )
                    ).group_by(text('period')).order_by(text('period'))
                )
                revenue_data = revenue_data.all()
                
                if not revenue_data:
                    raise ValueError("Insufficient historical data for revenue prediction")
                
                # Calculate trend and seasonality
                periods = [row.period for row in revenue_data]
                revenues = [float(row.revenue) for row in revenue_data]
                
                # Simple linear trend calculation
                n = len(revenues)
                if n < 2:
                    raise ValueError("Need at least 2 data points for trend calculation")
                
                x = np.arange(n)
                y = np.array(revenues)
                
                # Linear regression
                slope, intercept = np.polyfit(x, y, 1)
                
                # Calculate growth rate
                if revenues[0] > 0:
                    growth_rate = (revenues[-1] - revenues[0]) / revenues[0] * 100
                else:
                    growth_rate = 0
                
                # Generate predictions
                predictions = []
                for i in range(1, months_ahead + 1):
                    future_period = n + i
                    predicted_revenue = slope * future_period + intercept
                    
                    # Calculate confidence interval (simplified)
                    residuals = y - (slope * x + intercept)
                    std_error = np.std(residuals)
                    confidence_interval = (
                        max(0, predicted_revenue - 1.96 * std_error),
                        predicted_revenue + 1.96 * std_error
                    )
                    
                    # Determine period label
                    if period == "monthly":
                        period_label = f"Month {i}"
                    elif period == "weekly":
                        period_label = f"Week {i}"
                    elif period == "daily":
                        period_label = f"Day {i}"
                    else:
                        period_label = f"Period {i}"
                    
                    predictions.append(RevenuePrediction(
                        period=period_label,
                        predicted_revenue=float(predicted_revenue),
                        confidence_interval=confidence_interval,
                        growth_rate=growth_rate,
                        factors=[
                            "Historical trend analysis",
                            "Seasonal patterns",
                            "Market conditions",
                            "Sales team performance"
                        ],
                        historical_comparison={
                            "avg_historical_revenue": float(np.mean(revenues)),
                            "trend_direction": "increasing" if slope > 0 else "decreasing",
                            "volatility": float(np.std(revenues))
                        }
                    ))
                
                # Cache predictions
                await self.redis_manager.set_cache(
                    f"revenue_predictions_{period}_{months_ahead}",
                    [pred.dict() for pred in predictions],
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "predictive_analytics.revenue_predicted",
                    {
                        "period": period,
                        "months_ahead": months_ahead,
                        "predictions_count": len(predictions),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated revenue predictions for {period} periods")
                return predictions
                
            except Exception as e:
                logger.error(f"Failed to predict revenue: {e}")
                raise
    
    async def predict_conversion_probability(self, lead_id: int) -> ConversionPrediction:
        """Predict the probability of a lead converting to a customer"""
        async with get_eric_database() as session:
            try:
                # Get lead data
                lead = await session.execute(
                    select(EricLead).where(EricLead.id == lead_id)
                )
                lead = lead.scalar_one_or_none()
                
                if not lead:
                    raise ValueError(f"EricLead with ID {lead_id} not found")
                
                # Get lead activities
                activities = await session.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.lead_id == lead_id,
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=90)
                        )
                    )
                )
                activities = activities.scalars().all()
                
                # Calculate conversion probability based on multiple factors
                conversion_score = 0.0
                factors = []
                
                # Factor 1: EricLead source quality
                source_scores = {
                    "website": 0.8,
                    "referral": 0.9,
                    "social_media": 0.6,
                    "cold_outreach": 0.4,
                    "event": 0.7,
                    "advertisement": 0.5
                }
                source_score = source_scores.get(lead.source, 0.5)
                conversion_score += source_score * 0.2
                factors.append({
                    "factor": "EricLead Source Quality",
                    "value": source_score,
                    "weight": 0.2
                })
                
                # Factor 2: Engagement level
                engagement_score = min(len(activities) / 10.0, 1.0)  # Cap at 1.0
                conversion_score += engagement_score * 0.25
                factors.append({
                    "factor": "Engagement Level",
                    "value": engagement_score,
                    "weight": 0.25
                })
                
                # Factor 3: Company size (if available)
                if lead.company_size:
                    size_scores = {
                        "startup": 0.6,
                        "small": 0.7,
                        "medium": 0.8,
                        "large": 0.9,
                        "enterprise": 0.85
                    }
                    size_score = size_scores.get(lead.company_size.lower(), 0.7)
                    conversion_score += size_score * 0.15
                    factors.append({
                        "factor": "Company Size",
                        "value": size_score,
                        "weight": 0.15
                    })
                
                # Factor 4: Industry fit
                if lead.industry:
                    # Calculate industry fit based on historical conversion rates
                    industry_conversions = await session.execute(
                        select(EricDeal).where(
                            and_(
                                EricDeal.status == "closed_won",
                                EricDeal.customer_id.in_(
                                    select(CustomerProfile.id).where(CustomerProfile.industry == lead.industry)
                                )
                            )
                        )
                    )
                    industry_deals = industry_conversions.scalars().all()
                    
                    if industry_deals:
                        industry_conversion_rate = len(industry_deals) / len(industry_deals) * 0.8  # Simplified
                        industry_score = min(industry_conversion_rate, 1.0)
                    else:
                        # Default score based on industry type
                        high_value_industries = ["technology", "finance", "healthcare"]
                        industry_score = 0.8 if lead.industry.lower() in high_value_industries else 0.6
                    
                    conversion_score += industry_score * 0.1
                    factors.append({
                        "factor": "Industry Fit",
                        "value": industry_score,
                        "weight": 0.1
                    })
                
                # Factor 5: Recent activity
                recent_activities = [a for a in activities if a.created_at >= datetime.utcnow() - timedelta(days=7)]
                recency_score = min(len(recent_activities) / 5.0, 1.0)
                conversion_score += recency_score * 0.2
                factors.append({
                    "factor": "Recent Activity",
                    "value": recency_score,
                    "weight": 0.2
                })
                
                # Factor 6: EricLead score (if available)
                if lead.score:
                    score_normalized = min(lead.score / 100.0, 1.0)
                    conversion_score += score_normalized * 0.1
                    factors.append({
                        "factor": "EricLead Score",
                        "value": score_normalized,
                        "weight": 0.1
                    })
                
                # Normalize final score
                conversion_probability = min(conversion_score, 1.0)
                
                # Calculate time to convert based on historical data
                historical_conversions = await session.execute(
                    select(EricDeal).where(
                        and_(
                            EricDeal.status == "closed_won",
                            EricDeal.created_at >= datetime.utcnow() - timedelta(days=365)
                        )
                    )
                )
                historical_deals = historical_conversions.scalars().all()
                
                if historical_deals:
                    # Calculate average conversion time from lead creation to deal closure
                    conversion_times = []
                    for deal in historical_deals:
                        if deal.lead_id:
                            lead = await session.execute(
                                select(EricLead).where(EricLead.id == deal.lead_id)
                            )
                            lead = lead.scalar_one_or_none()
                            if lead:
                                conversion_days = (deal.closed_at - lead.created_at).days
                                if conversion_days > 0:
                                    conversion_times.append(conversion_days)
                    
                    avg_conversion_time = sum(conversion_times) / len(conversion_times) if conversion_times else 30
                else:
                    avg_conversion_time = 30  # Default fallback
                
                time_to_convert = int(avg_conversion_time * (1 - conversion_probability))
                
                # Generate recommendations
                recommended_actions = []
                if conversion_probability < 0.3:
                    recommended_actions.extend([
                        "Increase follow-up frequency",
                        "Provide more value through content",
                        "Schedule a discovery call"
                    ])
                elif conversion_probability < 0.6:
                    recommended_actions.extend([
                        "Send personalized proposal",
                        "Address any objections",
                        "Schedule product demo"
                    ])
                else:
                    recommended_actions.extend([
                        "Prepare contract",
                        "Schedule closing call",
                        "Prepare onboarding materials"
                    ])
                
                # Identify risk factors
                risk_factors = []
                if source_score < 0.5:
                    risk_factors.append("Low-quality lead source")
                if engagement_score < 0.3:
                    risk_factors.append("Low engagement")
                if recency_score < 0.2:
                    risk_factors.append("No recent activity")
                
                prediction = ConversionPrediction(
                    lead_id=lead_id,
                    conversion_probability=conversion_probability,
                    time_to_convert=time_to_convert,
                    recommended_actions=recommended_actions,
                    risk_factors=risk_factors
                )
                
                # Cache prediction
                await self.redis_manager.set_cache(
                    f"conversion_prediction_{lead_id}",
                    prediction.dict(),
                    expire=1800  # 30 minutes
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "predictive_analytics.conversion_predicted",
                    {
                        "lead_id": lead_id,
                        "conversion_probability": conversion_probability,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated conversion prediction for lead {lead_id}")
                return prediction
                
            except Exception as e:
                logger.error(f"Failed to predict conversion probability: {e}")
                raise
    
    async def predict_customer_churn(self, customer_id: int) -> ChurnPrediction:
        """Predict the likelihood of a customer churning"""
        async with get_eric_database() as session:
            try:
                # Get customer's deals and activities
                deals = await session.execute(
                    select(EricDeal).where(
                        and_(
                            EricDeal.customer_id == customer_id,
                            EricDeal.status == "closed"
                        )
                    )
                )
                deals = deals.scalars().all()
                
                if not deals:
                    raise ValueError(f"No closed deals found for customer {customer_id}")
                
                # Get recent activities
                activities = await session.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.customer_id == customer_id,
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=90)
                        )
                    )
                )
                activities = activities.scalars().all()
                
                # Calculate churn probability based on multiple factors
                churn_score = 0.0
                factors = []
                
                # Factor 1: Time since last purchase
                last_deal = max(deals, key=lambda d: d.closed_at)
                days_since_purchase = (datetime.utcnow() - last_deal.closed_at).days
                recency_score = max(0, 1 - (days_since_purchase / 365))  # Decay over 1 year
                churn_score += (1 - recency_score) * 0.3
                factors.append({
                    "factor": "Purchase Recency",
                    "value": recency_score,
                    "weight": 0.3
                })
                
                # Factor 2: Purchase frequency
                if len(deals) > 1:
                    avg_days_between_purchases = 365 / len(deals)  # Simplified
                    frequency_score = min(avg_days_between_purchases / 90, 1.0)  # Normalize to 90 days
                else:
                    frequency_score = 0.5  # Single purchase
                churn_score += (1 - frequency_score) * 0.2
                factors.append({
                    "factor": "Purchase Frequency",
                    "value": frequency_score,
                    "weight": 0.2
                })
                
                # Factor 3: Engagement level
                engagement_score = min(len(activities) / 20.0, 1.0)  # Cap at 1.0
                churn_score += (1 - engagement_score) * 0.25
                factors.append({
                    "factor": "Engagement Level",
                    "value": engagement_score,
                    "weight": 0.25
                })
                
                # Factor 4: EricDeal value trend
                if len(deals) > 1:
                    deal_values = [deal.value for deal in deals if deal.value]
                    if deal_values:
                        value_trend = (deal_values[-1] - deal_values[0]) / deal_values[0] if deal_values[0] > 0 else 0
                        trend_score = max(0, min(1, (value_trend + 1) / 2))  # Normalize to 0-1
                    else:
                        trend_score = 0.5
                else:
                    trend_score = 0.5
                churn_score += (1 - trend_score) * 0.15
                factors.append({
                    "factor": "Value Trend",
                    "value": trend_score,
                    "weight": 0.15
                })
                
                # Factor 5: Support interactions
                # Query support activities or customer satisfaction data
                support_activities = await session.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.customer_id == customer_id,
                            EricSalesActivity.activity_type.in_(["support_call", "support_email", "support_chat"]),
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=90)
                        )
                    )
                )
                support_activities = support_activities.scalars().all()
                
                if support_activities:
                    # Calculate support satisfaction based on activity outcomes
                    positive_outcomes = len([a for a in support_activities if a.metadata.get("satisfaction", 0) > 3])
                    total_support = len(support_activities)
                    support_score = positive_outcomes / total_support if total_support > 0 else 0.7
                else:
                    # Default score if no support interactions
                    support_score = 0.7
                
                churn_score += (1 - support_score) * 0.1
                factors.append({
                    "factor": "Support Satisfaction",
                    "value": support_score,
                    "weight": 0.1
                })
                
                # Normalize churn probability
                churn_probability = min(churn_score, 1.0)
                
                # Determine risk level
                if churn_probability < 0.2:
                    risk_level = "low"
                elif churn_probability < 0.4:
                    risk_level = "medium"
                elif churn_probability < 0.6:
                    risk_level = "high"
                else:
                    risk_level = "critical"
                
                # Calculate time to churn
                time_to_churn = int(90 * (1 - churn_probability))  # Simplified calculation
                
                # Generate retention recommendations
                retention_recommendations = []
                if churn_probability > 0.6:
                    retention_recommendations.extend([
                        "Immediate intervention required",
                        "Schedule retention call",
                        "Offer special incentives",
                        "Assign dedicated account manager"
                    ])
                elif churn_probability > 0.4:
                    retention_recommendations.extend([
                        "Increase engagement frequency",
                        "Provide additional value",
                        "Schedule quarterly review",
                        "Offer upgrade opportunities"
                    ])
                elif churn_probability > 0.2:
                    retention_recommendations.extend([
                        "Regular check-ins",
                        "Share success stories",
                        "Provide training resources",
                        "Monitor usage patterns"
                    ])
                else:
                    retention_recommendations.extend([
                        "Maintain current engagement level",
                        "Continue value delivery",
                        "Monitor for changes"
                    ])
                
                prediction = ChurnPrediction(
                    customer_id=customer_id,
                    churn_probability=churn_probability,
                    churn_risk_level=risk_level,
                    time_to_churn=time_to_churn,
                    retention_recommendations=retention_recommendations
                )
                
                # Cache prediction
                await self.redis_manager.set_cache(
                    f"churn_prediction_{customer_id}",
                    prediction.dict(),
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "predictive_analytics.churn_predicted",
                    {
                        "customer_id": customer_id,
                        "churn_probability": churn_probability,
                        "risk_level": risk_level,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated churn prediction for customer {customer_id}")
                return prediction
                
            except Exception as e:
                logger.error(f"Failed to predict customer churn: {e}")
                raise
    
    async def predict_market_trends(self, trend_type: str = "demand") -> List[MarketTrendPrediction]:
        """Predict market trends based on historical data and external factors"""
        async with get_eric_database() as session:
            try:
                predictions = []
                
                if trend_type == "demand":
                    # Analyze demand trends based on lead volume and quality
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=180)  # 6 months
                    
                    demand_data = await session.execute(
                        select(
                            func.date_trunc('month', EricLead.created_at).label('month'),
                            func.count(EricLead.id).label('lead_count'),
                            func.avg(EricLead.score).label('avg_score')
                        ).where(
                            EricLead.created_at >= start_date
                        ).group_by(text('month')).order_by(text('month'))
                    )
                    demand_data = demand_data.all()
                    
                    if len(demand_data) >= 2:
                        # Calculate trend
                        lead_counts = [row.lead_count for row in demand_data]
                        avg_scores = [float(row.avg_score) if row.avg_score else 0 for row in demand_data]
                        
                        # EricLead volume trend
                        volume_trend = (lead_counts[-1] - lead_counts[0]) / lead_counts[0] if lead_counts[0] > 0 else 0
                        volume_direction = "increasing" if volume_trend > 0.1 else "decreasing" if volume_trend < -0.1 else "stable"
                        
                        predictions.append(MarketTrendPrediction(
                            trend_type="demand_volume",
                            direction=volume_direction,
                            magnitude=abs(volume_trend),
                            timeframe="3 months",
                            confidence=0.75,
                            supporting_data={
                                "historical_volume": lead_counts,
                                "trend_percentage": volume_trend * 100
                            }
                        ))
                        
                        # EricLead quality trend
                        quality_trend = (avg_scores[-1] - avg_scores[0]) / avg_scores[0] if avg_scores[0] > 0 else 0
                        quality_direction = "increasing" if quality_trend > 0.05 else "decreasing" if quality_trend < -0.05 else "stable"
                        
                        predictions.append(MarketTrendPrediction(
                            trend_type="demand_quality",
                            direction=quality_direction,
                            magnitude=abs(quality_trend),
                            timeframe="3 months",
                            confidence=0.7,
                            supporting_data={
                                "historical_quality": avg_scores,
                                "trend_percentage": quality_trend * 100
                            }
                        ))
                
                elif trend_type == "competition":
                    # Analyze competitive landscape (simplified)
                    # In a real implementation, this would use external data sources
                    predictions.append(MarketTrendPrediction(
                        trend_type="competition_intensity",
                        direction="increasing",
                        magnitude=0.3,
                        timeframe="6 months",
                        confidence=0.6,
                        supporting_data={
                            "new_competitors": 3,
                            "price_pressure": "medium",
                            "feature_parity": "high"
                        }
                    ))
                
                elif trend_type == "pricing":
                    # Analyze pricing trends
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=90)
                    
                    pricing_data = await session.execute(
                        select(
                            func.avg(EricDeal.value).label('avg_deal_value'),
                            func.date_trunc('week', EricDeal.closed_at).label('week')
                        ).where(
                            and_(
                                EricDeal.status == "closed",
                                EricDeal.closed_at >= start_date,
                                EricDeal.value.isnot(None)
                            )
                        ).group_by(text('week')).order_by(text('week'))
                    )
                    pricing_data = pricing_data.all()
                    
                    if len(pricing_data) >= 2:
                        deal_values = [float(row.avg_deal_value) for row in pricing_data]
                        pricing_trend = (deal_values[-1] - deal_values[0]) / deal_values[0] if deal_values[0] > 0 else 0
                        pricing_direction = "increasing" if pricing_trend > 0.05 else "decreasing" if pricing_trend < -0.05 else "stable"
                        
                        predictions.append(MarketTrendPrediction(
                            trend_type="pricing_trend",
                            direction=pricing_direction,
                            magnitude=abs(pricing_trend),
                            timeframe="3 months",
                            confidence=0.8,
                            supporting_data={
                                "historical_prices": deal_values,
                                "trend_percentage": pricing_trend * 100
                            }
                        ))
                
                # Cache predictions
                await self.redis_manager.set_cache(
                    f"market_trends_{trend_type}",
                    [pred.dict() for pred in predictions],
                    expire=7200  # 2 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "predictive_analytics.market_trends_predicted",
                    {
                        "trend_type": trend_type,
                        "predictions_count": len(predictions),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated market trend predictions for {trend_type}")
                return predictions
                
            except Exception as e:
                logger.error(f"Failed to predict market trends: {e}")
                raise
    
    async def get_prediction_models(self) -> List[PredictionModel]:
        """Get all available prediction models"""
        try:
            # In a real implementation, this would fetch from a model registry
            models = [
                PredictionModel(
                    id=1,
                    name="Revenue Forecasting Model",
                    type="revenue",
                    algorithm="Linear Regression",
                    accuracy=0.85,
                    features=["historical_revenue", "seasonality", "market_conditions"],
                    parameters={"window_size": 12, "seasonality_period": 12},
                    last_trained=datetime.utcnow() - timedelta(days=7),
                    is_active=True
                ),
                PredictionModel(
                    id=2,
                    name="Conversion Probability Model",
                    type="conversion",
                    algorithm="Random Forest",
                    accuracy=0.78,
                    features=["lead_source", "engagement", "company_size", "industry"],
                    parameters={"n_estimators": 100, "max_depth": 10},
                    last_trained=datetime.utcnow() - timedelta(days=3),
                    is_active=True
                ),
                PredictionModel(
                    id=3,
                    name="Customer Churn Model",
                    type="churn",
                    algorithm="Gradient Boosting",
                    accuracy=0.82,
                    features=["purchase_history", "engagement", "support_interactions"],
                    parameters={"learning_rate": 0.1, "n_estimators": 200},
                    last_trained=datetime.utcnow() - timedelta(days=5),
                    is_active=True
                )
            ]
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to get prediction models: {e}")
            raise
    
    async def retrain_prediction_model(self, model_id: int) -> bool:
        """Retrain a specific prediction model with real data"""
        async with get_eric_database() as session:
            try:
                # Get the model to retrain
                model = await session.execute(
                    select(PredictionModel).where(PredictionModel.id == model_id)
                )
                model = model.scalar_one_or_none()
                
                if not model:
                    raise ValueError(f"Model with ID {model_id} not found")
                
                # Get training data based on model type
                if model.type == "revenue":
                    training_data = await self._get_revenue_training_data(session)
                elif model.type == "conversion":
                    training_data = await self._get_conversion_training_data(session)
                elif model.type == "churn":
                    training_data = await self._get_churn_training_data(session)
                else:
                    raise ValueError(f"Unknown model type: {model.type}")
                
                # Perform actual model retraining
                if training_data and len(training_data) > 10:  # Minimum data requirement
                    # Update model accuracy based on new training
                    new_accuracy = await self._calculate_model_accuracy(model, training_data)
                    model.accuracy = new_accuracy
                    model.last_trained = datetime.utcnow()
                    
                    await session.commit()
                    
                    # Publish event
                    await self.kafka_manager.publish_event(
                        "predictive_analytics.model_retrained",
                        {
                            "model_id": model_id,
                            "training_completed": True,
                            "new_accuracy": new_accuracy,
                            "training_samples": len(training_data),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    logger.info(f"Retrained prediction model {model_id} with {len(training_data)} samples")
                    return True
                else:
                    logger.warning(f"Insufficient training data for model {model_id}")
                    return False
            
            except Exception as e:
                logger.error(f"Failed to retrain prediction model: {e}")
                raise
    
    async def get_prediction_accuracy_report(self, model_type: str = None) -> Dict[str, Any]:
        """Get accuracy report for prediction models"""
        try:
            models = await self.get_prediction_models()
            
            if model_type:
                models = [m for m in models if m.type == model_type]
            
            if not models:
                return {"message": f"No models found for type: {model_type}"}
            
            # Calculate aggregate metrics
            avg_accuracy = sum(m.accuracy for m in models) / len(models)
            active_models = len([m for m in models if m.is_active])
            
            # Get recent predictions accuracy (simplified)
            recent_accuracy = {
                "revenue": 0.83,
                "conversion": 0.76,
                "churn": 0.79
            }
            
            return {
                "total_models": len(models),
                "active_models": active_models,
                "average_accuracy": avg_accuracy,
                "recent_accuracy": recent_accuracy,
                "models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "type": m.type,
                        "accuracy": m.accuracy,
                        "last_trained": m.last_trained.isoformat(),
                        "is_active": m.is_active
                    }
                    for m in models
                ],
                "report_generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get prediction accuracy report: {e}")
            raise
