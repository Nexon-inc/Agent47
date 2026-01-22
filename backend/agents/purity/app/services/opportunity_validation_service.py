from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import PurityBusinessIdea, PurityOpportunityValidation, PurityBusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class OpportunityValidationService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def validate_business_opportunity(
        self,
        db: AsyncSession,
        business_idea: str,
        target_market: str,
        market_data: Dict[str, Any],
        seo_trends: Dict[str, Any],
        competitor_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            cache_key = f"opportunity_validation:{business_idea[:50]}:{target_market}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_validation_prompt(
                business_idea, target_market, market_data, seo_trends, competitor_analysis
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that validates business opportunities. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            validation_data = json.loads(ai_response)
            
            opportunity_validation = {
                "id": f"validation_{business_idea[:30]}",
                "business_idea": business_idea,
                "target_market": target_market,
                "market_data": market_data,
                "seo_trends": seo_trends,
                "competitor_analysis": competitor_analysis,
                "validation_score": validation_data.get("validation_score", 0.0),
                "market_viability": validation_data.get("market_viability", {}),
                "competitive_analysis": validation_data.get("competitive_analysis", {}),
                "seo_opportunity": validation_data.get("seo_opportunity", {}),
                "risk_assessment": validation_data.get("risk_assessment", []),
                "recommendations": validation_data.get("recommendations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(validation_data), expire=3600)
            await self.event_bus.publish("purity.opportunity_validated", {
                "business_idea": business_idea[:50],
                "target_market": target_market,
                "validation_score": opportunity_validation["validation_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return opportunity_validation
            
        except Exception as e:
            raise e
    
    async def analyze_market_data(
        self,
        db: AsyncSession,
        market_segment: str,
        geographic_region: str,
        time_period: str,
        data_sources: List[str]
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_market_analysis_prompt(
                market_segment, geographic_region, time_period, data_sources
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that validates business opportunities. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            market_data = json.loads(ai_response)
            
            market_analysis = {
                "id": f"market_analysis:{market_segment}:{geographic_region}",
                "market_segment": market_segment,
                "geographic_region": geographic_region,
                "time_period": time_period,
                "data_sources": data_sources,
                "market_size": market_data.get("market_size", {}),
                "growth_trends": market_data.get("growth_trends", {}),
                "customer_demographics": market_data.get("customer_demographics", {}),
                "market_dynamics": market_data.get("market_dynamics", {}),
                "opportunity_indicators": market_data.get("opportunity_indicators", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.market_data_analyzed", {
                "market_segment": market_segment,
                "geographic_region": geographic_region,
                "time_period": time_period,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return market_analysis
            
        except Exception as e:
            raise e
    
    async def analyze_seo_trends(
        self,
        db: AsyncSession,
        keywords: List[str],
        industry: str,
        search_volume_data: Dict[str, Any],
        competition_level: str
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_seo_analysis_prompt(
                keywords, industry, search_volume_data, competition_level
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that validates business opportunities. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            seo_data = json.loads(ai_response)
            
            seo_analysis = {
                "id": f"seo_analysis:{industry}:{len(keywords)}_keywords",
                "keywords": keywords,
                "industry": industry,
                "search_volume_data": search_volume_data,
                "competition_level": competition_level,
                "keyword_opportunities": seo_data.get("keyword_opportunities", []),
                "search_trends": seo_data.get("search_trends", {}),
                "content_gaps": seo_data.get("content_gaps", []),
                "ranking_potential": seo_data.get("ranking_potential", {}),
                "seo_strategy": seo_data.get("seo_strategy", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.seo_trends_analyzed", {
                "industry": industry,
                "keyword_count": len(keywords),
                "competition_level": competition_level,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return seo_analysis
            
        except Exception as e:
            raise e
    
    async def conduct_competitor_analysis(
        self,
        db: AsyncSession,
        competitors: List[str],
        analysis_depth: str,
        competitive_metrics: Dict[str, Any],
        market_position: str
    ) -> Dict[str, Any]:
        try:
            prompt = self._create_competitor_analysis_prompt(
                competitors, analysis_depth, competitive_metrics, market_position
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that validates business opportunities. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            competitor_data = json.loads(ai_response)
            
            competitor_analysis = {
                "id": f"competitor_analysis:{len(competitors)}_competitors",
                "competitors": competitors,
                "analysis_depth": analysis_depth,
                "competitive_metrics": competitive_metrics,
                "market_position": market_position,
                "competitor_profiles": competitor_data.get("competitor_profiles", []),
                "competitive_landscape": competitor_data.get("competitive_landscape", {}),
                "market_share_analysis": competitor_data.get("market_share_analysis", {}),
                "competitive_advantages": competitor_data.get("competitive_advantages", []),
                "differentiation_opportunities": competitor_data.get("differentiation_opportunities", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.competitor_analysis_conducted", {
                "competitor_count": len(competitors),
                "analysis_depth": analysis_depth,
                "market_position": market_position,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return competitor_analysis
            
        except Exception as e:
            raise e
    
    def _create_validation_prompt(
        self,
        business_idea: str,
        target_market: str,
        market_data: Dict[str, Any],
        seo_trends: Dict[str, Any],
        competitor_analysis: Dict[str, Any]
    ) -> str:
        return f"""
        Validate business opportunity for:
        - Business Idea: {business_idea}
        - Target Market: {target_market}
        - Market Data: {market_data}
        - SEO Trends: {seo_trends}
        - Competitor Analysis: {competitor_analysis}
        
        Provide comprehensive opportunity validation including:
        1. Overall validation score (0-100)
        2. Market viability assessment
        3. Competitive analysis
        4. SEO opportunity analysis
        5. Risk assessment
        6. Strategic recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "validation_score": 85.5,
            "market_viability": {{
                "market_size_score": 90.0,
                "growth_potential_score": 85.0,
                "customer_demand_score": 80.0,
                "market_barriers_score": 75.0,
                "overall_viability": "High"
            }},
            "competitive_analysis": {{
                "competitor_count": "Moderate",
                "competitive_intensity": "Medium",
                "market_share_opportunity": "High",
                "differentiation_potential": "Strong",
                "competitive_advantages": ["Advantage 1", "Advantage 2"]
            }},
            "seo_opportunity": {{
                "keyword_opportunities": ["Opportunity 1", "Opportunity 2"],
                "search_volume": "High",
                "competition_level": "Moderate",
                "content_gaps": ["Gap 1", "Gap 2"],
                "ranking_potential": "Strong"
            }},
            "risk_assessment": [
                "Risk 1: Market saturation",
                "Risk 2: Regulatory changes",
                "Risk 3: Technology disruption"
            ],
            "recommendations": [
                "Recommendation 1: Focus on differentiation",
                "Recommendation 2: Develop strong SEO strategy",
                "Recommendation 3: Build competitive advantages"
            ]
        }}
        """
    
    def _create_market_analysis_prompt(
        self,
        market_segment: str,
        geographic_region: str,
        time_period: str,
        data_sources: List[str]
    ) -> str:
        return f"""
        Analyze market data for:
        - Market Segment: {market_segment}
        - Geographic Region: {geographic_region}
        - Time Period: {time_period}
        - Data Sources: {', '.join(data_sources)}
        
        Provide comprehensive market analysis including:
        1. Market size and growth
        2. Growth trends and projections
        3. Customer demographics
        4. Market dynamics
        5. Opportunity indicators
        
        Return the response as a JSON object with the following structure:
        {{
            "market_size": {{
                "current_size": "$10B",
                "projected_size": "$15B",
                "growth_rate": "50%",
                "market_maturity": "Growing"
            }},
            "growth_trends": {{
                "historical_growth": "25% annually",
                "projected_growth": "30% annually",
                "growth_drivers": ["Driver 1", "Driver 2"],
                "growth_barriers": ["Barrier 1", "Barrier 2"]
            }},
            "customer_demographics": {{
                "age_groups": ["25-34", "35-44"],
                "income_levels": ["$50K-$100K", "$100K+"],
                "geographic_distribution": "Urban areas",
                "behavioral_patterns": ["Pattern 1", "Pattern 2"]
            }},
            "market_dynamics": {{
                "supply_chain": "Supply chain analysis",
                "distribution_channels": "Channel analysis",
                "pricing_trends": "Pricing analysis",
                "regulatory_environment": "Regulatory analysis"
            }},
            "opportunity_indicators": [
                "Indicator 1: Growing demand",
                "Indicator 2: Technology adoption",
                "Indicator 3: Market gaps",
                "Indicator 4: Customer pain points"
            ]
        }}
        """
    
    def _create_seo_analysis_prompt(
        self,
        keywords: List[str],
        industry: str,
        search_volume_data: Dict[str, Any],
        competition_level: str
    ) -> str:
        return f"""
        Analyze SEO trends for:
        - Keywords: {', '.join(keywords)}
        - Industry: {industry}
        - Search Volume Data: {search_volume_data}
        - Competition Level: {competition_level}
        
        Provide comprehensive SEO analysis including:
        1. Keyword opportunities
        2. Search trends
        3. Content gaps
        4. Ranking potential
        5. SEO strategy recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "keyword_opportunities": [
                {{
                    "keyword": "Keyword 1",
                    "search_volume": "10K monthly",
                    "competition": "Low",
                    "opportunity_score": 85.0,
                    "content_gaps": ["Gap 1", "Gap 2"]
                }}
            ],
            "search_trends": {{
                "trending_keywords": ["Trend 1", "Trend 2"],
                "seasonal_patterns": "Seasonal analysis",
                "growth_keywords": ["Growth 1", "Growth 2"],
                "declining_keywords": ["Decline 1", "Decline 2"]
            }},
            "content_gaps": [
                {{
                    "topic": "Topic 1",
                    "search_volume": "5K monthly",
                    "competition": "Low",
                    "content_opportunity": "High"
                }}
            ],
            "ranking_potential": {{
                "high_potential_keywords": ["Keyword 1", "Keyword 2"],
                "medium_potential_keywords": ["Keyword 3", "Keyword 4"],
                "low_potential_keywords": ["Keyword 5", "Keyword 6"],
                "ranking_timeline": "6-12 months"
            }},
            "seo_strategy": {{
                "content_strategy": "Content strategy recommendations",
                "technical_seo": "Technical SEO recommendations",
                "link_building": "Link building strategy",
                "local_seo": "Local SEO strategy"
            }}
        }}
        """
    
    def _create_competitor_analysis_prompt(
        self,
        competitors: List[str],
        analysis_depth: str,
        competitive_metrics: Dict[str, Any],
        market_position: str
    ) -> str:
        return f"""
        Conduct competitor analysis for:
        - Competitors: {', '.join(competitors)}
        - Analysis Depth: {analysis_depth}
        - Competitive Metrics: {competitive_metrics}
        - Market Position: {market_position}
        
        Provide comprehensive competitor analysis including:
        1. Competitor profiles
        2. Competitive landscape
        3. Market share analysis
        4. Competitive advantages
        5. Differentiation opportunities
        
        Return the response as a JSON object with the following structure:
        {{
            "competitor_profiles": [
                {{
                    "name": "Competitor 1",
                    "market_share": "25%",
                    "strengths": ["Strength 1", "Strength 2"],
                    "weaknesses": ["Weakness 1", "Weakness 2"],
                    "strategies": ["Strategy 1", "Strategy 2"]
                }}
            ],
            "competitive_landscape": {{
                "market_leader": "Leader name",
                "market_followers": ["Follower 1", "Follower 2"],
                "niche_players": ["Niche 1", "Niche 2"],
                "competitive_intensity": "High/Medium/Low"
            }},
            "market_share_analysis": {{
                "total_market_size": "$100B",
                "market_share_distribution": {{
                    "leader": "30%",
                    "followers": "45%",
                    "niche": "15%",
                    "others": "10%"
                }},
                "market_share_opportunity": "15-20%"
            }},
            "competitive_advantages": [
                "Advantage 1: Technology superiority",
                "Advantage 2: Customer service excellence",
                "Advantage 3: Cost leadership"
            ],
            "differentiation_opportunities": [
                "Opportunity 1: Unique value proposition",
                "Opportunity 2: Market gap exploitation",
                "Opportunity 3: Innovation leadership"
            ]
        }}
        """
