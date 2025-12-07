from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from backend.core.cache.redis_manager import RedisManager
from backend.core.messaging.kafka_manager import KafkaManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep, SalesAnalytics
)

logger = logging.getLogger(__name__)

class PricingStrategy(BaseModel):
    strategy_id: str
    name: str
    description: str
    pricing_model: str  # cost_plus, value_based, competitive, dynamic
    base_price: float
    min_price: float
    max_price: float
    target_margin: float
    elasticity_factor: float = 1.0
    is_active: bool = True
    created_at: datetime

class PricingRecommendation(BaseModel):
    recommendation_id: str
    product_id: str
    current_price: float
    recommended_price: float
    confidence_score: float
    reasoning: List[str]
    market_factors: Dict[str, Any]
    competitor_analysis: Dict[str, Any]
    demand_forecast: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    created_at: datetime

class CompetitorPricing(BaseModel):
    competitor_id: str
    competitor_name: str
    product_name: str
    price: float
    currency: str
    last_updated: datetime
    price_trend: str  # increasing, decreasing, stable
    market_share: float = 0.0

class MarketCondition(BaseModel):
    market_id: str
    market_name: str
    demand_level: str  # high, medium, low
    supply_level: str  # high, medium, low
    seasonality_factor: float = 1.0
    economic_indicator: str  # growth, recession, stable
    inflation_rate: float = 0.0
    last_updated: datetime

class DynamicPricingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize dynamic pricing service"""
        if self._initialized:
            return
        
        try:
            from backend.core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Dynamic pricing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dynamic pricing service: {e}")
            raise
        
        # Pricing strategies
        self.pricing_strategies = {
            "cost_plus": {
                "name": "Cost-Plus Pricing",
                "description": "Add markup to cost of goods",
                "base_margin": 0.30,
                "flexibility": "low"
            },
            "value_based": {
                "name": "Value-Based Pricing",
                "description": "Price based on customer perceived value",
                "base_margin": 0.50,
                "flexibility": "high"
            },
            "competitive": {
                "name": "Competitive Pricing",
                "description": "Price relative to competitors",
                "base_margin": 0.25,
                "flexibility": "medium"
            },
            "dynamic": {
                "name": "Dynamic Pricing",
                "description": "Real-time price adjustments",
                "base_margin": 0.35,
                "flexibility": "very_high"
            }
        }
    
    async def generate_pricing_recommendation(self, product_id: str, market_data: Dict[str, Any]) -> PricingRecommendation:
        """Generate dynamic pricing recommendation"""
        async with get_eric_database() as session:
            try:
                # Get current product data
                current_price = market_data.get("current_price", 100.0)
                
                # Analyze market conditions
                market_conditions = await self._analyze_market_conditions(market_data)
                
                # Analyze competitor pricing
                competitor_analysis = await self._analyze_competitor_pricing(product_id, market_data)
                
                # Forecast demand
                demand_forecast = await self._forecast_demand(product_id, market_data)
                
                # Calculate optimal price
                recommended_price = await self._calculate_optimal_price(
                    current_price,
                    market_conditions,
                    competitor_analysis,
                    demand_forecast
                )
                
                # Assess risks
                risk_assessment = await self._assess_pricing_risks(recommended_price, market_data)
                
                # Generate reasoning
                reasoning = await self._generate_pricing_reasoning(
                    current_price,
                    recommended_price,
                    market_conditions,
                    competitor_analysis,
                    demand_forecast
                )
                
                # Calculate confidence score
                confidence_score = await self._calculate_confidence_score(
                    market_conditions,
                    competitor_analysis,
                    demand_forecast
                )
                
                recommendation = PricingRecommendation(
                    recommendation_id=f"rec_{datetime.utcnow().timestamp()}",
                    product_id=product_id,
                    current_price=current_price,
                    recommended_price=recommended_price,
                    confidence_score=confidence_score,
                    reasoning=reasoning,
                    market_factors=market_conditions,
                    competitor_analysis=competitor_analysis,
                    demand_forecast=demand_forecast,
                    risk_assessment=risk_assessment,
                    created_at=datetime.utcnow()
                )
                
                # Cache recommendation
                await self.redis_manager.set_cache(
                    f"pricing_recommendation_{product_id}",
                    recommendation.dict(),
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "dynamic_pricing.recommendation_generated",
                    {
                        "product_id": product_id,
                        "current_price": current_price,
                        "recommended_price": recommended_price,
                        "confidence_score": confidence_score,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated pricing recommendation for product {product_id}")
                return recommendation
                
            except Exception as e:
                logger.error(f"Failed to generate pricing recommendation: {e}")
                raise
    
    async def analyze_competitor_pricing(self, product_id: str, market_data: Dict[str, Any]) -> List[CompetitorPricing]:
        """Analyze competitor pricing for a product"""
        try:
            # Get competitor data
            competitors = market_data.get("competitors", [])
            
            competitor_pricing = []
            for competitor in competitors:
                # Analyze price trends
                price_trend = await self._analyze_price_trend(competitor.get("price_history", []))
                
                # Calculate market share
                market_share = await self._calculate_market_share(competitor, competitors)
                
                comp_pricing = CompetitorPricing(
                    competitor_id=competitor["id"],
                    competitor_name=competitor["name"],
                    product_name=competitor["product_name"],
                    price=competitor["price"],
                    currency=competitor.get("currency", "USD"),
                    last_updated=datetime.fromisoformat(competitor["last_updated"]),
                    price_trend=price_trend,
                    market_share=market_share
                )
                competitor_pricing.append(comp_pricing)
            
            logger.info(f"Analyzed pricing for {len(competitor_pricing)} competitors")
            return competitor_pricing
            
        except Exception as e:
            logger.error(f"Failed to analyze competitor pricing: {e}")
            raise
    
    async def create_pricing_strategy(self, strategy_data: Dict[str, Any]) -> PricingStrategy:
        """Create a new pricing strategy"""
        try:
            strategy_id = f"strategy_{datetime.utcnow().timestamp()}"
            
            strategy = PricingStrategy(
                strategy_id=strategy_id,
                name=strategy_data["name"],
                description=strategy_data["description"],
                pricing_model=strategy_data["pricing_model"],
                base_price=strategy_data["base_price"],
                min_price=strategy_data["min_price"],
                max_price=strategy_data["max_price"],
                target_margin=strategy_data["target_margin"],
                elasticity_factor=strategy_data.get("elasticity_factor", 1.0),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Cache strategy
            await self.redis_manager.set_cache(
                f"pricing_strategy_{strategy_id}",
                strategy.dict(),
                expire=86400  # 24 hours
            )
            
            logger.info(f"Created pricing strategy {strategy_id}")
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to create pricing strategy: {e}")
            raise
    
    async def get_pricing_analytics(self, product_id: str = None, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics for pricing performance"""
        try:
            # Query actual pricing data from database
            from ..models import Deal, SalesActivity, CustomerProfile
            
            # Calculate date range
            end_date = datetime.now()
            if date_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif date_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get deals in the date range
            deals_query = db.query(Deal).filter(
                and_(
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
            
            if product_id:
                deals_query = deals_query.filter(Deal.product_id == product_id)
            
            deals = deals_query.all()
            
            # Get pricing activities
            pricing_activities = db.query(SalesActivity).filter(
                and_(
                    SalesActivity.activity_type == "pricing_recommendation",
                    SalesActivity.created_at >= start_date,
                    SalesActivity.created_at <= end_date
                )
            ).all()
            
            # Calculate analytics
            total_recommendations = len(pricing_activities)
            recommendations_followed = len([a for a in pricing_activities if a.metadata.get("followed", False)])
            success_rate = recommendations_followed / total_recommendations if total_recommendations > 0 else 0
            
            # Calculate price changes
            price_changes = []
            for activity in pricing_activities:
                metadata = activity.metadata or {}
                if "price_change_percent" in metadata:
                    price_changes.append(metadata["price_change_percent"])
            
            average_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
            
            # Calculate revenue impact
            total_revenue = sum(d.value for d in deals if d.status == "closed_won")
            avg_deal_value = total_revenue / len(deals) if deals else 0
            
            # Calculate seasonal patterns
            seasonal_data = {}
            for deal in deals:
                quarter = f"q{(deal.created_at.month - 1) // 3 + 1}"
                if quarter not in seasonal_data:
                    seasonal_data[quarter] = {"deals": [], "total_value": 0}
                seasonal_data[quarter]["deals"].append(deal)
                seasonal_data[quarter]["total_value"] += deal.value
            
            seasonal_patterns = {}
            for quarter, data in seasonal_data.items():
                avg_value = data["total_value"] / len(data["deals"]) if data["deals"] else 0
                seasonal_patterns[quarter] = {
                    "demand": "high" if len(data["deals"]) > len(deals) / 4 else "medium",
                    "price_factor": avg_value / avg_deal_value if avg_deal_value > 0 else 1.0
                }
            
            # Get top performing strategies
            strategy_performance = {}
            for activity in pricing_activities:
                metadata = activity.metadata or {}
                strategy = metadata.get("strategy", "unknown")
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {"count": 0, "successful": 0, "revenue": 0}
                
                strategy_performance[strategy]["count"] += 1
                if metadata.get("followed", False):
                    strategy_performance[strategy]["successful"] += 1
                    strategy_performance[strategy]["revenue"] += metadata.get("revenue_impact", 0)
            
            top_performing_strategies = []
            for strategy, data in strategy_performance.items():
                if data["count"] > 0:
                    success_rate = data["successful"] / data["count"]
                    avg_revenue_impact = data["revenue"] / data["successful"] if data["successful"] > 0 else 0
                    top_performing_strategies.append({
                        "strategy": strategy,
                        "success_rate": success_rate,
                        "revenue_impact": avg_revenue_impact
                    })
            
            # Sort by success rate
            top_performing_strategies.sort(key=lambda x: x["success_rate"], reverse=True)
            
            analytics = {
                "total_recommendations": total_recommendations,
                "recommendations_followed": recommendations_followed,
                "success_rate": success_rate,
                "average_price_change": average_price_change,
                "revenue_impact": (total_revenue / len(deals) - avg_deal_value) / avg_deal_value if avg_deal_value > 0 else 0,
                "profit_impact": average_price_change * 0.8,  # Estimate profit impact
                "price_elasticity": -1.2,  # Would calculate from historical data
                "market_share_change": 0.05,  # Would calculate from market data
                "competitor_response_rate": 0.60,  # Would calculate from competitor analysis
                "seasonal_patterns": seasonal_patterns,
                "top_performing_strategies": top_performing_strategies[:3]  # Top 3
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get pricing analytics: {e}")
            raise
    
    async def _analyze_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            conditions = {
                "demand_level": market_data.get("demand_level", "medium"),
                "supply_level": market_data.get("supply_level", "medium"),
                "seasonality_factor": market_data.get("seasonality_factor", 1.0),
                "economic_indicator": market_data.get("economic_indicator", "stable"),
                "inflation_rate": market_data.get("inflation_rate", 0.02),
                "market_volatility": market_data.get("market_volatility", 0.1),
                "customer_sentiment": market_data.get("customer_sentiment", "neutral")
            }
            
            return conditions
            
        except Exception as e:
            logger.error(f"Failed to analyze market conditions: {e}")
            return {}
    
    async def _analyze_competitor_pricing(self, product_id: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor pricing"""
        try:
            competitors = market_data.get("competitors", [])
            
            if not competitors:
                return {"average_price": 0, "price_range": 0, "market_position": "unknown"}
            
            prices = [comp["price"] for comp in competitors]
            average_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            current_price = market_data.get("current_price", 100.0)
            
            # Determine market position
            if current_price < min_price:
                market_position = "lowest"
            elif current_price > max_price:
                market_position = "highest"
            else:
                market_position = "competitive"
            
            return {
                "average_price": average_price,
                "min_price": min_price,
                "max_price": max_price,
                "price_range": max_price - min_price,
                "market_position": market_position,
                "competitor_count": len(competitors)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze competitor pricing: {e}")
            return {}
    
    async def _forecast_demand(self, product_id: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast demand for the product"""
        try:
            # Query historical demand data from database
            from ..models import Deal, SalesActivity, CustomerProfile
            
            # Get historical deals for demand analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 year of data
            
            deals_query = db.query(Deal).filter(
                and_(
                    Deal.created_at >= start_date,
                    Deal.created_at <= end_date
                )
            )
            
            if product_id:
                deals_query = deals_query.filter(Deal.product_id == product_id)
            
            deals = deals_query.all()
            
            if not deals:
                # Fallback to market data
                base_demand = market_data.get("base_demand", 1000)
                seasonality = market_data.get("seasonality_factor", 1.0)
                trend_factor = market_data.get("trend_factor", 1.0)
                
                forecasted_demand = base_demand * seasonality * trend_factor
                
                return {
                    "forecasted_demand": forecasted_demand,
                    "demand_trend": "increasing" if trend_factor > 1 else "decreasing",
                    "confidence_level": 0.70,
                    "seasonality_impact": seasonality
                }
            
            # Calculate demand patterns
            monthly_demand = {}
            for deal in deals:
                month_key = f"{deal.created_at.year}-{deal.created_at.month:02d}"
                if month_key not in monthly_demand:
                    monthly_demand[month_key] = 0
                monthly_demand[month_key] += 1
            
            # Calculate trend
            sorted_months = sorted(monthly_demand.keys())
            if len(sorted_months) >= 2:
                recent_demand = sum(monthly_demand[month] for month in sorted_months[-3:])  # Last 3 months
                earlier_demand = sum(monthly_demand[month] for month in sorted_months[:3])  # First 3 months
                trend_factor = recent_demand / earlier_demand if earlier_demand > 0 else 1.0
            else:
                trend_factor = 1.0
            
            # Calculate seasonality
            current_month = datetime.now().month
            seasonal_demand = {}
            for month_key, demand in monthly_demand.items():
                month = int(month_key.split('-')[1])
                if month not in seasonal_demand:
                    seasonal_demand[month] = []
                seasonal_demand[month].append(demand)
            
            # Calculate average demand by month
            avg_monthly_demand = {}
            for month, demands in seasonal_demand.items():
                avg_monthly_demand[month] = sum(demands) / len(demands)
            
            # Calculate overall average
            overall_avg = sum(avg_monthly_demand.values()) / len(avg_monthly_demand) if avg_monthly_demand else 1
            
            # Calculate seasonality factor for current month
            seasonality = avg_monthly_demand.get(current_month, overall_avg) / overall_avg if overall_avg > 0 else 1.0
            
            # Calculate base demand (average monthly demand)
            base_demand = overall_avg
            
            # Forecast demand
            forecasted_demand = base_demand * seasonality * trend_factor
            
            # Calculate confidence level based on data quality
            confidence_factors = []
            if len(deals) >= 50:
                confidence_factors.append(0.9)  # Good data volume
            elif len(deals) >= 20:
                confidence_factors.append(0.7)  # Moderate data volume
            else:
                confidence_factors.append(0.5)  # Low data volume
            
            if len(monthly_demand) >= 6:
                confidence_factors.append(0.8)  # Good time series
            else:
                confidence_factors.append(0.6)  # Limited time series
            
            confidence_level = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.7
            
            return {
                "forecasted_demand": round(forecasted_demand, 2),
                "demand_trend": "increasing" if trend_factor > 1.05 else "decreasing" if trend_factor < 0.95 else "stable",
                "confidence_level": round(confidence_level, 2),
                "seasonality_impact": round(seasonality, 2),
                "trend_factor": round(trend_factor, 2),
                "base_demand": round(base_demand, 2),
                "data_points": len(deals),
                "time_period_months": len(monthly_demand)
            }
            
        except Exception as e:
            logger.error(f"Failed to forecast demand: {e}")
            return {}
    
    async def _calculate_optimal_price(self, current_price: float, market_conditions: Dict[str, Any], competitor_analysis: Dict[str, Any], demand_forecast: Dict[str, Any]) -> float:
        """Calculate optimal price based on various factors"""
        try:
            base_price = current_price
            
            # Market condition adjustments
            demand_level = market_conditions.get("demand_level", "medium")
            if demand_level == "high":
                base_price *= 1.1
            elif demand_level == "low":
                base_price *= 0.9
            
            # Competitor adjustments
            market_position = competitor_analysis.get("market_position", "competitive")
            if market_position == "highest":
                base_price *= 0.95  # Reduce if highest
            elif market_position == "lowest":
                base_price *= 1.05  # Increase if lowest
            
            # Demand forecast adjustments
            demand_trend = demand_forecast.get("demand_trend", "stable")
            if demand_trend == "increasing":
                base_price *= 1.05
            elif demand_trend == "decreasing":
                base_price *= 0.95
            
            # Seasonality adjustments
            seasonality = market_conditions.get("seasonality_factor", 1.0)
            base_price *= seasonality
            
            # Inflation adjustment
            inflation_rate = market_conditions.get("inflation_rate", 0.02)
            base_price *= (1 + inflation_rate)
            
            return round(base_price, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal price: {e}")
            return current_price
    
    async def _assess_pricing_risks(self, recommended_price: float, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks associated with pricing recommendation"""
        try:
            current_price = market_data.get("current_price", 100.0)
            price_change = (recommended_price - current_price) / current_price
            
            risks = {
                "price_change_percentage": price_change,
                "risk_level": "low",
                "potential_risks": [],
                "mitigation_strategies": []
            }
            
            # Assess risk level
            if abs(price_change) > 0.25:  # More than 25% change
                risks["risk_level"] = "high"
                risks["potential_risks"].append("Significant price change may impact customer perception")
                risks["mitigation_strategies"].append("Implement gradual price changes")
            elif abs(price_change) > 0.10:  # More than 10% change
                risks["risk_level"] = "medium"
                risks["potential_risks"].append("Moderate price change may affect demand")
                risks["mitigation_strategies"].append("Monitor customer response closely")
            else:
                risks["risk_level"] = "low"
                risks["potential_risks"].append("Minimal risk with small price change")
                risks["mitigation_strategies"].append("Proceed with confidence")
            
            return risks
            
        except Exception as e:
            logger.error(f"Failed to assess pricing risks: {e}")
            return {"risk_level": "unknown", "potential_risks": [], "mitigation_strategies": []}
    
    async def _generate_pricing_reasoning(self, current_price: float, recommended_price: float, market_conditions: Dict[str, Any], competitor_analysis: Dict[str, Any], demand_forecast: Dict[str, Any]) -> List[str]:
        """Generate reasoning for pricing recommendation"""
        try:
            reasoning = []
            price_change = (recommended_price - current_price) / current_price
            
            # Market condition reasoning
            demand_level = market_conditions.get("demand_level", "medium")
            if demand_level == "high":
                reasoning.append("High market demand supports price increase")
            elif demand_level == "low":
                reasoning.append("Low market demand suggests price reduction")
            
            # Competitor reasoning
            market_position = competitor_analysis.get("market_position", "competitive")
            if market_position == "highest":
                reasoning.append("Currently highest priced competitor - consider reduction")
            elif market_position == "lowest":
                reasoning.append("Currently lowest priced competitor - room for increase")
            
            # Demand forecast reasoning
            demand_trend = demand_forecast.get("demand_trend", "stable")
            if demand_trend == "increasing":
                reasoning.append("Increasing demand trend supports price optimization")
            elif demand_trend == "decreasing":
                reasoning.append("Decreasing demand trend requires competitive pricing")
            
            # Seasonality reasoning
            seasonality = market_conditions.get("seasonality_factor", 1.0)
            if seasonality > 1.1:
                reasoning.append("Seasonal demand peak supports higher pricing")
            elif seasonality < 0.9:
                reasoning.append("Seasonal demand low suggests promotional pricing")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Failed to generate pricing reasoning: {e}")
            return ["Pricing recommendation based on market analysis"]
    
    async def _calculate_confidence_score(self, market_conditions: Dict[str, Any], competitor_analysis: Dict[str, Any], demand_forecast: Dict[str, Any]) -> float:
        """Calculate confidence score for pricing recommendation"""
        try:
            confidence = 0.5  # Base confidence
            
            # Market conditions confidence
            if market_conditions.get("demand_level") and market_conditions.get("supply_level"):
                confidence += 0.1
            
            # Competitor analysis confidence
            if competitor_analysis.get("competitor_count", 0) > 0:
                confidence += 0.2
            
            # Demand forecast confidence
            if demand_forecast.get("confidence_level"):
                confidence += demand_forecast["confidence_level"] * 0.2
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.5
    
    async def _analyze_price_trend(self, price_history: List[Dict[str, Any]]) -> str:
        """Analyze price trend from historical data"""
        try:
            if len(price_history) < 2:
                return "stable"
            
            prices = [entry["price"] for entry in price_history]
            if prices[-1] > prices[0] * 1.05:
                return "increasing"
            elif prices[-1] < prices[0] * 0.95:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Failed to analyze price trend: {e}")
            return "stable"
    
    async def _calculate_market_share(self, competitor: Dict[str, Any], all_competitors: List[Dict[str, Any]]) -> float:
        """Calculate market share for a competitor"""
        try:
            total_revenue = sum(comp.get("revenue", 0) for comp in all_competitors)
            if total_revenue > 0:
                return competitor.get("revenue", 0) / total_revenue
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate market share: {e}")
            return 0.0
