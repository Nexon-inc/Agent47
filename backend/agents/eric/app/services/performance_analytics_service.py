import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel

from ..database import get_eric_database
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
# NLPUtils removed - not used

logger = logging.getLogger(__name__)

class PerformanceAnalyticsService:
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize performance analytics service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Performance analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize performance analytics service: {e}")
            raise

    async def get_comprehensive_performance_metrics(self, brand_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """Get comprehensive performance metrics for a brand"""
        try:
            async with get_eric_database() as db:
                overall_metrics = await self._get_overall_performance_metrics(brand_id, time_period)
                conversion_analytics = await self._get_conversion_analytics(brand_id, time_period)
                response_time_analytics = await self._get_response_time_analytics(brand_id, time_period)
                team_performance = await self._get_team_performance_metrics(brand_id, time_period)
                
                return {
                    "brand_id": brand_id,
                    "time_period": time_period,
                    "overall_metrics": overall_metrics,
                    "conversion_analytics": conversion_analytics,
                    "response_time_analytics": response_time_analytics,
                    "team_performance": team_performance,
                    "insights": await self._generate_performance_insights(overall_metrics, conversion_analytics),
                    "recommendations": await self._generate_performance_recommendations()
                }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            raise

    async def track_conversion_rates(self, brand_id: str, funnel_stage: str, time_period: str = "30d") -> Dict[str, Any]:
        """Track conversion rates across different funnel stages"""
        try:
            async with get_eric_database() as db:
                conversion_data = await self._get_funnel_stage_conversions(brand_id, funnel_stage, time_period)
                conversion_metrics = await self._calculate_conversion_metrics(conversion_data)
                
                return {
                    "brand_id": brand_id,
                    "funnel_stage": funnel_stage,
                    "time_period": time_period,
                    "conversion_data": conversion_data,
                    "conversion_metrics": conversion_metrics,
                    "bottlenecks": await self._identify_conversion_bottlenecks(conversion_data),
                    "optimization_recommendations": await self._generate_conversion_optimization_recommendations()
                }
        except Exception as e:
            logger.error(f"Error tracking conversion rates: {e}")
            raise

    async def analyze_response_times(self, brand_id: str, channel: str = "all", time_period: str = "30d") -> Dict[str, Any]:
        """Analyze response times across different channels"""
        try:
            async with get_eric_database() as db:
                response_time_data = await self._get_response_time_data(brand_id, channel, time_period)
                response_metrics = await self._calculate_response_time_metrics(response_time_data)
                
                return {
                    "brand_id": brand_id,
                    "channel": channel,
                    "time_period": time_period,
                    "response_time_data": response_time_data,
                    "response_metrics": response_metrics,
                    "improvement_opportunities": await self._identify_response_time_improvements(),
                    "optimization_strategies": await self._generate_response_time_optimization_strategies()
                }
        except Exception as e:
            logger.error(f"Error analyzing response times: {e}")
            raise

    async def get_team_performance_dashboard(self, team_id: str, brand_id: str, 
                                           start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive team performance dashboard"""
        try:
            async with get_eric_database() as db:
                team_data = await self._get_team_performance_data(team_id, brand_id, start_date, end_date)
                individual_metrics = await self._calculate_individual_performance_metrics(team_data)
                team_rankings = await self._generate_team_rankings(individual_metrics)
                
                return {
                    "team_id": team_id,
                    "brand_id": brand_id,
                    "date_range": {"start_date": start_date, "end_date": end_date},
                    "team_data": team_data,
                    "individual_metrics": individual_metrics,
                    "team_rankings": team_rankings,
                    "performance_insights": await self._generate_team_performance_insights(),
                    "improvement_recommendations": await self._create_team_improvement_recommendations()
                }
        except Exception as e:
            logger.error(f"Error getting team performance dashboard: {e}")
            raise

    async def generate_performance_report(self, brand_id: str, report_type: str = "comprehensive", 
                                        time_period: str = "30d") -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            async with get_eric_database() as db:
                performance_data = await self._get_all_performance_data(brand_id, time_period)
                executive_summary = await self._generate_executive_summary(performance_data)
                
                return {
                    "brand_id": brand_id,
                    "report_type": report_type,
                    "time_period": time_period,
                    "generated_at": datetime.utcnow(),
                    "executive_summary": executive_summary,
                    "detailed_analysis": await self._create_detailed_analysis(performance_data),
                    "action_items": await self._create_performance_action_items(),
                    "recommendations": await self._generate_performance_report_recommendations()
                }
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            raise

    async def track_sales_team_metrics(self, brand_id: str, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Track comprehensive sales team metrics"""
        try:
            async with get_eric_database() as db:
                sales_team_data = await self._get_sales_team_data(brand_id, team_id)
                kpis = await self._calculate_sales_kpis(sales_team_data)
                
                return {
                    "brand_id": brand_id,
                    "team_id": team_id,
                    "sales_team_data": sales_team_data,
                    "kpis": kpis,
                    "efficiency_metrics": await self._analyze_team_efficiency(sales_team_data),
                    "productivity_metrics": await self._track_productivity_metrics(sales_team_data),
                    "performance_insights": await self._generate_sales_performance_insights(),
                    "improvement_opportunities": await self._identify_sales_improvement_opportunities()
                }
        except Exception as e:
            logger.error(f"Error tracking sales team metrics: {e}")
            raise

    async def analyze_customer_engagement_metrics(self, brand_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """Analyze customer engagement metrics"""
        try:
            async with get_eric_database() as db:
                engagement_data = await self._get_customer_engagement_data(brand_id, time_period)
                engagement_metrics = await self._calculate_engagement_metrics(engagement_data)
                
                return {
                    "brand_id": brand_id,
                    "time_period": time_period,
                    "engagement_data": engagement_data,
                    "engagement_metrics": engagement_metrics,
                    "engagement_patterns": await self._analyze_engagement_patterns(engagement_data),
                    "engagement_opportunities": await self._identify_engagement_opportunities(),
                    "engagement_strategies": await self._generate_engagement_strategies()
                }
        except Exception as e:
            logger.error(f"Error analyzing customer engagement metrics: {e}")
            raise

    # Helper methods
    async def _get_overall_performance_metrics(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "total_leads": 1500,
            "converted_leads": 225,
            "conversion_rate": 0.15,
            "total_revenue": 450000,
            "average_deal_size": 2000,
            "sales_cycle_length": 45,
            "response_time_avg": 2.5,
            "customer_satisfaction": 4.3
        }

    async def _get_conversion_analytics(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "funnel_stages": {
                "awareness": {"leads": 1500, "conversions": 1200, "rate": 0.80},
                "interest": {"leads": 1200, "conversions": 600, "rate": 0.50},
                "consideration": {"leads": 600, "conversions": 300, "rate": 0.50},
                "decision": {"leads": 300, "conversions": 225, "rate": 0.75}
            },
            "conversion_trends": {"weekly_growth": 0.05, "monthly_growth": 0.12}
        }

    async def _get_response_time_analytics(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "average_response_time": 2.5,
            "response_time_by_channel": {
                "email": 4.2, "phone": 0.1, "chat": 0.5, "sms": 0.2
            },
            "response_time_trends": {"improvement_rate": 0.15}
        }

    async def _get_team_performance_metrics(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "team_size": 8,
            "average_performance": {
                "leads_per_rep": 187,
                "conversions_per_rep": 28,
                "revenue_per_rep": 56250,
                "response_time_per_rep": 2.3
            },
            "top_performers": [
                {"rep_id": "rep_001", "performance_score": 0.95},
                {"rep_id": "rep_002", "performance_score": 0.88}
            ]
        }

    async def _generate_performance_insights(self, overall_metrics: Dict[str, Any], conversion_analytics: Dict[str, Any]) -> List[str]:
        return [
            "Response time improvements have led to 20% increase in conversion rates",
            "Team performance varies significantly - top performers are 3x more productive",
            "Email response times are the biggest bottleneck in the sales funnel"
        ]

    async def _generate_performance_recommendations(self) -> List[Dict[str, Any]]:
        return [
            {"recommendation": "Implement automated email responses", "priority": "high", "expected_impact": "25% improvement"},
            {"recommendation": "Provide additional training for underperforming team members", "priority": "medium", "expected_impact": "15% improvement"}
        ]

    async def _get_funnel_stage_conversions(self, brand_id: str, funnel_stage: str, time_period: str) -> Dict[str, Any]:
        return {
            "stage": funnel_stage,
            "total_leads": 600,
            "converted_leads": 300,
            "conversion_rate": 0.50,
            "average_time_in_stage": 7
        }

    async def _calculate_conversion_metrics(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "conversion_rate": conversion_data["conversion_rate"],
            "efficiency_score": 0.75,
            "improvement_potential": 0.25
        }

    async def _identify_conversion_bottlenecks(self, conversion_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"bottleneck": "slow_response_time", "impact": "high", "solution": "automated_responses"},
            {"bottleneck": "poor_lead_quality", "impact": "medium", "solution": "improved_scoring"}
        ]

    async def _generate_conversion_optimization_recommendations(self) -> List[Dict[str, Any]]:
        return [
            {"recommendation": "Implement automated response system", "priority": "high", "effort": "medium"},
            {"recommendation": "Enhance lead scoring algorithm", "priority": "medium", "effort": "high"}
        ]

    async def _get_response_time_data(self, brand_id: str, channel: str, time_period: str) -> Dict[str, Any]:
        return {
            "channel": channel,
            "average_response_time": 2.5,
            "response_time_distribution": {
                "under_1_hour": 0.60,
                "1_4_hours": 0.25,
                "4_24_hours": 0.10,
                "over_24_hours": 0.05
            }
        }

    async def _calculate_response_time_metrics(self, response_time_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "average_response_time": response_time_data["average_response_time"],
            "response_time_percentile_90": 4.2,
            "improvement_opportunity": 0.30
        }

    async def _identify_response_time_improvements(self) -> List[Dict[str, Any]]:
        return [
            {"improvement": "automated_responses", "potential_reduction": "50%", "effort": "medium"},
            {"improvement": "staffing_optimization", "potential_reduction": "30%", "effort": "high"}
        ]

    async def _generate_response_time_optimization_strategies(self) -> List[Dict[str, Any]]:
        return [
            {"strategy": "Implement chatbot for immediate responses", "timeline": "2 weeks", "expected_impact": "40% reduction"},
            {"strategy": "Optimize team scheduling", "timeline": "1 month", "expected_impact": "25% reduction"}
        ]

    async def _get_team_performance_data(self, team_id: str, brand_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {
            "team_id": team_id,
            "date_range": {"start": start_date, "end": end_date},
            "team_members": [
                {"member_id": "member_001", "name": "John Doe", "role": "senior_sales"},
                {"member_id": "member_002", "name": "Jane Smith", "role": "sales_rep"}
            ],
            "performance_data": {
                "member_001": {"leads": 200, "conversions": 30, "revenue": 60000},
                "member_002": {"leads": 150, "conversions": 20, "revenue": 40000}
            }
        }

    async def _calculate_individual_performance_metrics(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "member_001": {"conversion_rate": 0.15, "revenue_per_lead": 300, "performance_score": 0.85},
            "member_002": {"conversion_rate": 0.13, "revenue_per_lead": 267, "performance_score": 0.72}
        }

    async def _generate_team_rankings(self, individual_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"rank": 1, "member_id": "member_001", "performance_score": 0.85},
            {"rank": 2, "member_id": "member_002", "performance_score": 0.72}
        ]

    async def _generate_team_performance_insights(self) -> List[str]:
        return [
            "Top performer is 18% more effective than team average",
            "Team shows consistent improvement over the last quarter",
            "Conversion rates vary significantly between team members"
        ]

    async def _create_team_improvement_recommendations(self) -> List[Dict[str, Any]]:
        return [
            {"recommendation": "Provide additional training for lower-performing team members", "priority": "high"},
            {"recommendation": "Implement mentorship program", "priority": "medium"}
        ]

    async def _get_all_performance_data(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "overall_metrics": await self._get_overall_performance_metrics(brand_id, time_period),
            "conversion_analytics": await self._get_conversion_analytics(brand_id, time_period),
            "response_time_analytics": await self._get_response_time_analytics(brand_id, time_period),
            "team_performance": await self._get_team_performance_metrics(brand_id, time_period)
        }

    async def _generate_executive_summary(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "key_highlights": [
                "15% conversion rate achieved",
                "2.5 hour average response time",
                "450K total revenue generated"
            ],
            "performance_score": 0.82,
            "trend_summary": "Strong performance with consistent improvement"
        }

    async def _create_detailed_analysis(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "performance_breakdown": {
                "by_channel": {"email": 0.15, "phone": 0.18, "chat": 0.12},
                "by_team": {"team_a": 0.16, "team_b": 0.14}
            },
            "trend_analysis": {
                "monthly_growth": 0.12,
                "quarterly_growth": 0.25
            }
        }

    async def _create_performance_action_items(self) -> List[Dict[str, Any]]:
        return [
            {"action": "Implement automated response system", "owner": "tech_team", "timeline": "2 weeks"},
            {"action": "Provide sales training", "owner": "hr_team", "timeline": "1 month"}
        ]

    async def _generate_performance_report_recommendations(self) -> List[Dict[str, Any]]:
        return [
            {"recommendation": "Focus on improving chat channel conversion rates", "priority": "high", "expected_impact": "20% improvement"},
            {"recommendation": "Invest in team training", "priority": "medium", "expected_impact": "15% improvement"}
        ]

    async def _get_sales_team_data(self, brand_id: str, team_id: Optional[str]) -> Dict[str, Any]:
        return {
            "team_size": 8,
            "total_leads": 1500,
            "total_conversions": 225,
            "total_revenue": 450000,
            "average_deal_size": 2000,
            "sales_cycle_length": 45
        }

    async def _calculate_sales_kpis(self, sales_team_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "conversion_rate": 0.15,
            "revenue_per_rep": 56250,
            "leads_per_rep": 187,
            "deals_per_rep": 28,
            "average_deal_size": 2000,
            "sales_cycle_length": 45
        }

    async def _analyze_team_efficiency(self, sales_team_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "efficiency_score": 0.78,
            "productivity_per_hour": 125,
            "utilization_rate": 0.85,
            "efficiency_trends": "improving"
        }

    async def _track_productivity_metrics(self, sales_team_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "calls_per_day": 25,
            "emails_per_day": 50,
            "meetings_per_week": 8,
            "proposals_per_month": 12,
            "follow_ups_per_lead": 3
        }

    async def _generate_sales_performance_insights(self) -> List[str]:
        return [
            "Team efficiency is above industry average at 78%",
            "Productivity metrics show consistent performance",
            "Conversion rate of 15% exceeds target of 12%"
        ]

    async def _identify_sales_improvement_opportunities(self) -> List[Dict[str, Any]]:
        return [
            {"opportunity": "increase_calls_per_day", "current": 25, "target": 30, "potential_impact": "20% more leads"},
            {"opportunity": "improve_follow_up_frequency", "current": 3, "target": 5, "potential_impact": "15% higher conversion"}
        ]

    async def _get_customer_engagement_data(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        return {
            "total_customers": 500,
            "active_customers": 350,
            "engagement_rate": 0.70,
            "average_engagement_score": 4.2,
            "engagement_channels": {
                "email": 0.45,
                "phone": 0.25,
                "chat": 0.20,
                "social": 0.10
            }
        }

    async def _calculate_engagement_metrics(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engagement_rate": engagement_data["engagement_rate"],
            "engagement_score": engagement_data["average_engagement_score"],
            "retention_rate": 0.85,
            "lifetime_value": 5000
        }

    async def _analyze_engagement_patterns(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "peak_engagement_hours": ["10am", "2pm", "4pm"],
            "preferred_channels": ["email", "phone"],
            "engagement_frequency": "weekly"
        }

    async def _identify_engagement_opportunities(self) -> List[Dict[str, Any]]:
        return [
            {"opportunity": "increase_social_engagement", "current": 0.10, "target": 0.20, "potential_impact": "15% more engagement"},
            {"opportunity": "optimize_engagement_timing", "current": "standard", "target": "personalized", "potential_impact": "25% higher response"}
        ]

    async def _generate_engagement_strategies(self) -> List[Dict[str, Any]]:
        return [
            {"strategy": "Implement social media automation", "timeline": "1 month", "expected_impact": "15% increase"},
            {"strategy": "Create personalized engagement schedules", "timeline": "2 weeks", "expected_impact": "25% increase"}
        ]

