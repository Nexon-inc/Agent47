from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from ..models import JackieMarketResearch
from core.utils.nlp_utils import NLPUtils

class MarketResearchService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_utils = NLPUtils()

    def analyze_competitors(self, competitor_urls: List[str], analysis_type: str = "comprehensive") -> Dict[str, Any]:
        analysis_data = {
            "competitors": [],
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "market_position": {},
            "recommendations": []
        }
        
        for url in competitor_urls:
            competitor_analysis = self._analyze_single_competitor(url, analysis_type)
            analysis_data["competitors"].append(competitor_analysis)
        
        analysis_data["market_position"] = self._calculate_market_position(analysis_data["competitors"])
        analysis_data["recommendations"] = self._generate_competitor_recommendations(analysis_data)
        
        insights = self._extract_competitor_insights(analysis_data)
        
        research = MarketResearch(
            research_type="competitor_analysis",
            data=json.dumps(analysis_data),
            insights=json.dumps(insights),
            created_at=datetime.utcnow()
        )
        
        self.db.add(research)
        self.db.commit()
        self.db.refresh(research)
        
        return {
            "id": research.id,
            "data": analysis_data,
            "insights": insights,
            "created_at": research.created_at
        }

    def analyze_trends(self, industry: str, timeframe: str = "30d", keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        trend_data = {
            "industry": industry,
            "timeframe": timeframe,
            "trending_topics": [],
            "keyword_trends": {},
            "market_growth": {},
            "consumer_behavior": {},
            "technology_trends": [],
            "regulatory_changes": []
        }
        
        if keywords:
            for keyword in keywords:
                trend_data["keyword_trends"][keyword] = self._analyze_keyword_trend(keyword, timeframe)
        
        trend_data["trending_topics"] = self._get_trending_topics(industry, timeframe)
        trend_data["market_growth"] = self._analyze_market_growth(industry, timeframe)
        trend_data["consumer_behavior"] = self._analyze_consumer_behavior(industry, timeframe)
        trend_data["technology_trends"] = self._get_technology_trends(industry)
        trend_data["regulatory_changes"] = self._get_regulatory_changes(industry)
        
        insights = self._extract_trend_insights(trend_data)
        
        research = MarketResearch(
            research_type="trend_analysis",
            data=json.dumps(trend_data),
            insights=json.dumps(insights),
            created_at=datetime.utcnow()
        )
        
        self.db.add(research)
        self.db.commit()
        self.db.refresh(research)
        
        return {
            "id": research.id,
            "data": trend_data,
            "insights": insights,
            "created_at": research.created_at
        }

    def research_audience(self, target_demographics: dict, interests: List[str], platforms: List[str]) -> Dict[str, Any]:
        audience_data = {
            "demographics": target_demographics,
            "interests": interests,
            "platforms": platforms,
            "audience_size": {},
            "engagement_patterns": {},
            "content_preferences": {},
            "purchasing_behavior": {},
            "platform_analysis": {},
            "recommendations": []
        }
        
        for platform in platforms:
            platform_analysis = self._analyze_platform_audience(platform, target_demographics, interests)
            audience_data["platform_analysis"][platform] = platform_analysis
            audience_data["audience_size"][platform] = platform_analysis.get("audience_size", 0)
        
        audience_data["engagement_patterns"] = self._analyze_engagement_patterns(target_demographics, interests)
        audience_data["content_preferences"] = self._analyze_content_preferences(target_demographics, interests)
        audience_data["purchasing_behavior"] = self._analyze_purchasing_behavior(target_demographics, interests)
        audience_data["recommendations"] = self._generate_audience_recommendations(audience_data)
        
        insights = self._extract_audience_insights(audience_data)
        
        research = MarketResearch(
            research_type="audience_research",
            data=json.dumps(audience_data),
            insights=json.dumps(insights),
            created_at=datetime.utcnow()
        )
        
        self.db.add(research)
        self.db.commit()
        self.db.refresh(research)
        
        return {
            "id": research.id,
            "data": audience_data,
            "insights": insights,
            "created_at": research.created_at
        }

    def get_market_insights(self, market_segment: str, analysis_depth: str = "detailed") -> Dict[str, Any]:
        insights_data = {
            "market_segment": market_segment,
            "analysis_depth": analysis_depth,
            "market_size": {},
            "growth_rate": {},
            "competitive_landscape": {},
            "customer_segments": [],
            "value_propositions": [],
            "market_barriers": [],
            "opportunities": [],
            "risks": [],
            "forecast": {}
        }
        
        insights_data["market_size"] = self._analyze_market_size(market_segment)
        insights_data["growth_rate"] = self._analyze_growth_rate(market_segment)
        insights_data["competitive_landscape"] = self._analyze_competitive_landscape(market_segment)
        insights_data["customer_segments"] = self._identify_customer_segments(market_segment)
        insights_data["value_propositions"] = self._analyze_value_propositions(market_segment)
        insights_data["market_barriers"] = self._identify_market_barriers(market_segment)
        insights_data["opportunities"] = self._identify_opportunities(market_segment)
        insights_data["risks"] = self._identify_risks(market_segment)
        insights_data["forecast"] = self._generate_market_forecast(market_segment)
        
        insights = self._extract_market_insights(insights_data)
        
        research = MarketResearch(
            research_type="market_insights",
            data=json.dumps(insights_data),
            insights=json.dumps(insights),
            created_at=datetime.utcnow()
        )
        
        self.db.add(research)
        self.db.commit()
        self.db.refresh(research)
        
        return {
            "id": research.id,
            "data": insights_data,
            "insights": insights,
            "created_at": research.created_at
        }

    def get_research_by_id(self, research_id: int) -> Optional[Dict[str, Any]]:
        research = self.db.query(MarketResearch).filter(MarketResearch.id == research_id).first()
        if not research:
            return None
        
        return {
            "id": research.id,
            "research_type": research.research_type,
            "data": json.loads(research.data),
            "insights": json.loads(research.insights),
            "created_at": research.created_at
        }

    def list_research(self, research_type: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(MarketResearch)
        
        if research_type:
            query = query.filter(MarketResearch.research_type == research_type)
        
        research_list = query.order_by(desc(MarketResearch.created_at)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": research.id,
                "research_type": research.research_type,
                "data": json.loads(research.data),
                "insights": json.loads(research.insights),
                "created_at": research.created_at
            }
            for research in research_list
        ]

    def delete_research(self, research_id: int) -> bool:
        research = self.db.query(MarketResearch).filter(MarketResearch.id == research_id).first()
        if not research:
            return False
        
        self.db.delete(research)
        self.db.commit()
        return True

    def _analyze_single_competitor(self, url: str, analysis_type: str) -> Dict[str, Any]:
        return {
            "url": url,
            "domain_authority": 75,
            "traffic_volume": 50000,
            "content_quality": "high",
            "social_presence": "strong",
            "pricing_strategy": "competitive",
            "unique_selling_points": ["fast delivery", "quality products"],
            "weaknesses": ["limited product range", "high prices"]
        }

    def _calculate_market_position(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "market_share": 15.5,
            "competitive_advantage": "technology",
            "positioning": "premium",
            "differentiation": "customer service"
        }

    def _generate_competitor_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        return [
            "Focus on unique value propositions",
            "Improve customer service differentiation",
            "Expand product range strategically",
            "Optimize pricing for market position"
        ]

    def _extract_competitor_insights(self, analysis_data: Dict[str, Any]) -> List[str]:
        return [
            "Competitors focus on price competition",
            "Technology differentiation is key",
            "Customer service quality varies significantly",
            "Market consolidation opportunities exist"
        ]

    def _analyze_keyword_trend(self, keyword: str, timeframe: str) -> Dict[str, Any]:
        return {
            "keyword": keyword,
            "search_volume": 10000,
            "trend_direction": "increasing",
            "competition": "medium",
            "seasonality": "year-round"
        }

    def _get_trending_topics(self, industry: str, timeframe: str) -> List[str]:
        return [
            "sustainability",
            "digital transformation",
            "remote work",
            "e-commerce growth"
        ]

    def _analyze_market_growth(self, industry: str, timeframe: str) -> Dict[str, Any]:
        return {
            "growth_rate": 8.5,
            "market_size": 1500000000,
            "growth_drivers": ["technology", "consumer demand"],
            "growth_barriers": ["regulation", "competition"]
        }

    def _analyze_consumer_behavior(self, industry: str, timeframe: str) -> Dict[str, Any]:
        return {
            "preferences": ["convenience", "quality", "price"],
            "purchasing_patterns": "online-first",
            "brand_loyalty": "moderate",
            "decision_factors": ["reviews", "price", "convenience"]
        }

    def _get_technology_trends(self, industry: str) -> List[str]:
        return [
            "AI and machine learning",
            "Blockchain applications",
            "IoT integration",
            "Cloud computing"
        ]

    def _get_regulatory_changes(self, industry: str) -> List[str]:
        return [
            "Data privacy regulations",
            "Environmental compliance",
            "Consumer protection laws",
            "Industry-specific standards"
        ]

    def _extract_trend_insights(self, trend_data: Dict[str, Any]) -> List[str]:
        return [
            "Technology adoption is accelerating",
            "Consumer preferences are shifting online",
            "Sustainability is becoming a key differentiator",
            "Regulatory compliance is increasingly important"
        ]

    def _analyze_platform_audience(self, platform: str, demographics: dict, interests: List[str]) -> Dict[str, Any]:
        return {
            "platform": platform,
            "audience_size": 1000000,
            "engagement_rate": 3.2,
            "demographic_match": 85,
            "content_performance": "high",
            "ad_cost": 2.50
        }

    def _analyze_engagement_patterns(self, demographics: dict, interests: List[str]) -> Dict[str, Any]:
        return {
            "peak_hours": ["9-11am", "7-9pm"],
            "content_types": ["video", "images", "text"],
            "interaction_rate": 4.5,
            "sharing_behavior": "moderate"
        }

    def _analyze_content_preferences(self, demographics: dict, interests: List[str]) -> Dict[str, Any]:
        return {
            "preferred_formats": ["short video", "infographics"],
            "content_length": "medium",
            "tone_preference": "informative",
            "visual_elements": "important"
        }

    def _analyze_purchasing_behavior(self, demographics: dict, interests: List[str]) -> Dict[str, Any]:
        return {
            "purchase_frequency": "monthly",
            "average_order_value": 150,
            "decision_time": "1-3 days",
            "influencing_factors": ["reviews", "social proof"]
        }

    def _generate_audience_recommendations(self, audience_data: Dict[str, Any]) -> List[str]:
        return [
            "Focus on video content for higher engagement",
            "Target peak hours for maximum reach",
            "Use social proof in marketing materials",
            "Optimize for mobile experience"
        ]

    def _extract_audience_insights(self, audience_data: Dict[str, Any]) -> List[str]:
        return [
            "Video content performs 40% better than text",
            "Mobile users prefer shorter content",
            "Social proof increases conversion by 25%",
            "Peak engagement occurs during commute hours"
        ]

    def _analyze_market_size(self, market_segment: str) -> Dict[str, Any]:
        return {
            "total_addressable_market": 5000000000,
            "serviceable_addressable_market": 1000000000,
            "serviceable_obtainable_market": 100000000,
            "current_market_share": 2.5
        }

    def _analyze_growth_rate(self, market_segment: str) -> Dict[str, Any]:
        return {
            "annual_growth_rate": 12.5,
            "compound_annual_growth_rate": 15.2,
            "growth_projections": {
                "year_1": 12.5,
                "year_2": 14.0,
                "year_3": 16.5
            }
        }

    def _analyze_competitive_landscape(self, market_segment: str) -> Dict[str, Any]:
        return {
            "competitor_count": 25,
            "market_concentration": "fragmented",
            "barriers_to_entry": "medium",
            "competitive_intensity": "high"
        }

    def _identify_customer_segments(self, market_segment: str) -> List[Dict[str, Any]]:
        return [
            {
                "segment": "early_adopters",
                "size": 5000000,
                "characteristics": ["tech-savvy", "high-income"],
                "value_proposition": "innovation"
            },
            {
                "segment": "mainstream_users",
                "size": 25000000,
                "characteristics": ["practical", "price-conscious"],
                "value_proposition": "reliability"
            }
        ]

    def _analyze_value_propositions(self, market_segment: str) -> List[str]:
        return [
            "Superior technology and innovation",
            "Exceptional customer service",
            "Competitive pricing",
            "Comprehensive solution"
        ]

    def _identify_market_barriers(self, market_segment: str) -> List[str]:
        return [
            "High initial investment",
            "Regulatory compliance",
            "Established competitors",
            "Customer switching costs"
        ]

    def _identify_opportunities(self, market_segment: str) -> List[str]:
        return [
            "Emerging technology adoption",
            "Market consolidation",
            "International expansion",
            "Product diversification"
        ]

    def _identify_risks(self, market_segment: str) -> List[str]:
        return [
            "Economic downturn",
            "Technology disruption",
            "Regulatory changes",
            "Competitive pressure"
        ]

    def _generate_market_forecast(self, market_segment: str) -> Dict[str, Any]:
        return {
            "short_term": {
                "growth_rate": 8.5,
                "market_size": 1100000000,
                "key_drivers": ["digital adoption", "consumer demand"]
            },
            "medium_term": {
                "growth_rate": 12.0,
                "market_size": 1400000000,
                "key_drivers": ["technology advancement", "market expansion"]
            },
            "long_term": {
                "growth_rate": 15.5,
                "market_size": 2000000000,
                "key_drivers": ["global expansion", "innovation"]
            }
        }

    def _extract_market_insights(self, insights_data: Dict[str, Any]) -> List[str]:
        return [
            "Market is growing at 12.5% annually",
            "Competition is fragmented with opportunity for consolidation",
            "Technology innovation is the key differentiator",
            "International expansion presents significant opportunity"
        ]
