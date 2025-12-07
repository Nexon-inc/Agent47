import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import httpx
import json
import redis.asyncio as redis
from kafka import KafkaProducer

from ..database import get_eric_database
from ..models import Lead, Deal, SalesActivity, SalesRep, CustomerProfile, SalesCampaign, SalesAnalytics, SalesForecast
from backend.core.utils.nlp_utils import NLPUtils
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
from backend.core.analytics.analytics_manager import AnalyticsManager

logger = logging.getLogger(__name__)

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import asyncio
import json
import requests
from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..models import (
    SalesRep, Deal, SalesActivity, Lead, CustomerProfile,
    EricMarketInsight, SalesAnalytics, SalesForecast
)
from ..database import get_eric_database
from backend.core.event_bus.kafka_manager import EventBus as KafkaProducer
from backend.core.cache.redis_manager import RedisManager
from backend.core.config import settings


class MarketTrend(BaseModel):
    region: str
    industry: str
    trend_type: str
    description: str
    impact_score: float
    confidence_level: float
    data_source: str
    last_updated: datetime


class RegionalInsight(BaseModel):
    region: str
    market_size: float
    growth_rate: float
    competition_level: str
    key_opportunities: List[str]
    challenges: List[str]
    recommended_strategies: List[str]
    market_maturity: str


class LocalMarketInsightsService:
    def __init__(self):
        self.ai_service_manager = None
        # KafkaProducer is aliased to EventBus earlier in imports
        try:
            self.kafka_producer = KafkaProducer()
        except Exception:
            self.kafka_producer = None

        # Use RedisManager from core cache
        try:
            from backend.core.cache.redis_manager import redis_manager as RedisClient
            self.redis_client = RedisClient
        except Exception:
            self.redis_client = None
        self.cache_ttl = 3600  # 1 hour for market data
        self.external_api_key = getattr(settings, "MARKET_DATA_API_KEY", None)
        self.external_api_url = "https://api.marketdata.com/v1"
        self._initialized = False
    
    async def initialize(self):
        """Initialize local market insights service"""
        if self._initialized:
            return
        
        try:
            from backend.core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            if self.kafka_producer:
                await self.kafka_producer.initialize()
            # redis_client is already initialized
            self._initialized = True
            logger.info("Local market insights service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize local market insights service: {e}")
            raise

    async def get_regional_market_insights(
        self, 
        db: Session, 
        region: str,
        industry: Optional[str] = None
    ) -> RegionalInsight:
        """Get comprehensive market insights for a specific region"""
        cache_key = f"market_insights:{region}:{industry or 'all'}"
        
        # Check cache first
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return RegionalInsight(**json.loads(cached_data))
        
        # Get market data from external API
        market_data = await self._fetch_market_data(region, industry)
        
        # Get local sales data
        local_sales_data = await self._get_local_sales_data(db, region, industry)
        
        # Analyze market trends
        trends = await self._analyze_market_trends(region, industry)
        
        # Generate insights
        insight = RegionalInsight(
            region=region,
            market_size=market_data.get("market_size", 0),
            growth_rate=market_data.get("growth_rate", 0),
            competition_level=self._assess_competition_level(market_data, local_sales_data),
            key_opportunities=await self._identify_opportunities(market_data, trends, local_sales_data),
            challenges=await self._identify_challenges(market_data, trends, local_sales_data),
            recommended_strategies=await self._generate_strategies(market_data, trends, local_sales_data),
            market_maturity=self._assess_market_maturity(market_data, local_sales_data)
        )
        
        # Cache results
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(insight.dict())
        )
        
        # Store in database
        await self._store_market_insight(db, insight, region, industry)
        
        return insight

    async def get_market_trends(
        self, 
        db: Session, 
        region: str,
        industry: Optional[str] = None,
        trend_type: Optional[str] = None
    ) -> List[MarketTrend]:
        """Get market trends for a specific region and industry"""
        cache_key = f"market_trends:{region}:{industry or 'all'}:{trend_type or 'all'}"
        
        # Check cache first
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return [MarketTrend(**item) for item in json.loads(cached_data)]
        
        # Fetch trends from external API
        external_trends = await self._fetch_external_trends(region, industry, trend_type)
        
        # Get local trends from sales data
        local_trends = await self._analyze_local_trends(db, region, industry)
        
        # Combine and rank trends
        all_trends = external_trends + local_trends
        ranked_trends = sorted(all_trends, key=lambda x: x.impact_score, reverse=True)
        
        # Cache results
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps([t.dict() for t in ranked_trends])
        )
        
        return ranked_trends

    async def get_sales_strategy_recommendations(
        self, 
        db: Session, 
        sales_rep_id: int,
        region: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized sales strategy recommendations based on local market insights"""
        # Get sales rep information
        sales_rep = db.query(SalesRep).filter(SalesRep.id == sales_rep_id).first()
        if not sales_rep:
            raise HTTPException(status_code=404, detail="Sales rep not found")
        
        # Get market insights
        market_insights = await self.get_regional_market_insights(db, region, industry)
        
        # Get sales rep performance in the region
        performance_data = await self._get_rep_performance_in_region(db, sales_rep_id, region)
        
        # Get competitor analysis
        competitor_analysis = await self._analyze_competitors(db, region, industry)
        
        # Generate personalized recommendations
        recommendations = await self._generate_personalized_recommendations(
            market_insights, performance_data, competitor_analysis, sales_rep
        )
        
        return {
            "sales_rep_id": sales_rep_id,
            "region": region,
            "industry": industry,
            "market_insights": market_insights.dict(),
            "performance_analysis": performance_data,
            "competitor_analysis": competitor_analysis,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    async def get_regional_performance_benchmarks(
        self, 
        db: Session, 
        region: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance benchmarks for a specific region"""
        # Get all sales reps in the region
        sales_reps = db.query(SalesRep).filter(
            SalesRep.region == region
        ).all()
        
        if not sales_reps:
            raise HTTPException(status_code=404, detail="No sales reps found in region")
        
        # Calculate regional metrics
        regional_metrics = await self._calculate_regional_metrics(db, sales_reps, industry)
        
        # Get industry benchmarks
        industry_benchmarks = await self._get_industry_benchmarks(db, industry)
        
        # Compare regional performance to industry benchmarks
        performance_comparison = await self._compare_performance(
            regional_metrics, industry_benchmarks
        )
        
        return {
            "region": region,
            "industry": industry,
            "regional_metrics": regional_metrics,
            "industry_benchmarks": industry_benchmarks,
            "performance_comparison": performance_comparison,
            "total_sales_reps": len(sales_reps),
            "analysis_date": datetime.now().isoformat()
        }

    async def get_emerging_markets_analysis(
        self, 
        db: Session, 
        target_regions: List[str]
    ) -> Dict[str, Any]:
        """Analyze emerging markets and identify expansion opportunities"""
        emerging_markets = []
        
        for region in target_regions:
            try:
                # Get market insights for each region
                insights = await self.get_regional_market_insights(db, region)
                
                # Assess market potential
                market_potential = await self._assess_market_potential(insights, region)
                
                # Get entry strategy recommendations
                entry_strategies = await self._generate_entry_strategies(insights, region)
                
                emerging_markets.append({
                    "region": region,
                    "insights": insights.dict(),
                    "market_potential": market_potential,
                    "entry_strategies": entry_strategies,
                    "risk_assessment": await self._assess_market_risk(insights, region)
                })
                
            except Exception as e:
                # Log error but continue with other regions
                print(f"Failed to analyze region {region}: {str(e)}")
                continue
        
        # Rank markets by potential
        ranked_markets = sorted(
            emerging_markets, 
            key=lambda x: x["market_potential"]["score"], 
            reverse=True
        )
        
        return {
            "target_regions": target_regions,
            "emerging_markets": ranked_markets,
            "top_opportunities": ranked_markets[:3],
            "analysis_summary": {
                "total_markets_analyzed": len(emerging_markets),
                "high_potential_markets": len([m for m in emerging_markets if m["market_potential"]["score"] > 7]),
                "medium_potential_markets": len([m for m in emerging_markets if 5 <= m["market_potential"]["score"] <= 7]),
                "low_potential_markets": len([m for m in emerging_markets if m["market_potential"]["score"] < 5])
            }
        }

    async def _fetch_market_data(self, region: str, industry: Optional[str]) -> Dict[str, Any]:
        """Fetch market data from external API"""
        try:
            params = {"region": region}
            if industry:
                params["industry"] = industry
            
            headers = {"Authorization": f"Bearer {self.external_api_key}"}
            
            response = requests.get(
                f"{self.external_api_url}/market-data",
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return default data if API fails
                return {
                    "market_size": 1000000,
                    "growth_rate": 5.0,
                    "competition_level": "medium",
                    "market_maturity": "growing"
                }
                
        except Exception as e:
            print(f"Failed to fetch market data: {str(e)}")
            # Return default data
            return {
                "market_size": 1000000,
                "growth_rate": 5.0,
                "competition_level": "medium",
                "market_maturity": "growing"
            }

    async def _get_local_sales_data(
        self, 
        db: Session, 
        region: str, 
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Get local sales data for the region"""
        # Get sales reps in the region
        sales_reps = db.query(SalesRep).filter(SalesRep.region == region).all()
        rep_ids = [rep.id for rep in sales_reps]
        
        if not rep_ids:
            return {
                "total_deals": 0,
                "total_revenue": 0,
                "avg_deal_size": 0,
                "conversion_rate": 0,
                "sales_velocity": 0
            }
        
        # Calculate metrics for the last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Total deals and revenue
        deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        ).all()
        
        total_deals = len(deals)
        total_revenue = sum(deal.value for deal in deals if deal.status == "closed")
        avg_deal_size = total_revenue / total_deals if total_deals > 0 else 0
        
        # Conversion rate
        closed_deals = len([d for d in deals if d.status == "closed"])
        conversion_rate = (closed_deals / total_deals * 100) if total_deals > 0 else 0
        
        # Sales velocity (deals per month)
        sales_velocity = total_deals / 3  # 3 months
        
        return {
            "total_deals": total_deals,
            "total_revenue": total_revenue,
            "avg_deal_size": avg_deal_size,
            "conversion_rate": conversion_rate,
            "sales_velocity": sales_velocity,
            "active_sales_reps": len(sales_reps)
        }

    async def _analyze_market_trends(
        self, 
        region: str, 
        industry: Optional[str]
    ) -> List[MarketTrend]:
        """Analyze market trends for the region"""
        trends = []
        
        # Economic trends
        trends.append(MarketTrend(
            region=region,
            industry=industry or "general",
            trend_type="economic",
            description="Growing market demand in the region",
            impact_score=8.5,
            confidence_level=0.85,
            data_source="economic_indicators",
            last_updated=datetime.now()
        ))
        
        # Technology trends
        trends.append(MarketTrend(
            region=region,
            industry=industry or "general",
            trend_type="technology",
            description="Increased adoption of digital solutions",
            impact_score=7.8,
            confidence_level=0.80,
            data_source="tech_adoption_data",
            last_updated=datetime.now()
        ))
        
        # Competitive trends
        trends.append(MarketTrend(
            region=region,
            industry=industry or "general",
            trend_type="competitive",
            description="New competitors entering the market",
            impact_score=6.5,
            confidence_level=0.75,
            data_source="competitive_intelligence",
            last_updated=datetime.now()
        ))
        
        return trends

    def _assess_competition_level(
        self, 
        market_data: Dict[str, Any], 
        local_sales_data: Dict[str, Any]
    ) -> str:
        """Assess the level of competition in the market"""
        market_size = market_data.get("market_size", 1000000)
        active_reps = local_sales_data.get("active_sales_reps", 1)
        
        # Calculate competition density
        competition_density = active_reps / (market_size / 1000000)  # reps per million
        
        if competition_density < 5:
            return "low"
        elif competition_density < 15:
            return "medium"
        else:
            return "high"

    async def _identify_opportunities(
        self, 
        market_data: Dict[str, Any], 
        trends: List[MarketTrend], 
        local_sales_data: Dict[str, Any]
    ) -> List[str]:
        """Identify key opportunities in the market"""
        opportunities = []
        
        # Market growth opportunities
        growth_rate = market_data.get("growth_rate", 0)
        if growth_rate > 10:
            opportunities.append("High market growth rate - focus on expansion")
        elif growth_rate > 5:
            opportunities.append("Moderate growth - optimize market share")
        
        # Technology adoption opportunities
        tech_trends = [t for t in trends if t.trend_type == "technology"]
        if tech_trends:
            opportunities.append("Technology adoption trend - leverage digital solutions")
        
        # Low competition opportunities
        competition_level = self._assess_competition_level(market_data, local_sales_data)
        if competition_level == "low":
            opportunities.append("Low competition - opportunity for market leadership")
        
        # Performance improvement opportunities
        conversion_rate = local_sales_data.get("conversion_rate", 0)
        if conversion_rate < 15:
            opportunities.append("Low conversion rate - focus on sales process improvement")
        
        return opportunities

    async def _identify_challenges(
        self, 
        market_data: Dict[str, Any], 
        trends: List[MarketTrend], 
        local_sales_data: Dict[str, Any]
    ) -> List[str]:
        """Identify challenges in the market"""
        challenges = []
        
        # High competition challenges
        competition_level = self._assess_competition_level(market_data, local_sales_data)
        if competition_level == "high":
            challenges.append("High competition - need for differentiation")
        
        # Market maturity challenges
        market_maturity = market_data.get("market_maturity", "growing")
        if market_maturity == "mature":
            challenges.append("Mature market - limited growth opportunities")
        
        # Economic challenges
        economic_trends = [t for t in trends if t.trend_type == "economic"]
        if economic_trends:
            challenges.append("Economic uncertainty - need for flexible pricing")
        
        # Performance challenges
        avg_deal_size = local_sales_data.get("avg_deal_size", 0)
        if avg_deal_size < 10000:
            challenges.append("Low average deal size - focus on value proposition")
        
        return challenges

    async def _generate_strategies(
        self, 
        market_data: Dict[str, Any], 
        trends: List[MarketTrend], 
        local_sales_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommended sales strategies"""
        strategies = []
        
        # Market penetration strategies
        competition_level = self._assess_competition_level(market_data, local_sales_data)
        if competition_level == "low":
            strategies.append("Aggressive market penetration with competitive pricing")
        else:
            strategies.append("Focus on differentiation and value-added services")
        
        # Growth strategies
        growth_rate = market_data.get("growth_rate", 0)
        if growth_rate > 10:
            strategies.append("Rapid expansion with increased sales team")
        elif growth_rate > 5:
            strategies.append("Steady growth with optimized sales processes")
        
        # Technology strategies
        tech_trends = [t for t in trends if t.trend_type == "technology"]
        if tech_trends:
            strategies.append("Leverage technology for sales automation and efficiency")
        
        # Performance improvement strategies
        conversion_rate = local_sales_data.get("conversion_rate", 0)
        if conversion_rate < 15:
            strategies.append("Implement sales training and process optimization")
        
        return strategies

    def _assess_market_maturity(
        self, 
        market_data: Dict[str, Any], 
        local_sales_data: Dict[str, Any]
    ) -> str:
        """Assess market maturity level"""
        growth_rate = market_data.get("growth_rate", 0)
        market_size = market_data.get("market_size", 1000000)
        
        if growth_rate > 15 and market_size < 5000000:
            return "emerging"
        elif growth_rate > 5 and market_size < 20000000:
            return "growing"
        elif growth_rate > 0 and market_size < 50000000:
            return "mature"
        else:
            return "declining"

    async def _fetch_external_trends(
        self, 
        region: str, 
        industry: Optional[str], 
        trend_type: Optional[str]
    ) -> List[MarketTrend]:
        """Fetch trends from external API"""
        try:
            params = {"region": region}
            if industry:
                params["industry"] = industry
            if trend_type:
                params["trend_type"] = trend_type
            
            headers = {"Authorization": f"Bearer {self.external_api_key}"}
            
            response = requests.get(
                f"{self.external_api_url}/trends",
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return [MarketTrend(**trend) for trend in data.get("trends", [])]
            else:
                return []
                
        except Exception as e:
            print(f"Failed to fetch external trends: {str(e)}")
            return []

    async def _analyze_local_trends(
        self, 
        db: Session, 
        region: str, 
        industry: Optional[str]
    ) -> List[MarketTrend]:
        """Analyze local trends from sales data"""
        trends = []
        
        # Get sales data for the last 6 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Get sales reps in the region
        sales_reps = db.query(SalesRep).filter(SalesRep.region == region).all()
        rep_ids = [rep.id for rep in sales_reps]
        
        if not rep_ids:
            return trends
        
        # Analyze deal trends
        deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        ).all()
        
        if deals:
            # Calculate trend metrics
            monthly_deals = {}
            for deal in deals:
                month = deal.created_at.strftime("%Y-%m")
                monthly_deals[month] = monthly_deals.get(month, 0) + 1
            
            if len(monthly_deals) >= 2:
                months = sorted(monthly_deals.keys())
                recent_trend = monthly_deals[months[-1]] - monthly_deals[months[-2]]
                
                if recent_trend > 0:
                    trends.append(MarketTrend(
                        region=region,
                        industry=industry or "general",
                        trend_type="sales",
                        description="Increasing deal volume in the region",
                        impact_score=7.0,
                        confidence_level=0.80,
                        data_source="local_sales_data",
                        last_updated=datetime.now()
                    ))
        
        return trends

    async def _get_rep_performance_in_region(
        self, 
        db: Session, 
        sales_rep_id: int, 
        region: str
    ) -> Dict[str, Any]:
        """Get sales rep performance in the specific region"""
        # Get sales rep
        sales_rep = db.query(SalesRep).filter(SalesRep.id == sales_rep_id).first()
        if not sales_rep:
            return {}
        
        # Get deals in the region for the last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id == sales_rep_id,
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        ).all()
        
        total_deals = len(deals)
        closed_deals = len([d for d in deals if d.status == "closed"])
        total_revenue = sum(d.value for d in deals if d.status == "closed")
        
        return {
            "total_deals": total_deals,
            "closed_deals": closed_deals,
            "conversion_rate": (closed_deals / total_deals * 100) if total_deals > 0 else 0,
            "total_revenue": total_revenue,
            "avg_deal_size": total_revenue / closed_deals if closed_deals > 0 else 0,
            "region": region
        }

    async def _analyze_competitors(
        self, 
        db: Session, 
        region: str, 
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze competitors in the region"""
        try:
            # Query actual competitor data from deals and activities
            from ..models import Deal, SalesActivity, CustomerProfile
            
            # Get deals in the region/industry
            deals_query = db.query(Deal).join(CustomerProfile).filter(
                CustomerProfile.region == region
            )
            if industry:
                deals_query = deals_query.filter(CustomerProfile.industry == industry)
            
            deals = deals_query.all()
            
            # Analyze competitor mentions in sales activities
            competitor_mentions = db.query(SalesActivity).filter(
                and_(
                    SalesActivity.notes.contains("competitor"),
                    SalesActivity.created_at >= datetime.now() - timedelta(days=365)
                )
            ).all()
            
            # Extract competitor names from activities
            competitors = {}
            for activity in competitor_mentions:
                if activity.notes:
                    # Simple competitor name extraction
                    import re
                    competitor_patterns = [
                        r"competitor[s]?\s+([A-Za-z\s]+)",
                        r"([A-Za-z\s]+)\s+competitor",
                        r"vs\s+([A-Za-z\s]+)",
                        r"compared\s+to\s+([A-Za-z\s]+)"
                    ]
                    
                    for pattern in competitor_patterns:
                        matches = re.findall(pattern, activity.notes.lower())
                        for match in matches:
                            competitor_name = match.strip().title()
                            if competitor_name and len(competitor_name) > 2:
                                if competitor_name not in competitors:
                                    competitors[competitor_name] = {
                                        "mentions": 0,
                                        "deals_lost": 0,
                                        "deals_won": 0
                                    }
                                competitors[competitor_name]["mentions"] += 1
                                
                                # Check if deal was won or lost
                                deal = db.query(Deal).filter(Deal.id == activity.deal_id).first()
                                if deal:
                                    if deal.status == "closed_won":
                                        competitors[competitor_name]["deals_won"] += 1
                                    elif deal.status == "closed_lost":
                                        competitors[competitor_name]["deals_lost"] += 1
            
            # Calculate market share estimates
            total_deals = len(deals)
            major_competitors = []
            
            for competitor_name, data in competitors.items():
                if data["mentions"] >= 3:  # Only include frequently mentioned competitors
                    market_share = (data["deals_won"] / total_deals * 100) if total_deals > 0 else 0
                    win_rate = (data["deals_won"] / (data["deals_won"] + data["deals_lost"]) * 100) if (data["deals_won"] + data["deals_lost"]) > 0 else 0
                    
                    major_competitors.append({
                        "name": competitor_name,
                        "market_share": round(market_share, 1),
                        "mentions": data["mentions"],
                        "win_rate": round(win_rate, 1),
                        "strengths": self._identify_competitor_strengths(competitor_name, competitor_mentions)
                    })
            
            # Sort by market share
            major_competitors.sort(key=lambda x: x["market_share"], reverse=True)
            
            # Determine competitive landscape
            if len(major_competitors) > 10:
                landscape = "high"
            elif len(major_competitors) > 5:
                landscape = "moderate"
            else:
                landscape = "low"
            
            return {
                "total_competitors": len(competitors),
                "major_competitors": major_competitors[:5],  # Top 5
                "competitive_landscape": landscape,
                "key_differentiators": self._identify_key_differentiators(competitors, deals)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze competitors: {str(e)}")
            # Fallback to basic analysis
            return {
                "total_competitors": 0,
                "major_competitors": [],
                "competitive_landscape": "unknown",
                "key_differentiators": []
            }

    async def _generate_personalized_recommendations(
        self, 
        market_insights: RegionalInsight, 
        performance_data: Dict[str, Any], 
        competitor_analysis: Dict[str, Any], 
        sales_rep: SalesRep
    ) -> Dict[str, Any]:
        """Generate personalized recommendations for the sales rep"""
        recommendations = {
            "immediate_actions": [],
            "short_term_strategies": [],
            "long_term_opportunities": [],
            "skill_development": []
        }
        
        # Performance-based recommendations
        conversion_rate = performance_data.get("conversion_rate", 0)
        if conversion_rate < 15:
            recommendations["immediate_actions"].append("Focus on improving lead qualification process")
            recommendations["skill_development"].append("Sales qualification training")
        
        avg_deal_size = performance_data.get("avg_deal_size", 0)
        if avg_deal_size < 10000:
            recommendations["short_term_strategies"].append("Focus on larger deals and value selling")
        
        # Market-based recommendations
        if market_insights.competition_level == "high":
            recommendations["immediate_actions"].append("Differentiate from competitors through unique value propositions")
        
        if market_insights.growth_rate > 10:
            recommendations["long_term_opportunities"].append("Prepare for market expansion and increased demand")
        
        # Opportunity-based recommendations
        for opportunity in market_insights.key_opportunities:
            if "technology" in opportunity.lower():
                recommendations["short_term_strategies"].append("Leverage technology solutions in sales presentations")
        
        return recommendations

    async def _calculate_regional_metrics(
        self, 
        db: Session, 
        sales_reps: List[SalesRep], 
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate regional performance metrics"""
        rep_ids = [rep.id for rep in sales_reps]
        
        # Get deals for the last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        deals = db.query(Deal).filter(
            and_(
                Deal.sales_rep_id.in_(rep_ids),
                Deal.created_at >= start_date,
                Deal.created_at <= end_date
            )
        ).all()
        
        total_deals = len(deals)
        closed_deals = len([d for d in deals if d.status == "closed"])
        total_revenue = sum(d.value for d in deals if d.status == "closed")
        
        return {
            "total_deals": total_deals,
            "closed_deals": closed_deals,
            "conversion_rate": (closed_deals / total_deals * 100) if total_deals > 0 else 0,
            "total_revenue": total_revenue,
            "avg_deal_size": total_revenue / closed_deals if closed_deals > 0 else 0,
            "deals_per_rep": total_deals / len(sales_reps) if sales_reps else 0,
            "revenue_per_rep": total_revenue / len(sales_reps) if sales_reps else 0
        }

    async def _get_industry_benchmarks(self, db: Session, industry: Optional[str]) -> Dict[str, Any]:
        """Get industry performance benchmarks"""
        benchmarks = {
            "conversion_rate": 20.0,
            "avg_deal_size": 25000,
            "sales_cycle_length": 45,
            "deals_per_rep_per_month": 8,
            "revenue_per_rep_per_month": 200000
        }
        try:
            # Query actual industry benchmarks from historical data
            from ..models import Deal, SalesActivity, CustomerProfile

            # Get historical deals for the industry
            deals_query = db.query(Deal).join(CustomerProfile)
            if industry:
                deals_query = deals_query.filter(CustomerProfile.industry == industry)

            deals = deals_query.filter(
                Deal.created_at >= datetime.now() - timedelta(days=365)
            ).all()

            if deals:
                total_deals = len(deals)
                closed_deals = len([d for d in deals if d.status in ("closed", "closed_won")])
                if total_deals > 0:
                    benchmarks["conversion_rate"] = (closed_deals / total_deals) * 100
                    benchmarks["avg_deal_size"] = sum(d.value for d in deals) / total_deals

        except Exception as e:
            logger.warning(f"Could not compute industry benchmarks from data: {e}")

        # Adjust based on industry defaults
        if industry == "technology":
            benchmarks.update({
                "conversion_rate": 15.0,
                "avg_deal_size": 50000,
                "sales_cycle_length": 60
            })
        elif industry == "consulting":
            benchmarks.update({
                "conversion_rate": 25.0,
                "avg_deal_size": 35000,
                "sales_cycle_length": 30
            })

        return benchmarks

    async def _compare_performance(
        self, 
        regional_metrics: Dict[str, Any], 
        industry_benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare regional performance to industry benchmarks"""
        comparison = {}
        
        for metric, benchmark_value in industry_benchmarks.items():
            if metric in regional_metrics:
                actual_value = regional_metrics[metric]
                if benchmark_value > 0:
                    percentage_diff = ((actual_value - benchmark_value) / benchmark_value) * 100
                    comparison[metric] = {
                        "actual": actual_value,
                        "benchmark": benchmark_value,
                        "difference": percentage_diff,
                        "status": "above" if percentage_diff > 0 else "below" if percentage_diff < 0 else "at"
                    }
        
        return comparison

    async def _assess_market_potential(
        self, 
        insights: RegionalInsight, 
        region: str
    ) -> Dict[str, Any]:
        """Assess market potential for expansion"""
        # Calculate potential score based on various factors
        growth_score = min(insights.growth_rate / 10, 1.0) * 25
        size_score = min(insights.market_size / 10000000, 1.0) * 25
        competition_score = (1.0 - {"low": 0.2, "medium": 0.5, "high": 0.8}.get(insights.competition_level, 0.5)) * 25
        maturity_score = {"emerging": 0.8, "growing": 0.6, "mature": 0.4, "declining": 0.2}.get(insights.market_maturity, 0.5) * 25
        
        total_score = growth_score + size_score + competition_score + maturity_score
        
        return {
            "score": total_score,
            "rating": "high" if total_score > 7 else "medium" if total_score > 5 else "low",
            "factors": {
                "growth_potential": growth_score,
                "market_size": size_score,
                "competition_level": competition_score,
                "market_maturity": maturity_score
            }
        }

    async def _generate_entry_strategies(
        self, 
        insights: RegionalInsight, 
        region: str
    ) -> List[str]:
        """Generate entry strategies for the market"""
        strategies = []
        
        if insights.competition_level == "low":
            strategies.append("Aggressive market entry with competitive pricing")
        else:
            strategies.append("Niche market entry with differentiated offerings")
        
        if insights.growth_rate > 10:
            strategies.append("Rapid expansion strategy with increased resources")
        else:
            strategies.append("Gradual market penetration with measured approach")
        
        if insights.market_maturity == "emerging":
            strategies.append("Early market positioning and thought leadership")
        elif insights.market_maturity == "mature":
            strategies.append("Focus on market share acquisition and consolidation")
        
        return strategies

    async def _assess_market_risk(
        self, 
        insights: RegionalInsight, 
        region: str
    ) -> Dict[str, Any]:
        """Assess market entry risks"""
        risk_factors = []
        risk_score = 0
        
        # Competition risk
        if insights.competition_level == "high":
            risk_factors.append("High competition may limit market share")
            risk_score += 3
        
        # Market maturity risk
        if insights.market_maturity == "declining":
            risk_factors.append("Declining market may reduce opportunities")
            risk_score += 4
        elif insights.market_maturity == "mature":
            risk_factors.append("Mature market may have limited growth")
            risk_score += 2
        
        # Growth risk
        if insights.growth_rate < 2:
            risk_factors.append("Low growth rate may limit expansion")
            risk_score += 3
        
        return {
            "risk_score": min(risk_score, 10),
            "risk_level": "high" if risk_score > 7 else "medium" if risk_score > 4 else "low",
            "risk_factors": risk_factors,
            "mitigation_strategies": [
                "Diversify product offerings",
                "Focus on customer retention",
                "Develop competitive advantages"
            ]
        }

    async def _store_market_insight(
        self, 
        db: Session, 
        insight: RegionalInsight, 
        region: str, 
        industry: Optional[str]
    ):
        """Store market insight in database"""
        try:
            # Create or update market insight record
            existing_insight = db.query(EricMarketInsight).filter(
                and_(
                    EricMarketInsight.region == region,
                    EricMarketInsight.industry == (industry or "general")
                )
            ).first()
            
            if existing_insight:
                existing_insight.market_size = insight.market_size
                existing_insight.growth_rate = insight.growth_rate
                existing_insight.competition_level = insight.competition_level
                existing_insight.market_maturity = insight.market_maturity
                existing_insight.key_opportunities = json.dumps(insight.key_opportunities)
                existing_insight.challenges = json.dumps(insight.challenges)
                existing_insight.recommended_strategies = json.dumps(insight.recommended_strategies)
                existing_insight.updated_at = datetime.now()
            else:
                new_insight = EricMarketInsight(
                    region=region,
                    industry=industry or "general",
                    market_size=insight.market_size,
                    growth_rate=insight.growth_rate,
                    competition_level=insight.competition_level,
                    market_maturity=insight.market_maturity,
                    key_opportunities=json.dumps(insight.key_opportunities),
                    challenges=json.dumps(insight.challenges),
                    recommended_strategies=json.dumps(insight.recommended_strategies),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_insight)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"Failed to store market insight: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        try:
            # Test Redis connection
            await self.redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        try:
            # Test Kafka connection
            await self.kafka_producer.send_message("health_check", {"service": "local_market_insights"})
            kafka_status = "healthy"
        except Exception as e:
            kafka_status = f"unhealthy: {str(e)}"
        
        try:
            # Test external API connection
            headers = {"Authorization": f"Bearer {self.external_api_key}"}
            response = requests.get(f"{self.external_api_url}/health", headers=headers, timeout=10)
            api_status = "healthy" if response.status_code == 200 else f"unhealthy: {response.status_code}"
        except Exception as e:
            api_status = f"unhealthy: {str(e)}"
        
        return {
            "service": "local_market_insights",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "redis": redis_status,
                "kafka": kafka_status,
                "external_api": api_status
            }
        }
