from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessHealth, BusinessModel, FinancialForecast
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class BusinessHealthService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_business_health_dashboard(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_revenue: float,
        current_costs: float,
        customer_count: int,
        conversion_rate: float,
        churn_rate: float,
        growth_rate: float
    ) -> BusinessHealth:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"business_health:{business_idea_id}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_business_health_prompt(
                business_idea, current_revenue, current_costs, customer_count,
                conversion_rate, churn_rate, growth_rate
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes business health. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            health_data = json.loads(ai_response)
            
            business_health = BusinessHealth(
                business_idea_id=business_idea_id,
                current_revenue=current_revenue,
                current_costs=current_costs,
                customer_count=customer_count,
                conversion_rate=conversion_rate,
                churn_rate=churn_rate,
                growth_rate=growth_rate,
                kpi_metrics=json.dumps(health_data.get("kpi_metrics", {})),
                health_score=health_data.get("health_score", 0.0),
                performance_indicators=json.dumps(health_data.get("performance_indicators", [])),
                risk_factors=json.dumps(health_data.get("risk_factors", [])),
                improvement_recommendations=json.dumps(health_data.get("improvement_recommendations", [])),
                trend_analysis=health_data.get("trend_analysis", "")
            )
            
            db.add(business_health)
            await db.commit()
            await db.refresh(business_health)
            
            await self.redis_manager.set(cache_key, json.dumps(health_data), expire=3600)
            await self.event_bus.publish("purity.business_health_created", {
                "business_idea_id": business_idea_id,
                "health_score": business_health.health_score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_health
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def track_kpi_metrics(
        self,
        db: AsyncSession,
        business_health_id: int,
        metrics_data: Dict[str, Any],
        tracking_period: str
    ) -> Dict[str, Any]:
        try:
            health_result = await db.execute(
                select(BusinessHealth).where(BusinessHealth.id == business_health_id)
            )
            business_health = health_result.scalar_one_or_none()
            if not business_health:
                raise ValueError("Business health record not found")
            
            prompt = self._create_kpi_tracking_prompt(
                business_health, metrics_data, tracking_period
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes business health. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            tracking_data = json.loads(ai_response)
            
            kpi_tracking = {
                "id": business_health_id,
                "business_health_id": business_health_id,
                "tracking_period": tracking_period,
                "metrics_data": metrics_data,
                "kpi_analysis": tracking_data.get("kpi_analysis", {}),
                "performance_trends": tracking_data.get("performance_trends", []),
                "anomaly_detection": tracking_data.get("anomaly_detection", []),
                "action_items": tracking_data.get("action_items", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.kpi_metrics_tracked", {
                "business_health_id": business_health_id,
                "tracking_period": tracking_period,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return kpi_tracking
            
        except Exception as e:
            raise e
    
    async def generate_health_report(
        self,
        db: AsyncSession,
        business_health_id: int,
        report_type: str,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        try:
            health_result = await db.execute(
                select(BusinessHealth).where(BusinessHealth.id == business_health_id)
            )
            business_health = health_result.scalar_one_or_none()
            if not business_health:
                raise ValueError("Business health record not found")
            
            prompt = self._create_health_report_prompt(
                business_health, report_type, include_recommendations
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes business health. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            report_data = json.loads(ai_response)
            
            health_report = {
                "id": business_health_id,
                "business_health_id": business_health_id,
                "report_type": report_type,
                "include_recommendations": include_recommendations,
                "executive_summary": report_data.get("executive_summary", ""),
                "detailed_analysis": report_data.get("detailed_analysis", ""),
                "key_findings": report_data.get("key_findings", []),
                "recommendations": report_data.get("recommendations", []),
                "action_plan": report_data.get("action_plan", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.health_report_generated", {
                "business_health_id": business_health_id,
                "report_type": report_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return health_report
            
        except Exception as e:
            raise e
    
    async def update_business_health(
        self,
        db: AsyncSession,
        health_id: int,
        current_revenue: float,
        current_costs: float,
        customer_count: int,
        conversion_rate: float,
        churn_rate: float,
        growth_rate: float
    ) -> BusinessHealth:
        try:
            result = await db.execute(
                select(BusinessHealth).where(BusinessHealth.id == health_id)
            )
            business_health = result.scalar_one_or_none()
            if not business_health:
                raise ValueError("Business health record not found")
            
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_health.business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            
            prompt = self._create_business_health_prompt(
                business_idea, current_revenue, current_costs, customer_count,
                conversion_rate, churn_rate, growth_rate
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes business health. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            health_data = json.loads(ai_response)
            
            business_health.current_revenue = current_revenue
            business_health.current_costs = current_costs
            business_health.customer_count = customer_count
            business_health.conversion_rate = conversion_rate
            business_health.churn_rate = churn_rate
            business_health.growth_rate = growth_rate
            business_health.kpi_metrics = json.dumps(health_data.get("kpi_metrics", {}))
            business_health.health_score = health_data.get("health_score", 0.0)
            business_health.performance_indicators = json.dumps(health_data.get("performance_indicators", []))
            business_health.risk_factors = json.dumps(health_data.get("risk_factors", []))
            business_health.improvement_recommendations = json.dumps(health_data.get("improvement_recommendations", []))
            business_health.trend_analysis = health_data.get("trend_analysis", "")
            business_health.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(business_health)
            
            await self.event_bus.publish("purity.business_health_updated", {
                "health_id": health_id,
                "health_score": business_health.health_score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_health
            
        except Exception as e:
            await db.rollback()
            raise e
    
    def _create_business_health_prompt(
        self,
        business_idea: BusinessIdea,
        current_revenue: float,
        current_costs: float,
        customer_count: int,
        conversion_rate: float,
        churn_rate: float,
        growth_rate: float
    ) -> str:
        return f"""
        Analyze business health for:
        - Business Idea: {business_idea.description}
        - Current Revenue: ${current_revenue:,.2f}
        - Current Costs: ${current_costs:,.2f}
        - Customer Count: {customer_count}
        - Conversion Rate: {conversion_rate}%
        - Churn Rate: {churn_rate}%
        - Growth Rate: {growth_rate}%
        
        Provide comprehensive business health analysis including:
        1. KPI metrics calculation
        2. Health score (0-100)
        3. Performance indicators
        4. Risk factors
        5. Improvement recommendations
        6. Trend analysis
        
        Return the response as a JSON object with the following structure:
        {{
            "kpi_metrics": {{
                "profit_margin": 25.5,
                "customer_lifetime_value": 1500.0,
                "customer_acquisition_cost": 200.0,
                "revenue_per_customer": 500.0,
                "monthly_recurring_revenue": 50000.0
            }},
            "health_score": 78.5,
            "performance_indicators": [
                "Indicator 1: Strong revenue growth",
                "Indicator 2: Healthy profit margins",
                "Indicator 3: Good customer retention"
            ],
            "risk_factors": [
                "Risk 1: High churn rate",
                "Risk 2: Increasing costs",
                "Risk 3: Market competition"
            ],
            "improvement_recommendations": [
                "Recommendation 1: Reduce churn rate",
                "Recommendation 2: Optimize costs",
                "Recommendation 3: Improve conversion"
            ],
            "trend_analysis": "Comprehensive trend analysis"
        }}
        """
    
    def _create_kpi_tracking_prompt(
        self,
        business_health: BusinessHealth,
        metrics_data: Dict[str, Any],
        tracking_period: str
    ) -> str:
        return f"""
        Track KPI metrics for:
        - Current Revenue: ${business_health.current_revenue:,.2f}
        - Current Costs: ${business_health.current_costs:,.2f}
        - Customer Count: {business_health.customer_count}
        - Conversion Rate: {business_health.conversion_rate}%
        - Churn Rate: {business_health.churn_rate}%
        - Growth Rate: {business_health.growth_rate}%
        - Tracking Period: {tracking_period}
        - Metrics Data: {metrics_data}
        
        Analyze KPI tracking including:
        1. KPI analysis
        2. Performance trends
        3. Anomaly detection
        4. Action items
        
        Return the response as a JSON object with the following structure:
        {{
            "kpi_analysis": {{
                "revenue_trend": "Revenue trend analysis",
                "cost_trend": "Cost trend analysis",
                "customer_trend": "Customer trend analysis",
                "conversion_trend": "Conversion trend analysis"
            }},
            "performance_trends": [
                "Trend 1: Revenue growth trend",
                "Trend 2: Cost optimization trend",
                "Trend 3: Customer acquisition trend"
            ],
            "anomaly_detection": [
                "Anomaly 1: Unusual revenue spike",
                "Anomaly 2: Cost increase anomaly",
                "Anomaly 3: Customer churn anomaly"
            ],
            "action_items": [
                "Action 1: Investigate revenue spike",
                "Action 2: Review cost structure",
                "Action 3: Address customer churn"
            ]
        }}
        """
    
    def _create_health_report_prompt(
        self,
        business_health: BusinessHealth,
        report_type: str,
        include_recommendations: bool
    ) -> str:
        return f"""
        Generate business health report for:
        - Health Score: {business_health.health_score}
        - Current Revenue: ${business_health.current_revenue:,.2f}
        - Current Costs: ${business_health.current_costs:,.2f}
        - Customer Count: {business_health.customer_count}
        - Conversion Rate: {business_health.conversion_rate}%
        - Churn Rate: {business_health.churn_rate}%
        - Growth Rate: {business_health.growth_rate}%
        - Report Type: {report_type}
        - Include Recommendations: {include_recommendations}
        
        Create comprehensive health report including:
        1. Executive summary
        2. Detailed analysis
        3. Key findings
        4. Recommendations (if requested)
        5. Action plan
        
        Return the response as a JSON object with the following structure:
        {{
            "executive_summary": "Executive summary of business health",
            "detailed_analysis": "Detailed analysis of business performance",
            "key_findings": [
                "Finding 1: Revenue performance",
                "Finding 2: Cost efficiency",
                "Finding 3: Customer metrics"
            ],
            "recommendations": [
                "Recommendation 1: Revenue optimization",
                "Recommendation 2: Cost reduction",
                "Recommendation 3: Customer retention"
            ],
            "action_plan": {{
                "immediate_actions": ["Action 1", "Action 2"],
                "short_term_goals": ["Goal 1", "Goal 2"],
                "long_term_strategy": "Long-term strategy"
            }}
        }}
        """
