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
    Lead, Deal, SalesActivity, SalesCampaign, SalesAnalytics,
    SalesForecast, SalesTeam, SalesRep, CustomerProfile
)

logger = logging.getLogger(__name__)

class ProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    category: str
    confidence_score: float
    reasoning: List[str]
    pricing_tier: str
    estimated_value: float
    upsell_potential: float

class PricingRecommendation(BaseModel):
    base_price: float
    recommended_price: float
    discount_percentage: Optional[float]
    pricing_strategy: str
    reasoning: List[str]
    market_comparison: Dict[str, Any]
    profit_margin: float

class SalesStrategyRecommendation(BaseModel):
    strategy_type: str  # "approach", "timing", "channel", "content"
    recommendation: str
    confidence: float
    reasoning: List[str]
    expected_outcome: str
    implementation_steps: List[str]

class CustomerProfile(BaseModel):
    customer_id: int
    segment: str
    lifetime_value: float
    purchase_history: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    risk_level: str
    engagement_score: float

class PersonalizedRecommendationsService:
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
        """Initialize personalized recommendations service"""
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
            logger.info("Personalized recommendations service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize personalized recommendations service: {e}")
            raise
        
    async def get_product_recommendations(self, customer_id: int, context: str = "general") -> List[ProductRecommendation]:
        """Generate personalized product recommendations for a customer"""
        async with get_eric_database() as session:
            try:
                # Get customer profile and purchase history
                customer_profile = await self._get_customer_profile(session, customer_id)
                
                # Get customer's deals and activities
                deals = await session.execute(
                    select(Deal).where(
                        and_(
                            Deal.customer_id == customer_id,
                            Deal.status == "closed"
                        )
                    )
                )
                deals = deals.scalars().all()
                
                # Get customer activities
                activities = await session.execute(
                    select(SalesActivity).where(
                        and_(
                            SalesActivity.customer_id == customer_id,
                            SalesActivity.created_at >= datetime.utcnow() - timedelta(days=180)
                        )
                    )
                )
                activities = activities.scalars().all()
                
                # Analyze purchase patterns
                purchase_patterns = self._analyze_purchase_patterns(deals)
                
                # Generate product recommendations based on patterns
                recommendations = []
                
                # Recommendation 1: Based on purchase history
                if deals:
                    last_deal = max(deals, key=lambda d: d.closed_at)
                    if last_deal.value and last_deal.value > 5000:
                        # High-value customer - recommend premium products
                        recommendations.append(ProductRecommendation(
                            product_id="premium_suite",
                            product_name="Premium Business Suite",
                            category="enterprise",
                            confidence_score=0.85,
                            reasoning=[
                                "High-value customer with premium purchase history",
                                "Shows enterprise-level buying behavior",
                                "Strong engagement with premium features"
                            ],
                            pricing_tier="enterprise",
                            estimated_value=15000.0,
                            upsell_potential=0.75
                        ))
                    elif last_deal.value and last_deal.value > 1000:
                        # Mid-value customer - recommend growth products
                        recommendations.append(ProductRecommendation(
                            product_id="growth_package",
                            product_name="Growth Acceleration Package",
                            category="business",
                            confidence_score=0.78,
                            reasoning=[
                                "Mid-value customer with growth potential",
                                "Consistent purchase behavior",
                                "Shows interest in scaling solutions"
                            ],
                            pricing_tier="business",
                            estimated_value=5000.0,
                            upsell_potential=0.65
                        ))
                
                # Recommendation 2: Based on engagement patterns
                engagement_score = self._calculate_engagement_score(activities)
                if engagement_score > 0.7:
                    recommendations.append(ProductRecommendation(
                        product_id="advanced_analytics",
                        product_name="Advanced Analytics Platform",
                        category="analytics",
                        confidence_score=0.72,
                        reasoning=[
                            "High engagement with current products",
                            "Shows interest in data-driven insights",
                            "Consistent usage patterns"
                        ],
                        pricing_tier="professional",
                        estimated_value=3000.0,
                        upsell_potential=0.6
                    ))
                
                # Recommendation 3: Based on customer segment
                if customer_profile.segment == "enterprise":
                    recommendations.append(ProductRecommendation(
                        product_id="enterprise_integration",
                        product_name="Enterprise Integration Hub",
                        category="integration",
                        confidence_score=0.8,
                        reasoning=[
                            "Enterprise customer segment",
                            "Likely needs integration capabilities",
                            "High lifetime value potential"
                        ],
                        pricing_tier="enterprise",
                        estimated_value=25000.0,
                        upsell_potential=0.8
                    ))
                elif customer_profile.segment == "startup":
                    recommendations.append(ProductRecommendation(
                        product_id="startup_essentials",
                        product_name="Startup Essentials Bundle",
                        category="starter",
                        confidence_score=0.75,
                        reasoning=[
                            "Startup customer segment",
                            "Cost-conscious with growth focus",
                            "Needs foundational tools"
                        ],
                        pricing_tier="starter",
                        estimated_value=1500.0,
                        upsell_potential=0.7
                    ))
                
                # Recommendation 4: Based on context
                if context == "renewal":
                    # Recommend upgrades or add-ons for renewing customers
                    recommendations.append(ProductRecommendation(
                        product_id="premium_support",
                        product_name="Premium Support Package",
                        category="support",
                        confidence_score=0.68,
                        reasoning=[
                            "Renewal context - opportunity for value addition",
                            "Enhances customer experience",
                            "Increases retention and satisfaction"
                        ],
                        pricing_tier="addon",
                        estimated_value=2000.0,
                        upsell_potential=0.55
                    ))
                
                # Sort by confidence score
                recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
                
                # Cache recommendations
                await self.redis_manager.set_cache(
                    f"product_recommendations_{customer_id}_{context}",
                    [rec.dict() for rec in recommendations],
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "personalized_recommendations.products_generated",
                    {
                        "customer_id": customer_id,
                        "context": context,
                        "recommendations_count": len(recommendations),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated {len(recommendations)} product recommendations for customer {customer_id}")
                return recommendations
                
            except Exception as e:
                logger.error(f"Failed to generate product recommendations: {e}")
                raise
    
    async def get_pricing_recommendations(self, customer_id: int, product_id: str) -> PricingRecommendation:
        """Generate personalized pricing recommendations for a customer"""
        async with get_eric_database() as session:
            try:
                # Get customer profile
                customer_profile = await self._get_customer_profile(session, customer_id)
                
                # Get customer's purchase history
                deals = await session.execute(
                    select(Deal).where(
                        and_(
                            Deal.customer_id == customer_id,
                            Deal.status == "closed"
                        )
                    )
                )
                deals = deals.scalars().all()
                
                # Base pricing logic (in real implementation, this would come from product catalog)
                base_prices = {
                    "premium_suite": 15000.0,
                    "growth_package": 5000.0,
                    "advanced_analytics": 3000.0,
                    "enterprise_integration": 25000.0,
                    "startup_essentials": 1500.0,
                    "premium_support": 2000.0
                }
                
                base_price = base_prices.get(product_id, 5000.0)
                
                # Calculate recommended price based on customer characteristics
                recommended_price = base_price
                discount_percentage = None
                reasoning = []
                
                # Factor 1: Customer segment
                if customer_profile.segment == "enterprise":
                    # Enterprise customers typically pay full price
                    reasoning.append("Enterprise customer - premium pricing appropriate")
                elif customer_profile.segment == "startup":
                    # Startups might get discounts
                    discount_percentage = 15.0
                    recommended_price = base_price * (1 - discount_percentage / 100)
                    reasoning.append("Startup customer - 15% discount applied")
                
                # Factor 2: Purchase history
                if deals:
                    total_spent = sum(deal.value for deal in deals if deal.value)
                    if total_spent > 50000:
                        # High-value customer - consider loyalty discount
                        discount_percentage = 10.0
                        recommended_price = base_price * (1 - discount_percentage / 100)
                        reasoning.append("High-value customer - 10% loyalty discount")
                    elif total_spent < 5000:
                        # New customer - introductory pricing
                        discount_percentage = 20.0
                        recommended_price = base_price * (1 - discount_percentage / 100)
                        reasoning.append("New customer - 20% introductory discount")
                
                # Factor 3: Risk level
                if customer_profile.risk_level == "high":
                    # High-risk customers might need incentives
                    if not discount_percentage:
                        discount_percentage = 25.0
                        recommended_price = base_price * (1 - discount_percentage / 100)
                        reasoning.append("High-risk customer - 25% risk mitigation discount")
                
                # Factor 4: Engagement score
                if customer_profile.engagement_score > 0.8:
                    # Highly engaged customers might pay premium
                    if not discount_percentage:
                        recommended_price = base_price * 1.1  # 10% premium
                        reasoning.append("Highly engaged customer - 10% engagement premium")
                
                # Determine pricing strategy
                if discount_percentage:
                    if discount_percentage > 20:
                        pricing_strategy = "aggressive_discount"
                    elif discount_percentage > 10:
                        pricing_strategy = "moderate_discount"
                    else:
                        pricing_strategy = "light_discount"
                elif recommended_price > base_price:
                    pricing_strategy = "premium_pricing"
                else:
                    pricing_strategy = "standard_pricing"
                
                # Calculate profit margin (simplified)
                cost_of_goods = base_price * 0.4  # Assume 40% COGS
                profit_margin = ((recommended_price - cost_of_goods) / recommended_price) * 100
                
                # Market comparison based on historical data
                # Query similar deals to understand market positioning
                similar_deals = await session.execute(
                    select(Deal).where(
                        and_(
                            Deal.product_id == product_id,
                            Deal.status == "closed_won",
                            Deal.created_at >= datetime.utcnow() - timedelta(days=365)
                        )
                    )
                )
                similar_deals = similar_deals.scalars().all()
                
                if similar_deals:
                    competitor_prices = [deal.value for deal in similar_deals if deal.value]
                    avg_competitor_price = sum(competitor_prices) / len(competitor_prices) if competitor_prices else base_price
                    market_position = "competitive" if recommended_price <= avg_competitor_price else "premium"
                else:
                    avg_competitor_price = base_price * 0.95  # Default estimate
                    market_position = "competitive" if recommended_price <= base_price else "premium"
                
                # Calculate price elasticity based on customer segment
                if customer_profile.segment == "enterprise":
                    price_elasticity = "low"  # Enterprise customers less price sensitive
                elif customer_profile.segment == "startup":
                    price_elasticity = "high"  # Startups more price sensitive
                else:
                    price_elasticity = "moderate"
                
                market_comparison = {
                    "competitor_average": avg_competitor_price,
                    "market_position": market_position,
                    "price_elasticity": price_elasticity
                }
                
                recommendation = PricingRecommendation(
                    base_price=base_price,
                    recommended_price=recommended_price,
                    discount_percentage=discount_percentage,
                    pricing_strategy=pricing_strategy,
                    reasoning=reasoning,
                    market_comparison=market_comparison,
                    profit_margin=profit_margin
                )
                
                # Cache recommendation
                await self.redis_manager.set_cache(
                    f"pricing_recommendation_{customer_id}_{product_id}",
                    recommendation.dict(),
                    expire=1800  # 30 minutes
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "personalized_recommendations.pricing_generated",
                    {
                        "customer_id": customer_id,
                        "product_id": product_id,
                        "recommended_price": recommended_price,
                        "pricing_strategy": pricing_strategy,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated pricing recommendation for customer {customer_id}, product {product_id}")
                return recommendation
                
            except Exception as e:
                logger.error(f"Failed to generate pricing recommendation: {e}")
                raise
    
    async def get_sales_strategy_recommendations(self, customer_id: int, deal_id: Optional[int] = None) -> List[SalesStrategyRecommendation]:
        """Generate personalized sales strategy recommendations"""
        async with get_eric_database() as session:
            try:
                # Get customer profile
                customer_profile = await self._get_customer_profile(session, customer_id)
                
                # Get customer activities
                activities = await session.execute(
                    select(SalesActivity).where(
                        and_(
                            SalesActivity.customer_id == customer_id,
                            SalesActivity.created_at >= datetime.utcnow() - timedelta(days=90)
                        )
                    )
                )
                activities = activities.scalars().all()
                
                recommendations = []
                
                # Strategy 1: Approach recommendation
                if customer_profile.segment == "enterprise":
                    recommendations.append(SalesStrategyRecommendation(
                        strategy_type="approach",
                        recommendation="Executive-level consultative approach",
                        confidence=0.85,
                        reasoning=[
                            "Enterprise customer segment",
                            "High lifetime value",
                            "Complex decision-making process"
                        ],
                        expected_outcome="Higher close rate and deal value",
                        implementation_steps=[
                            "Schedule executive briefing",
                            "Prepare ROI analysis",
                            "Involve technical stakeholders",
                            "Present strategic value proposition"
                        ]
                    ))
                elif customer_profile.segment == "startup":
                    recommendations.append(SalesStrategyRecommendation(
                        strategy_type="approach",
                        recommendation="Agile, solution-focused approach",
                        confidence=0.78,
                        reasoning=[
                            "Startup customer segment",
                            "Fast decision-making",
                            "Cost-conscious with growth focus"
                        ],
                        expected_outcome="Faster sales cycle and adoption",
                        implementation_steps=[
                            "Focus on immediate value delivery",
                            "Provide flexible pricing options",
                            "Emphasize growth potential",
                            "Offer pilot program"
                        ]
                    ))
                
                # Strategy 2: Timing recommendation
                if deal_id:
                    deal = await session.execute(
                        select(Deal).where(Deal.id == deal_id)
                    )
                    deal = deal.scalar_one_or_none()
                    
                    if deal and deal.created_at:
                        days_in_pipeline = (datetime.utcnow() - deal.created_at).days
                        
                        if days_in_pipeline > 30:
                            recommendations.append(SalesStrategyRecommendation(
                                strategy_type="timing",
                                recommendation="Accelerate deal closure with urgency",
                                confidence=0.72,
                                reasoning=[
                                    f"Deal in pipeline for {days_in_pipeline} days",
                                    "Risk of deal stagnation",
                                    "Need for momentum"
                                ],
                                expected_outcome="Faster deal closure",
                                implementation_steps=[
                                    "Set firm closing timeline",
                                    "Create urgency with limited-time offers",
                                    "Schedule executive review",
                                    "Address any remaining objections"
                                ]
                            ))
                
                # Strategy 3: Channel recommendation
                channel_preferences = self._analyze_channel_preferences(activities)
                preferred_channel = max(channel_preferences.items(), key=lambda x: x[1])[0]
                
                recommendations.append(SalesStrategyRecommendation(
                    strategy_type="channel",
                    recommendation=f"Focus on {preferred_channel} communication",
                    confidence=0.68,
                    reasoning=[
                        f"Customer shows preference for {preferred_channel}",
                        "Higher engagement rates on this channel",
                        "Better response times"
                    ],
                    expected_outcome="Improved engagement and response rates",
                    implementation_steps=[
                        f"Prioritize {preferred_channel} outreach",
                        "Optimize messaging for this channel",
                        "Schedule follow-ups accordingly",
                        "Monitor engagement metrics"
                    ]
                ))
                
                # Strategy 4: Content recommendation
                if customer_profile.engagement_score > 0.7:
                    recommendations.append(SalesStrategyRecommendation(
                        strategy_type="content",
                        recommendation="Provide detailed technical content and case studies",
                        confidence=0.75,
                        reasoning=[
                            "High engagement customer",
                            "Shows interest in detailed information",
                            "Technical decision-maker likely"
                        ],
                        expected_outcome="Better understanding and faster decision-making",
                        implementation_steps=[
                            "Share technical specifications",
                            "Provide relevant case studies",
                            "Schedule technical deep-dive sessions",
                            "Offer proof-of-concept"
                        ]
                    ))
                else:
                    recommendations.append(SalesStrategyRecommendation(
                        strategy_type="content",
                        recommendation="Focus on value proposition and ROI",
                        confidence=0.7,
                        reasoning=[
                            "Moderate engagement level",
                            "Needs clear value demonstration",
                            "ROI-focused decision-making"
                        ],
                        expected_outcome="Clearer value understanding",
                        implementation_steps=[
                            "Present ROI calculator",
                            "Share success stories",
                            "Focus on business outcomes",
                            "Provide competitive analysis"
                        ]
                    ))
                
                # Sort by confidence
                recommendations.sort(key=lambda x: x.confidence, reverse=True)
                
                # Cache recommendations
                await self.redis_manager.set_cache(
                    f"sales_strategy_recommendations_{customer_id}",
                    [rec.dict() for rec in recommendations],
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "personalized_recommendations.strategy_generated",
                    {
                        "customer_id": customer_id,
                        "recommendations_count": len(recommendations),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Generated {len(recommendations)} sales strategy recommendations for customer {customer_id}")
                return recommendations
                
            except Exception as e:
                logger.error(f"Failed to generate sales strategy recommendations: {e}")
                raise
    
    async def get_customer_profile(self, customer_id: int) -> CustomerProfile:
        """Get comprehensive customer profile for personalization"""
        async with get_eric_database() as session:
            try:
                return await self._get_customer_profile(session, customer_id)
            except Exception as e:
                logger.error(f"Failed to get customer profile: {e}")
                raise
    
    async def _get_customer_profile(self, session: AsyncSession, customer_id: int) -> CustomerProfile:
        """Internal method to get customer profile"""
        # Get customer deals
        deals = await session.execute(
            select(Deal).where(
                and_(
                    Deal.customer_id == customer_id,
                    Deal.status == "closed"
                )
            )
        )
        deals = deals.scalars().all()
        
        # Get customer activities
        activities = await session.execute(
            select(SalesActivity).where(
                and_(
                    SalesActivity.customer_id == customer_id,
                    SalesActivity.created_at >= datetime.utcnow() - timedelta(days=180)
                )
            )
        )
        activities = activities.scalars().all()
        
        # Calculate customer metrics
        lifetime_value = sum(deal.value for deal in deals if deal.value) if deals else 0
        engagement_score = self._calculate_engagement_score(activities)
        
        # Determine customer segment
        if lifetime_value > 50000:
            segment = "enterprise"
        elif lifetime_value > 10000:
            segment = "business"
        elif lifetime_value > 1000:
            segment = "professional"
        else:
            segment = "startup"
        
        # Determine risk level
        if engagement_score < 0.3:
            risk_level = "high"
        elif engagement_score < 0.6:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Purchase history
        purchase_history = [
            {
                "deal_id": deal.id,
                "value": deal.value,
                "closed_at": deal.closed_at.isoformat(),
                "product": deal.title
            }
            for deal in deals
        ]
        
        # Customer preferences (simplified)
        preferences = {
            "communication_channel": self._get_preferred_channel(activities),
            "response_time": self._calculate_avg_response_time(activities),
            "deal_size_preference": self._analyze_deal_size_preference(deals)
        }
        
        return CustomerProfile(
            customer_id=customer_id,
            segment=segment,
            lifetime_value=lifetime_value,
            purchase_history=purchase_history,
            preferences=preferences,
            risk_level=risk_level,
            engagement_score=engagement_score
        )
    
    def _analyze_purchase_patterns(self, deals: List[Deal]) -> Dict[str, Any]:
        """Analyze customer purchase patterns"""
        if not deals:
            return {}
        
        deal_values = [deal.value for deal in deals if deal.value]
        deal_dates = [deal.closed_at for deal in deals if deal.closed_at]
        
        patterns = {
            "total_deals": len(deals),
            "avg_deal_value": sum(deal_values) / len(deal_values) if deal_values else 0,
            "total_spent": sum(deal_values),
            "deal_frequency": len(deals) / 12 if deal_dates else 0,  # deals per month
            "value_trend": "increasing" if len(deal_values) > 1 and deal_values[-1] > deal_values[0] else "stable"
        }
        
        return patterns
    
    def _calculate_engagement_score(self, activities: List[SalesActivity]) -> float:
        """Calculate customer engagement score"""
        if not activities:
            return 0.0
        
        # Weight different activity types
        activity_weights = {
            "email": 1.0,
            "call": 2.0,
            "meeting": 3.0,
            "demo": 4.0,
            "proposal": 5.0
        }
        
        total_score = 0
        for activity in activities:
            weight = activity_weights.get(activity.type, 1.0)
            total_score += weight
        
        # Normalize to 0-1 scale
        max_possible_score = len(activities) * 5.0  # Assuming max weight is 5
        return min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
    
    def _analyze_channel_preferences(self, activities: List[SalesActivity]) -> Dict[str, int]:
        """Analyze customer channel preferences"""
        channel_counts = defaultdict(int)
        
        for activity in activities:
            channel_counts[activity.type] += 1
        
        return dict(channel_counts)
    
    def _get_preferred_channel(self, activities: List[SalesActivity]) -> str:
        """Get customer's preferred communication channel"""
        channel_preferences = self._analyze_channel_preferences(activities)
        
        if not channel_preferences:
            return "email"  # Default
        
        return max(channel_preferences.items(), key=lambda x: x[1])[0]
    
    def _calculate_avg_response_time(self, activities: List[SalesActivity]) -> float:
        """Calculate average response time from activity data"""
        if not activities:
            return 24.0  # Default fallback
        
        # Calculate time between outreach and response activities
        response_times = []
        outreach_activities = [a for a in activities if a.activity_type in ["email", "call", "meeting"]]
        
        for i, activity in enumerate(outreach_activities):
            if i + 1 < len(activities):
                next_activity = activities[i + 1]
                if next_activity.activity_type in ["email_response", "call_response", "meeting_followup"]:
                    time_diff = (next_activity.created_at - activity.created_at).total_seconds() / 3600  # hours
                    if time_diff > 0 and time_diff < 168:  # Between 0 and 1 week
                        response_times.append(time_diff)
        
        if response_times:
            return sum(response_times) / len(response_times)
        else:
            return 24.0  # Default fallback
    
    def _analyze_deal_size_preference(self, deals: List[Deal]) -> str:
        """Analyze customer's preferred deal size"""
        if not deals:
            return "unknown"
        
        deal_values = [deal.value for deal in deals if deal.value]
        avg_value = sum(deal_values) / len(deal_values)
        
        if avg_value > 10000:
            return "large"
        elif avg_value > 5000:
            return "medium"
        else:
            return "small"
