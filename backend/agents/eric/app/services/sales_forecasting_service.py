import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.storage.chroma_manager import ChromaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..models import EricLead, EricDeal, EricSalesActivity, LeadStatus, SalesStage, EricSalesForecast
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class SalesForecastingService:
    """Service for sales forecasting and revenue prediction"""
    
    def __init__(self):
        self.nlp_utils = None
        self.redis_client = None
        self.chroma_manager = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize sales forecasting service"""
        if self._initialized:
            return
        
        try:
            # NLPUtils removed - not used in this service
            self.redis_client = await init_redis()
            self.chroma_manager = ChromaManager()
            await self.chroma_manager.initialize()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric sales forecasting service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sales forecasting service: {e}")
            raise
    
    async def generate_sales_forecast(
        self,
        brand_id: int,
        forecast_period: str = "30d",
        forecast_type: str = "revenue"
    ) -> Dict[str, Any]:
        """Generate sales forecast for specified period"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Calculate date range
            end_date = datetime.now()
            if forecast_period == "7d":
                start_date = end_date - timedelta(days=7)
                days_ahead = 7
            elif forecast_period == "30d":
                start_date = end_date - timedelta(days=30)
                days_ahead = 30
            elif forecast_period == "90d":
                start_date = end_date - timedelta(days=90)
                days_ahead = 90
            else:
                start_date = end_date - timedelta(days=30)
                days_ahead = 30
            
            # Get historical data
            historical_deals = db.query(EricDeal).filter(
                and_(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_date,
                    EricDeal.created_at <= end_date
                )
            ).all()
            
            # Get historical leads
            historical_leads = db.query(EricLead).filter(
                and_(
                    EricLead.brand_id == brand_id,
                    EricLead.created_at >= start_date,
                    EricLead.created_at <= end_date
                )
            ).all()
            
            # Calculate conversion rates
            total_leads = len(historical_leads)
            qualified_leads = len([l for l in historical_leads if l.lead_status == LeadStatus.QUALIFIED])
            converted_leads = len([l for l in historical_leads if l.lead_status in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST]])
            
            lead_to_qualified_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
            qualified_to_deal_rate = (converted_leads / qualified_leads * 100) if qualified_leads > 0 else 0
            
            # Calculate revenue metrics
            total_revenue = sum([d.deal_value for d in historical_deals if d.sales_stage == SalesStage.CLOSED and d.win_reason])
            avg_deal_value = total_revenue / len([d for d in historical_deals if d.sales_stage == SalesStage.CLOSED and d.win_reason]) if len([d for d in historical_deals if d.sales_stage == SalesStage.CLOSED and d.win_reason]) > 0 else 0
            
            # Generate AI-powered forecast
            forecast_data = await self._generate_ai_forecast(
                historical_deals=historical_deals,
                historical_leads=historical_leads,
                conversion_rates={
                    "lead_to_qualified": lead_to_qualified_rate,
                    "qualified_to_deal": qualified_to_deal_rate
                },
                revenue_metrics={
                    "total_revenue": total_revenue,
                    "avg_deal_value": avg_deal_value
                },
                forecast_period=forecast_period,
                days_ahead=days_ahead
            )
            
            # Store forecast in database
            forecast = EricSalesForecast(
                brand_id=brand_id,
                forecast_type=forecast_type,
                forecast_period=forecast_period,
                forecast_data=forecast_data,
                confidence_score=forecast_data.get("confidence_score", 0.8),
                created_at=datetime.now()
            )
            db.add(forecast)
            db.commit()
            
            return {
                "success": True,
                "forecast_id": forecast.id,
                "forecast_data": forecast_data,
                "historical_metrics": {
                    "total_leads": total_leads,
                    "qualified_leads": qualified_leads,
                    "converted_leads": converted_leads,
                    "lead_to_qualified_rate": round(lead_to_qualified_rate, 2),
                    "qualified_to_deal_rate": round(qualified_to_deal_rate, 2),
                    "total_revenue": total_revenue,
                    "avg_deal_value": round(avg_deal_value, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate sales forecast: {e}")
            return {
                "success": False,
                "error": f"Failed to generate sales forecast: {str(e)}"
            }
    
    async def predict_revenue_trends(
        self,
        brand_id: int,
        trend_period: str = "90d"
    ) -> Dict[str, Any]:
        """Predict revenue trends and patterns"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Calculate date range
            end_date = datetime.now()
            if trend_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif trend_period == "90d":
                start_date = end_date - timedelta(days=90)
            elif trend_period == "180d":
                start_date = end_date - timedelta(days=180)
            else:
                start_date = end_date - timedelta(days=90)
            
            # Get revenue data by month
            monthly_revenue = db.query(
                func.date_trunc('month', EricDeal.created_at).label('month'),
                func.sum(EricDeal.deal_value).label('revenue')
            ).filter(
                and_(
                    EricDeal.brand_id == brand_id,
                    EricDeal.created_at >= start_date,
                    EricDeal.created_at <= end_date,
                    EricDeal.sales_stage == SalesStage.CLOSED,
                    EricDeal.win_reason.isnot(None)
                )
            ).group_by(func.date_trunc('month', EricDeal.created_at)).all()
            
            # Analyze trends
            revenue_trends = []
            for month_data in monthly_revenue:
                revenue_trends.append({
                    "month": month_data.month.strftime("%Y-%m"),
                    "revenue": float(month_data.revenue),
                    "growth_rate": 0  # Will be calculated
                })
            
            # Calculate growth rates
            for i in range(1, len(revenue_trends)):
                prev_revenue = revenue_trends[i-1]["revenue"]
                curr_revenue = revenue_trends[i]["revenue"]
                if prev_revenue > 0:
                    growth_rate = ((curr_revenue - prev_revenue) / prev_revenue) * 100
                    revenue_trends[i]["growth_rate"] = round(growth_rate, 2)
            
            # Generate trend predictions
            trend_predictions = await self._predict_trends(revenue_trends)
            
            return {
                "success": True,
                "trend_period": trend_period,
                "revenue_trends": revenue_trends,
                "predictions": trend_predictions,
                "insights": await self._generate_trend_insights(revenue_trends)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict revenue trends: {e}")
            return {
                "success": False,
                "error": f"Failed to predict revenue trends: {str(e)}"
            }
    
    async def forecast_pipeline_performance(
        self,
        brand_id: int,
        pipeline_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Forecast pipeline performance and conversion rates"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Get current pipeline deals
            query = db.query(EricDeal).filter(EricDeal.brand_id == brand_id)
            if pipeline_id:
                query = query.filter(EricDeal.pipeline_id == pipeline_id)
            
            pipeline_deals = query.all()
            
            # Analyze pipeline stages
            stage_analysis = {}
            for stage in SalesStage:
                stage_deals = [d for d in pipeline_deals if d.sales_stage == stage]
                stage_value = sum([d.deal_value for d in stage_deals])
                stage_probability = sum([d.probability for d in stage_deals]) / len(stage_deals) if stage_deals else 0
                
                stage_analysis[stage.value] = {
                    "deal_count": len(stage_deals),
                    "total_value": stage_value,
                    "avg_probability": round(stage_probability, 2),
                    "weighted_value": stage_value * (stage_probability / 100)
                }
            
            # Calculate pipeline metrics
            total_pipeline_value = sum([d.deal_value for d in pipeline_deals])
            weighted_pipeline_value = sum([d.deal_value * (d.probability / 100) for d in pipeline_deals])
            
            # Predict conversion rates
            conversion_predictions = await self._predict_pipeline_conversions(stage_analysis)
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "stage_analysis": stage_analysis,
                "pipeline_metrics": {
                    "total_deals": len(pipeline_deals),
                    "total_value": total_pipeline_value,
                    "weighted_value": weighted_pipeline_value,
                    "avg_probability": round(sum([d.probability for d in pipeline_deals]) / len(pipeline_deals), 2) if pipeline_deals else 0
                },
                "conversion_predictions": conversion_predictions,
                "recommendations": await self._generate_pipeline_recommendations(stage_analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to forecast pipeline performance: {e}")
            return {
                "success": False,
                "error": f"Failed to forecast pipeline performance: {str(e)}"
            }
    
    async def get_forecast_history(
        self,
        brand_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get forecast history and accuracy"""
        try:
            await self.initialize()
            
            db = next(get_db())
            
            # Get recent forecasts
            forecasts = db.query(EricSalesForecast).filter(
                EricSalesForecast.brand_id == brand_id
            ).order_by(desc(EricSalesForecast.created_at)).limit(limit).all()
            
            forecast_history = []
            for forecast in forecasts:
                forecast_history.append({
                    "id": forecast.id,
                    "forecast_type": forecast.forecast_type,
                    "forecast_period": forecast.forecast_period,
                    "confidence_score": forecast.confidence_score,
                    "created_at": forecast.created_at.isoformat(),
                    "forecast_data": forecast.forecast_data
                })
            
            return {
                "success": True,
                "forecast_history": forecast_history,
                "total_forecasts": len(forecast_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get forecast history: {e}")
            return {
                "success": False,
                "error": f"Failed to get forecast history: {str(e)}"
            }
    
    async def _generate_ai_forecast(
        self,
        historical_deals: List[EricDeal],
        historical_leads: List[EricLead],
        conversion_rates: Dict[str, float],
        revenue_metrics: Dict[str, float],
        forecast_period: str,
        days_ahead: int
    ) -> Dict[str, Any]:
        """Generate AI-powered forecast using NLP"""
        try:
            # Prepare forecast context
            forecast_context = {
                "historical_deals_count": len(historical_deals),
                "historical_leads_count": len(historical_leads),
                "conversion_rates": conversion_rates,
                "revenue_metrics": revenue_metrics,
                "forecast_period": forecast_period,
                "days_ahead": days_ahead
            }
            
            # Generate forecast using AI
            forecast_prompt = f"""
            Generate a sales forecast based on the following data:
            
            Historical Data:
            - Deals: {len(historical_deals)}
            - Leads: {len(historical_leads)}
            - EricLead to Qualified Rate: {conversion_rates['lead_to_qualified']}%
            - Qualified to EricDeal Rate: {conversion_rates['qualified_to_deal']}%
            - Total Revenue: ${revenue_metrics['total_revenue']:,.2f}
            - Average EricDeal Value: ${revenue_metrics['avg_deal_value']:,.2f}
            
            Forecast Period: {forecast_period} ({days_ahead} days)
            
            Provide forecast in JSON format with:
            - predicted_revenue
            - predicted_leads
            - predicted_deals
            - confidence_score
            - growth_rate
            - key_factors
            """
            
            # Use AI Service Manager instead of NLPUtils (consistent with Aria)
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates sales forecasts in JSON format."},
                {"role": "user", "content": forecast_prompt}
            ]
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            ai_forecast = ai_response.text_content if ai_response.success else "{}"
            
            # Parse AI response
            try:
                forecast_data = json.loads(ai_forecast)
            except:
                # Fallback forecast calculation
                avg_daily_revenue = revenue_metrics['total_revenue'] / 30 if revenue_metrics['total_revenue'] > 0 else 0
                predicted_revenue = avg_daily_revenue * days_ahead
                
                forecast_data = {
                    "predicted_revenue": predicted_revenue,
                    "predicted_leads": len(historical_leads) * (days_ahead / 30),
                    "predicted_deals": len(historical_deals) * (days_ahead / 30),
                    "confidence_score": 0.7,
                    "growth_rate": 0.0,
                    "key_factors": ["Historical performance", "Seasonal trends", "Market conditions"]
                }
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"Failed to generate AI forecast: {e}")
            return {
                "predicted_revenue": 0,
                "predicted_leads": 0,
                "predicted_deals": 0,
                "confidence_score": 0.5,
                "growth_rate": 0.0,
                "key_factors": ["Insufficient data"]
            }
    
    async def _predict_trends(self, revenue_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future trends based on historical data"""
        try:
            if len(revenue_trends) < 2:
                return {
                    "next_month_prediction": 0,
                    "trend_direction": "stable",
                    "confidence": 0.5
                }
            
            # Calculate trend direction
            recent_growth_rates = [t["growth_rate"] for t in revenue_trends[-3:]]
            avg_growth_rate = sum(recent_growth_rates) / len(recent_growth_rates)
            
            # Predict next month
            last_revenue = revenue_trends[-1]["revenue"]
            predicted_revenue = last_revenue * (1 + avg_growth_rate / 100)
            
            # Determine trend direction
            if avg_growth_rate > 5:
                trend_direction = "increasing"
            elif avg_growth_rate < -5:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            return {
                "next_month_prediction": round(predicted_revenue, 2),
                "trend_direction": trend_direction,
                "avg_growth_rate": round(avg_growth_rate, 2),
                "confidence": min(0.9, 0.5 + abs(avg_growth_rate) / 100)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict trends: {e}")
            return {
                "next_month_prediction": 0,
                "trend_direction": "stable",
                "confidence": 0.5
            }
    
    async def _predict_pipeline_conversions(self, stage_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict pipeline stage conversions"""
        try:
            conversions = {}
            total_weighted_value = sum([stage["weighted_value"] for stage in stage_analysis.values()])
            
            for stage_name, stage_data in stage_analysis.items():
                if total_weighted_value > 0:
                    conversion_probability = (stage_data["weighted_value"] / total_weighted_value) * 100
                else:
                    conversion_probability = stage_data["avg_probability"]
                
                conversions[stage_name] = {
                    "conversion_probability": round(conversion_probability, 2),
                    "expected_revenue": stage_data["weighted_value"],
                    "deal_count": stage_data["deal_count"]
                }
            
            return conversions
            
        except Exception as e:
            logger.error(f"Failed to predict pipeline conversions: {e}")
            return {}
    
    async def _generate_trend_insights(self, revenue_trends: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from revenue trends"""
        try:
            insights = []
            
            if len(revenue_trends) >= 2:
                # Growth analysis
                recent_growth = revenue_trends[-1]["growth_rate"]
                if recent_growth > 10:
                    insights.append("Strong revenue growth detected - consider scaling successful strategies")
                elif recent_growth < -10:
                    insights.append("Revenue decline detected - review sales strategies and market conditions")
                
                # Trend consistency
                growth_rates = [t["growth_rate"] for t in revenue_trends[-3:]]
                if len(set(growth_rates)) == 1:
                    insights.append("Consistent growth pattern - current strategies are stable")
                elif max(growth_rates) - min(growth_rates) > 20:
                    insights.append("High volatility in revenue - investigate external factors")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate trend insights: {e}")
            return ["Unable to generate insights due to insufficient data"]
    
    async def _generate_pipeline_recommendations(self, stage_analysis: Dict[str, Any]) -> List[str]:
        """Generate pipeline optimization recommendations"""
        try:
            recommendations = []
            
            # Analyze stage bottlenecks
            for stage_name, stage_data in stage_analysis.items():
                if stage_data["deal_count"] > 0:
                    if stage_data["avg_probability"] < 30:
                        recommendations.append(f"Low probability deals in {stage_name} - focus on qualification")
                    elif stage_data["deal_count"] > 10:
                        recommendations.append(f"High deal volume in {stage_name} - consider automation")
            
            # Overall recommendations
            total_deals = sum([stage["deal_count"] for stage in stage_analysis.values()])
            if total_deals < 5:
                recommendations.append("Low pipeline volume - focus on lead generation")
            elif total_deals > 50:
                recommendations.append("High pipeline volume - optimize conversion rates")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate pipeline recommendations: {e}")
            return ["Unable to generate recommendations"]
