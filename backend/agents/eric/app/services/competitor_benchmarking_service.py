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

class CompetitorProfile(BaseModel):
    id: Optional[int] = None
    name: str
    industry: str
    website: str
    social_media: Dict[str, str] = {}
    key_metrics: Dict[str, float] = {}
    pricing_strategy: str
    target_market: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    opportunities: List[str] = []
    threats: List[str] = []
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None

class BenchmarkingMetrics(BaseModel):
    metric_name: str
    your_value: float
    industry_average: float
    competitor_average: float
    top_performer_value: float
    percentile_rank: float
    trend: str
    recommendation: str
    confidence_score: float

class CompetitiveAnalysis(BaseModel):
    analysis_id: str
    competitor_id: int
    analysis_date: datetime
    market_position: str
    competitive_advantage: List[str] = []
    areas_for_improvement: List[str] = []
    pricing_analysis: Dict[str, Any] = {}
    feature_comparison: Dict[str, Any] = {}
    market_share_estimate: float
    threat_level: str
    opportunities: List[str] = []
    recommendations: List[str] = []

class CompetitorBenchmarkingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize competitor benchmarking service"""
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
            logger.info("Competitor benchmarking service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize competitor benchmarking service: {e}")
            raise
        
        # Industry benchmarks (simplified for demo)
        self.industry_benchmarks = {
            "technology": {
                "conversion_rate": 2.5,
                "response_time": 5.2,
                "deal_size": 25000,
                "sales_cycle": 45,
                "customer_acquisition_cost": 1500,
                "lifetime_value": 75000,
                "churn_rate": 0.15
            },
            "healthcare": {
                "conversion_rate": 1.8,
                "response_time": 8.5,
                "deal_size": 50000,
                "sales_cycle": 90,
                "customer_acquisition_cost": 3000,
                "lifetime_value": 120000,
                "churn_rate": 0.08
            },
            "finance": {
                "conversion_rate": 1.2,
                "response_time": 12.0,
                "deal_size": 75000,
                "sales_cycle": 120,
                "customer_acquisition_cost": 5000,
                "lifetime_value": 200000,
                "churn_rate": 0.05
            },
            "manufacturing": {
                "conversion_rate": 3.2,
                "response_time": 4.8,
                "deal_size": 35000,
                "sales_cycle": 60,
                "customer_acquisition_cost": 2000,
                "lifetime_value": 90000,
                "churn_rate": 0.12
            }
        }
    
    async def create_competitor_profile(self, competitor_data: CompetitorProfile) -> CompetitorProfile:
        """Create a new competitor profile for benchmarking"""
        async with get_eric_database() as session:
            try:
                # Validate competitor data
                if not self._validate_competitor_data(competitor_data):
                    raise ValueError("Invalid competitor data")
                
                # Create competitor profile record
                competitor_profile = {
                    "name": competitor_data.name,
                    "industry": competitor_data.industry,
                    "website": competitor_data.website,
                    "social_media": json.dumps(competitor_data.social_media),
                    "key_metrics": json.dumps(competitor_data.key_metrics),
                    "pricing_strategy": competitor_data.pricing_strategy,
                    "target_market": json.dumps(competitor_data.target_market),
                    "strengths": json.dumps(competitor_data.strengths),
                    "weaknesses": json.dumps(competitor_data.weaknesses),
                    "opportunities": json.dumps(competitor_data.opportunities),
                    "threats": json.dumps(competitor_data.threats),
                    "created_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow()
                }
                
                # Store in database (simplified for demo)
                competitor_data.id = 1  # Simulate ID generation
                competitor_data.created_at = competitor_profile["created_at"]
                competitor_data.last_updated = competitor_profile["last_updated"]
                
                # Cache competitor profile
                await self.redis_manager.set_cache(
                    f"competitor_profile_{competitor_data.id}",
                    competitor_data.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "competitor_benchmarking.competitor_profile_created",
                    {
                        "competitor_id": competitor_data.id,
                        "name": competitor_data.name,
                        "industry": competitor_data.industry,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created competitor profile: {competitor_data.name}")
                return competitor_data
                
            except Exception as e:
                logger.error(f"Failed to create competitor profile: {e}")
                raise
    
    async def get_competitor_profiles(self, industry: str = None) -> List[CompetitorProfile]:
        """Get all competitor profiles, optionally filtered by industry"""
        try:
            # Try to get from cache first
            cache_key = f"competitor_profiles_{industry}" if industry else "all_competitor_profiles"
            cached_profiles = await self.redis_manager.get_cache(cache_key)
            if cached_profiles:
                return [CompetitorProfile(**profile) for profile in cached_profiles]
            
            # Get from database (simplified for demo)
            profiles = [
                CompetitorProfile(
                    id=1,
                    name="TechCorp Solutions",
                    industry="technology",
                    website="https://techcorp.com",
                    social_media={
                        "linkedin": "https://linkedin.com/company/techcorp",
                        "twitter": "https://twitter.com/techcorp"
                    },
                    key_metrics={
                        "conversion_rate": 2.8,
                        "response_time": 4.5,
                        "deal_size": 28000,
                        "sales_cycle": 42
                    },
                    pricing_strategy="premium",
                    target_market=["enterprise", "mid-market"],
                    strengths=["Strong brand", "Technical expertise", "Global presence"],
                    weaknesses=["High pricing", "Complex onboarding"],
                    opportunities=["AI integration", "Cloud migration"],
                    threats=["New entrants", "Price competition"],
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                ),
                CompetitorProfile(
                    id=2,
                    name="InnovateSoft",
                    industry="technology",
                    website="https://innovatesoft.com",
                    social_media={
                        "linkedin": "https://linkedin.com/company/innovatesoft",
                        "twitter": "https://twitter.com/innovatesoft"
                    },
                    key_metrics={
                        "conversion_rate": 3.2,
                        "response_time": 3.8,
                        "deal_size": 22000,
                        "sales_cycle": 38
                    },
                    pricing_strategy="competitive",
                    target_market=["startups", "small_business"],
                    strengths=["Fast implementation", "Affordable pricing", "Good support"],
                    weaknesses=["Limited features", "Small team"],
                    opportunities=["Market expansion", "Feature development"],
                    threats=["Larger competitors", "Economic downturn"],
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
            ]
            
            # Filter by industry if specified
            if industry:
                profiles = [p for p in profiles if p.industry == industry]
            
            # Cache profiles
            await self.redis_manager.set_cache(
                cache_key,
                [profile.dict() for profile in profiles],
                expire=3600  # 1 hour
            )
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to get competitor profiles: {e}")
            raise
    
    async def calculate_benchmarking_metrics(self, industry: str, your_metrics: Dict[str, float]) -> List[BenchmarkingMetrics]:
        """Calculate benchmarking metrics comparing your performance to industry and competitors"""
        async with get_eric_database() as session:
            try:
                # Get industry benchmarks
                industry_benchmarks = self.industry_benchmarks.get(industry, {})
                
                # Get competitor profiles for this industry
                competitors = await self.get_competitor_profiles(industry)
                
                # Calculate competitor averages
                competitor_metrics = {}
                for competitor in competitors:
                    for metric, value in competitor.key_metrics.items():
                        if metric not in competitor_metrics:
                            competitor_metrics[metric] = []
                        competitor_metrics[metric].append(value)
                
                competitor_averages = {}
                for metric, values in competitor_metrics.items():
                    competitor_averages[metric] = sum(values) / len(values)
                
                # Generate benchmarking metrics
                benchmarking_results = []
                
                for metric_name, your_value in your_metrics.items():
                    industry_avg = industry_benchmarks.get(metric_name, 0)
                    competitor_avg = competitor_averages.get(metric_name, 0)
                    
                    # Calculate top performer value (simplified)
                    top_performer = max(industry_avg, competitor_avg, your_value) * 1.2
                    
                    # Calculate percentile rank
                    all_values = [industry_avg, competitor_avg, your_value]
                    all_values.sort()
                    your_rank = all_values.index(your_value) + 1
                    percentile_rank = (your_rank / len(all_values)) * 100
                    
                    # Determine trend
                    if your_value > industry_avg:
                        trend = "above_average"
                    elif your_value < industry_avg:
                        trend = "below_average"
                    else:
                        trend = "average"
                    
                    # Generate recommendation
                    recommendation = self._generate_metric_recommendation(
                        metric_name, your_value, industry_avg, competitor_avg
                    )
                    
                    # Calculate confidence score
                    confidence_score = min(0.95, 0.7 + (len(competitors) * 0.05))
                    
                    benchmarking_results.append(BenchmarkingMetrics(
                        metric_name=metric_name,
                        your_value=your_value,
                        industry_average=industry_avg,
                        competitor_average=competitor_avg,
                        top_performer_value=top_performer,
                        percentile_rank=percentile_rank,
                        trend=trend,
                        recommendation=recommendation,
                        confidence_score=confidence_score
                    ))
                
                # Cache results
                await self.redis_manager.set_cache(
                    f"benchmarking_metrics_{industry}",
                    [metric.dict() for metric in benchmarking_results],
                    expire=3600  # 1 hour
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "competitor_benchmarking.metrics_calculated",
                    {
                        "industry": industry,
                        "metrics_count": len(benchmarking_results),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Calculated benchmarking metrics for {industry}")
                return benchmarking_results
                
            except Exception as e:
                logger.error(f"Failed to calculate benchmarking metrics: {e}")
                raise
    
    async def perform_competitive_analysis(self, competitor_id: int) -> CompetitiveAnalysis:
        """Perform comprehensive competitive analysis for a specific competitor"""
        async with get_eric_database() as session:
            try:
                # Get competitor profile
                competitors = await self.get_competitor_profiles()
                competitor = next((c for c in competitors if c.id == competitor_id), None)
                
                if not competitor:
                    raise ValueError(f"Competitor with ID {competitor_id} not found")
                
                # Analyze market position
                market_position = self._analyze_market_position(competitor)
                
                # Identify competitive advantages
                competitive_advantages = self._identify_competitive_advantages(competitor)
                
                # Identify areas for improvement
                areas_for_improvement = self._identify_improvement_areas(competitor)
                
                # Analyze pricing strategy
                pricing_analysis = self._analyze_pricing_strategy(competitor)
                
                # Compare features
                feature_comparison = self._compare_features(competitor)
                
                # Estimate market share
                market_share_estimate = self._estimate_market_share(competitor)
                
                # Assess threat level
                threat_level = self._assess_threat_level(competitor)
                
                # Identify opportunities
                opportunities = self._identify_opportunities(competitor)
                
                # Generate recommendations
                recommendations = self._generate_competitive_recommendations(competitor)
                
                analysis = CompetitiveAnalysis(
                    analysis_id=f"analysis_{competitor_id}_{datetime.utcnow().strftime('%Y%m%d')}",
                    competitor_id=competitor_id,
                    analysis_date=datetime.utcnow(),
                    market_position=market_position,
                    competitive_advantage=competitive_advantages,
                    areas_for_improvement=areas_for_improvement,
                    pricing_analysis=pricing_analysis,
                    feature_comparison=feature_comparison,
                    market_share_estimate=market_share_estimate,
                    threat_level=threat_level,
                    opportunities=opportunities,
                    recommendations=recommendations
                )
                
                # Cache analysis
                await self.redis_manager.set_cache(
                    f"competitive_analysis_{competitor_id}",
                    analysis.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "competitor_benchmarking.competitive_analysis_completed",
                    {
                        "competitor_id": competitor_id,
                        "analysis_id": analysis.analysis_id,
                        "threat_level": threat_level,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Completed competitive analysis for {competitor.name}")
                return analysis
                
            except Exception as e:
                logger.error(f"Failed to perform competitive analysis: {e}")
                raise
    
    async def get_competitive_intelligence_report(self, industry: str) -> Dict[str, Any]:
        """Generate comprehensive competitive intelligence report"""
        try:
            # Get competitor profiles
            competitors = await self.get_competitor_profiles(industry)
            
            # Get industry benchmarks
            industry_benchmarks = self.industry_benchmarks.get(industry, {})
            
            # Analyze competitive landscape
            competitive_landscape = self._analyze_competitive_landscape(competitors)
            
            # Identify market trends
            market_trends = self._identify_market_trends(industry, competitors)
            
            # Generate strategic insights
            strategic_insights = self._generate_strategic_insights(competitors, industry_benchmarks)
            
            # Calculate market concentration
            market_concentration = self._calculate_market_concentration(competitors)
            
            # Identify competitive threats
            competitive_threats = self._identify_competitive_threats(competitors)
            
            # Generate recommendations
            recommendations = self._generate_intelligence_recommendations(competitors, industry)
            
            report = {
                "industry": industry,
                "report_date": datetime.utcnow().isoformat(),
                "competitors_analyzed": len(competitors),
                "competitive_landscape": competitive_landscape,
                "market_trends": market_trends,
                "strategic_insights": strategic_insights,
                "market_concentration": market_concentration,
                "competitive_threats": competitive_threats,
                "recommendations": recommendations,
                "key_metrics": {
                    "total_competitors": len(competitors),
                    "high_threat_competitors": len([c for c in competitors if self._assess_threat_level(c) == "high"]),
                    "market_leader": max(competitors, key=lambda x: x.key_metrics.get("deal_size", 0)).name if competitors else None,
                    "fastest_growing": max(competitors, key=lambda x: x.key_metrics.get("conversion_rate", 0)).name if competitors else None
                }
            }
            
            # Cache report
            await self.redis_manager.set_cache(
                f"competitive_intelligence_report_{industry}",
                report,
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "competitor_benchmarking.intelligence_report_generated",
                {
                    "industry": industry,
                    "competitors_analyzed": len(competitors),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Generated competitive intelligence report for {industry}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate competitive intelligence report: {e}")
            raise
    
    async def monitor_competitor_activity(self, competitor_id: int) -> Dict[str, Any]:
        """Monitor real-time competitor activity and changes"""
        try:
            # Get competitor profile
            competitors = await self.get_competitor_profiles()
            competitor = next((c for c in competitors if c.id == competitor_id), None)
            
            if not competitor:
                raise ValueError(f"Competitor with ID {competitor_id} not found")
            
            # Monitor website changes (simplified)
            website_changes = await self._monitor_website_changes(competitor.website)
            
            # Monitor social media activity
            social_media_activity = await self._monitor_social_media(competitor.social_media)
            
            # Monitor pricing changes
            pricing_changes = await self._monitor_pricing_changes(competitor)
            
            # Monitor new features or announcements
            new_announcements = await self._monitor_announcements(competitor)
            
            # Monitor hiring activity
            hiring_activity = await self._monitor_hiring_activity(competitor)
            
            activity_report = {
                "competitor_id": competitor_id,
                "competitor_name": competitor.name,
                "monitoring_date": datetime.utcnow().isoformat(),
                "website_changes": website_changes,
                "social_media_activity": social_media_activity,
                "pricing_changes": pricing_changes,
                "new_announcements": new_announcements,
                "hiring_activity": hiring_activity,
                "activity_score": self._calculate_activity_score(
                    website_changes, social_media_activity, pricing_changes, new_announcements, hiring_activity
                ),
                "alerts": self._generate_activity_alerts(
                    website_changes, social_media_activity, pricing_changes, new_announcements, hiring_activity
                )
            }
            
            # Cache activity report
            await self.redis_manager.set_cache(
                f"competitor_activity_{competitor_id}",
                activity_report,
                expire=3600  # 1 hour
            )
            
            # Publish event if significant activity detected
            if activity_report["activity_score"] > 0.7:
                await self.kafka_manager.publish_event(
                    "competitor_benchmarking.high_activity_detected",
                    {
                        "competitor_id": competitor_id,
                        "competitor_name": competitor.name,
                        "activity_score": activity_report["activity_score"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            logger.info(f"Monitored competitor activity for {competitor.name}")
            return activity_report
            
        except Exception as e:
            logger.error(f"Failed to monitor competitor activity: {e}")
            raise
    
    async def update_competitor_profile(self, competitor_id: int, updates: Dict[str, Any]) -> CompetitorProfile:
        """Update an existing competitor profile"""
        async with get_eric_database() as session:
            try:
                # Get existing profile
                competitors = await self.get_competitor_profiles()
                competitor = next((c for c in competitors if c.id == competitor_id), None)
                
                if not competitor:
                    raise ValueError(f"Competitor with ID {competitor_id} not found")
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(competitor, field):
                        setattr(competitor, field, value)
                
                competitor.last_updated = datetime.utcnow()
                
                # Update cache
                await self.redis_manager.set_cache(
                    f"competitor_profile_{competitor_id}",
                    competitor.dict(),
                    expire=86400  # 24 hours
                )
                
                # Clear related caches
                await self.redis_manager.delete_cache("all_competitor_profiles")
                await self.redis_manager.delete_cache(f"competitor_profiles_{competitor.industry}")
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "competitor_benchmarking.competitor_profile_updated",
                    {
                        "competitor_id": competitor_id,
                        "updates": updates,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Updated competitor profile: {competitor.name}")
                return competitor
                
            except Exception as e:
                logger.error(f"Failed to update competitor profile: {e}")
                raise
    
    async def delete_competitor_profile(self, competitor_id: int) -> bool:
        """Delete a competitor profile"""
        try:
            # Get existing profile
            competitors = await self.get_competitor_profiles()
            competitor = next((c for c in competitors if c.id == competitor_id), None)
            
            if not competitor:
                raise ValueError(f"Competitor with ID {competitor_id} not found")
            
            # Delete from cache
            await self.redis_manager.delete_cache(f"competitor_profile_{competitor_id}")
            await self.redis_manager.delete_cache("all_competitor_profiles")
            await self.redis_manager.delete_cache(f"competitor_profiles_{competitor.industry}")
            
            # Publish event
            await self.kafka_manager.publish_event(
                "competitor_benchmarking.competitor_profile_deleted",
                {
                    "competitor_id": competitor_id,
                    "name": competitor.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Deleted competitor profile: {competitor.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete competitor profile: {e}")
            raise
    
    def _validate_competitor_data(self, competitor: CompetitorProfile) -> bool:
        """Validate competitor data"""
        if not competitor.name or not competitor.industry:
            return False
        
        if not competitor.website:
            return False
        
        if not competitor.key_metrics or len(competitor.key_metrics) == 0:
            return False
        
        return True
    
    def _generate_metric_recommendation(self, metric_name: str, your_value: float, industry_avg: float, competitor_avg: float) -> str:
        """Generate recommendation based on metric comparison"""
        if metric_name == "conversion_rate":
            if your_value < industry_avg:
                return "Focus on improving lead qualification and sales process optimization"
            elif your_value > competitor_avg:
                return "Maintain current performance and consider expanding market reach"
            else:
                return "Implement A/B testing to optimize conversion funnel"
        
        elif metric_name == "response_time":
            if your_value > industry_avg:
                return "Implement automated response systems and improve lead routing"
            elif your_value < competitor_avg:
                return "Leverage fast response time as competitive advantage in marketing"
            else:
                return "Optimize lead response workflows for faster engagement"
        
        elif metric_name == "deal_size":
            if your_value < industry_avg:
                return "Focus on upselling strategies and value-based selling"
            elif your_value > competitor_avg:
                return "Maintain premium positioning and expand enterprise offerings"
            else:
                return "Develop targeted pricing strategies for different market segments"
        
        else:
            return "Continue monitoring and optimizing this metric"
    
    def _analyze_market_position(self, competitor: CompetitorProfile) -> str:
        """Analyze competitor's market position"""
        avg_deal_size = competitor.key_metrics.get("deal_size", 0)
        conversion_rate = competitor.key_metrics.get("conversion_rate", 0)
        
        if avg_deal_size > 50000 and conversion_rate > 3.0:
            return "market_leader"
        elif avg_deal_size > 25000 and conversion_rate > 2.0:
            return "strong_contender"
        elif avg_deal_size > 15000 and conversion_rate > 1.5:
            return "mid_market_player"
        else:
            return "niche_player"
    
    def _identify_competitive_advantages(self, competitor: CompetitorProfile) -> List[str]:
        """Identify competitor's competitive advantages"""
        advantages = []
        
        if competitor.key_metrics.get("response_time", 100) < 5:
            advantages.append("Fast response time")
        
        if competitor.key_metrics.get("deal_size", 0) > 30000:
            advantages.append("Large deal sizes")
        
        if "global presence" in competitor.strengths:
            advantages.append("Global reach")
        
        if competitor.pricing_strategy == "premium":
            advantages.append("Premium positioning")
        
        return advantages
    
    def _identify_improvement_areas(self, competitor: CompetitorProfile) -> List[str]:
        """Identify areas where competitor can improve"""
        improvements = []
        
        if competitor.key_metrics.get("response_time", 100) > 10:
            improvements.append("Slow response time")
        
        if competitor.key_metrics.get("conversion_rate", 0) < 1.5:
            improvements.append("Low conversion rate")
        
        if "High pricing" in competitor.weaknesses:
            improvements.append("Pricing strategy")
        
        if "Complex onboarding" in competitor.weaknesses:
            improvements.append("Customer onboarding")
        
        return improvements
    
    def _analyze_pricing_strategy(self, competitor: CompetitorProfile) -> Dict[str, Any]:
        """Analyze competitor's pricing strategy"""
        return {
            "strategy": competitor.pricing_strategy,
            "positioning": "premium" if competitor.pricing_strategy == "premium" else "competitive",
            "target_market": competitor.target_market,
            "pricing_flexibility": "high" if competitor.pricing_strategy == "competitive" else "low",
            "value_proposition": "quality" if competitor.pricing_strategy == "premium" else "affordability"
        }
    
    def _compare_features(self, competitor: CompetitorProfile) -> Dict[str, Any]:
        """Compare features with competitor"""
        return {
            "strengths": competitor.strengths,
            "weaknesses": competitor.weaknesses,
            "unique_features": [s for s in competitor.strengths if "unique" in s.lower()],
            "market_differentiators": competitor.strengths[:3]
        }
    
    def _estimate_market_share(self, competitor: CompetitorProfile) -> float:
        """Estimate competitor's market share"""
        # Simplified estimation based on deal size and conversion rate
        deal_size = competitor.key_metrics.get("deal_size", 0)
        conversion_rate = competitor.key_metrics.get("conversion_rate", 0)
        
        # Base market share on relative performance
        base_share = min(25.0, (deal_size / 10000) * (conversion_rate / 2.0))
        
        # Adjust based on market position
        if self._analyze_market_position(competitor) == "market_leader":
            base_share *= 1.5
        elif self._analyze_market_position(competitor) == "niche_player":
            base_share *= 0.5
        
        return min(base_share, 30.0)  # Cap at 30%
    
    def _assess_threat_level(self, competitor: CompetitorProfile) -> str:
        """Assess competitive threat level"""
        market_position = self._analyze_market_position(competitor)
        market_share = self._estimate_market_share(competitor)
        
        if market_position == "market_leader" and market_share > 15:
            return "high"
        elif market_position == "strong_contender" and market_share > 10:
            return "medium"
        else:
            return "low"
    
    def _identify_opportunities(self, competitor: CompetitorProfile) -> List[str]:
        """Identify opportunities based on competitor analysis"""
        opportunities = []
        
        if "High pricing" in competitor.weaknesses:
            opportunities.append("Competitive pricing strategy")
        
        if "Complex onboarding" in competitor.weaknesses:
            opportunities.append("Simplified customer experience")
        
        if competitor.key_metrics.get("response_time", 100) > 8:
            opportunities.append("Faster customer service")
        
        opportunities.extend(competitor.opportunities)
        
        return opportunities[:5]  # Return top 5 opportunities
    
    def _generate_competitive_recommendations(self, competitor: CompetitorProfile) -> List[str]:
        """Generate strategic recommendations based on competitor analysis"""
        recommendations = []
        
        threat_level = self._assess_threat_level(competitor)
        
        if threat_level == "high":
            recommendations.append("Develop differentiated value proposition")
            recommendations.append("Focus on customer retention strategies")
            recommendations.append("Consider strategic partnerships")
        
        elif threat_level == "medium":
            recommendations.append("Monitor competitor pricing changes")
            recommendations.append("Enhance customer service capabilities")
            recommendations.append("Invest in product differentiation")
        
        else:
            recommendations.append("Maintain competitive advantages")
            recommendations.append("Expand market presence")
            recommendations.append("Focus on growth opportunities")
        
        return recommendations
    
    def _analyze_competitive_landscape(self, competitors: List[CompetitorProfile]) -> Dict[str, Any]:
        """Analyze overall competitive landscape"""
        if not competitors:
            return {"status": "no_competitors", "insights": []}
        
        # Analyze market positions
        positions = [self._analyze_market_position(c) for c in competitors]
        position_counts = {pos: positions.count(pos) for pos in set(positions)}
        
        # Analyze pricing strategies
        pricing_strategies = [c.pricing_strategy for c in competitors]
        pricing_counts = {strategy: pricing_strategies.count(strategy) for strategy in set(pricing_strategies)}
        
        # Calculate average metrics
        avg_deal_size = sum(c.key_metrics.get("deal_size", 0) for c in competitors) / len(competitors)
        avg_conversion_rate = sum(c.key_metrics.get("conversion_rate", 0) for c in competitors) / len(competitors)
        
        return {
            "total_competitors": len(competitors),
            "market_positions": position_counts,
            "pricing_strategies": pricing_counts,
            "average_metrics": {
                "deal_size": avg_deal_size,
                "conversion_rate": avg_conversion_rate
            },
            "market_concentration": "high" if len(competitors) <= 3 else "medium" if len(competitors) <= 8 else "low"
        }
    
    def _identify_market_trends(self, industry: str, competitors: List[CompetitorProfile]) -> List[str]:
        """Identify market trends based on competitor analysis"""
        trends = []
        
        # Analyze pricing trends
        premium_count = sum(1 for c in competitors if c.pricing_strategy == "premium")
        if premium_count > len(competitors) / 2:
            trends.append("Market moving toward premium pricing")
        
        # Analyze target market trends
        enterprise_focus = sum(1 for c in competitors if "enterprise" in c.target_market)
        if enterprise_focus > len(competitors) / 2:
            trends.append("Strong focus on enterprise market")
        
        # Analyze technology trends
        ai_focus = sum(1 for c in competitors if "AI" in " ".join(c.strengths + c.opportunities))
        if ai_focus > 0:
            trends.append("AI integration becoming standard")
        
        return trends
    
    def _generate_strategic_insights(self, competitors: List[CompetitorProfile], industry_benchmarks: Dict[str, float]) -> List[str]:
        """Generate strategic insights from competitive analysis"""
        insights = []
        
        if not competitors:
            return ["Limited competitive intelligence available"]
        
        # Analyze competitive gaps
        avg_deal_size = sum(c.key_metrics.get("deal_size", 0) for c in competitors) / len(competitors)
        if avg_deal_size < industry_benchmarks.get("deal_size", 0):
            insights.append("Opportunity to capture larger deals in the market")
        
        # Analyze response time advantage
        avg_response_time = sum(c.key_metrics.get("response_time", 10) for c in competitors) / len(competitors)
        if avg_response_time > 8:
            insights.append("Fast response time can be a significant competitive advantage")
        
        # Analyze market positioning
        premium_count = sum(1 for c in competitors if c.pricing_strategy == "premium")
        if premium_count < len(competitors) / 2:
            insights.append("Premium positioning opportunity in competitive market")
        
        return insights
    
    def _calculate_market_concentration(self, competitors: List[CompetitorProfile]) -> Dict[str, Any]:
        """Calculate market concentration metrics"""
        if not competitors:
            return {"concentration": "unknown", "hhi": 0, "interpretation": "No competitor data"}
        
        # Calculate Herfindahl-Hirschman Index (simplified)
        market_shares = [self._estimate_market_share(c) for c in competitors]
        hhi = sum(share ** 2 for share in market_shares)
        
        # Interpret HHI
        if hhi > 2500:
            concentration = "high"
            interpretation = "Highly concentrated market"
        elif hhi > 1500:
            concentration = "moderate"
            interpretation = "Moderately concentrated market"
        else:
            concentration = "low"
            interpretation = "Fragmented market"
        
        return {
            "concentration": concentration,
            "hhi": hhi,
            "interpretation": interpretation,
            "market_shares": market_shares
        }
    
    def _identify_competitive_threats(self, competitors: List[CompetitorProfile]) -> List[Dict[str, Any]]:
        """Identify competitive threats from analysis"""
        threats = []
        
        for competitor in competitors:
            threat_level = self._assess_threat_level(competitor)
            if threat_level in ["high", "medium"]:
                threats.append({
                    "competitor_name": competitor.name,
                    "threat_level": threat_level,
                    "threat_factors": [
                        "Large deal sizes" if competitor.key_metrics.get("deal_size", 0) > 40000 else None,
                        "High conversion rate" if competitor.key_metrics.get("conversion_rate", 0) > 3.0 else None,
                        "Premium positioning" if competitor.pricing_strategy == "premium" else None,
                        "Global presence" if "global presence" in competitor.strengths else None
                    ],
                    "recommended_response": "Monitor closely" if threat_level == "medium" else "Develop counter-strategy"
                })
        
        return threats
    
    def _generate_intelligence_recommendations(self, competitors: List[CompetitorProfile], industry: str) -> List[str]:
        """Generate recommendations based on competitive intelligence"""
        recommendations = []
        
        if not competitors:
            recommendations.append("Expand competitive intelligence gathering")
            return recommendations
        
        # Analyze competitive landscape
        landscape = self._analyze_competitive_landscape(competitors)
        
        if landscape["market_concentration"] == "high":
            recommendations.append("Focus on differentiation and unique value propositions")
        
        if landscape["market_concentration"] == "low":
            recommendations.append("Opportunity to consolidate market position")
        
        # Analyze pricing strategies
        pricing_strategies = landscape["pricing_strategies"]
        if pricing_strategies.get("premium", 0) > pricing_strategies.get("competitive", 0):
            recommendations.append("Consider competitive pricing strategy")
        else:
            recommendations.append("Premium positioning opportunity available")
        
        # Analyze market positions
        positions = landscape["market_positions"]
        if positions.get("niche_player", 0) > positions.get("market_leader", 0):
            recommendations.append("Opportunity to establish market leadership")
        
        return recommendations
    
    async def _monitor_website_changes(self, website: str) -> Dict[str, Any]:
        """Monitor competitor website for changes"""
        # Simplified monitoring
        return {
            "last_checked": datetime.utcnow().isoformat(),
            "changes_detected": False,
            "new_content": [],
            "pricing_updates": False,
            "feature_announcements": []
        }
    
    async def _monitor_social_media(self, social_media: Dict[str, str]) -> Dict[str, Any]:
        """Monitor competitor social media activity"""
        # Simplified monitoring
        return {
            "platforms_monitored": list(social_media.keys()),
            "recent_posts": 0,
            "engagement_rate": 0.0,
            "sentiment": "neutral",
            "key_topics": []
        }
    
    async def _monitor_pricing_changes(self, competitor: CompetitorProfile) -> Dict[str, Any]:
        """Monitor competitor pricing changes"""
        # Simplified monitoring
        return {
            "pricing_changes": False,
            "last_price_update": None,
            "price_direction": "stable",
            "affected_products": []
        }
    
    async def _monitor_announcements(self, competitor: CompetitorProfile) -> Dict[str, Any]:
        """Monitor competitor announcements and news"""
        # Simplified monitoring
        return {
            "recent_announcements": 0,
            "announcement_types": [],
            "key_announcements": []
        }
    
    async def _monitor_hiring_activity(self, competitor: CompetitorProfile) -> Dict[str, Any]:
        """Monitor competitor hiring activity"""
        # Simplified monitoring
        return {
            "active_job_postings": 0,
            "hiring_focus_areas": [],
            "expansion_indications": False
        }
    
    def _calculate_activity_score(self, website_changes: Dict, social_media: Dict, pricing_changes: Dict, announcements: Dict, hiring: Dict) -> float:
        """Calculate overall activity score"""
        score = 0.0
        
        if website_changes.get("changes_detected", False):
            score += 0.3
        
        if social_media.get("recent_posts", 0) > 5:
            score += 0.2
        
        if pricing_changes.get("pricing_changes", False):
            score += 0.3
        
        if announcements.get("recent_announcements", 0) > 0:
            score += 0.1
        
        if hiring.get("active_job_postings", 0) > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_activity_alerts(self, website_changes: Dict, social_media: Dict, pricing_changes: Dict, announcements: Dict, hiring: Dict) -> List[str]:
        """Generate alerts based on competitor activity"""
        alerts = []
        
        if website_changes.get("changes_detected", False):
            alerts.append("Website changes detected - review for strategic implications")
        
        if pricing_changes.get("pricing_changes", False):
            alerts.append("Pricing changes detected - assess competitive impact")
        
        if announcements.get("recent_announcements", 0) > 2:
            alerts.append("High announcement activity - monitor for new features or strategies")
        
        if hiring.get("active_job_postings", 0) > 5:
            alerts.append("Significant hiring activity - potential expansion or new initiatives")
        
        return alerts
