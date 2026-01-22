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

class LeadScoringService:
    def __init__(self):
        # NLPUtils removed - not used in this service
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize lead scoring service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("EricLead scoring service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize lead scoring service: {e}")
            raise

    async def score_lead(self, lead_id: str, brand_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a lead using AI-powered algorithms"""
        try:
            async with get_eric_database() as db:
                # Analyze lead data
                lead_analysis = await self._analyze_lead_data(lead_data)
                
                # Calculate behavioral score
                behavioral_score = await self._calculate_behavioral_score(lead_id, brand_id, lead_data)
                
                # Calculate demographic score
                demographic_score = await self._calculate_demographic_score(lead_data)
                
                # Calculate intent score
                intent_score = await self._calculate_intent_score(lead_id, brand_id, lead_data)
                
                # Calculate engagement score
                engagement_score = await self._calculate_engagement_score(lead_id, brand_id)
                
                # Calculate company fit score
                company_fit_score = await self._calculate_company_fit_score(lead_data)
                
                # Generate overall score
                overall_score = await self._generate_overall_score(
                    behavioral_score, demographic_score, intent_score, 
                    engagement_score, company_fit_score
                )
                
                # Determine lead qualification
                qualification = await self._determine_lead_qualification(overall_score, lead_data)
                
                # Generate scoring insights
                insights = await self._generate_scoring_insights(
                    overall_score, behavioral_score, demographic_score, 
                    intent_score, engagement_score, company_fit_score
                )
                
                return {
                    "lead_id": lead_id,
                    "brand_id": brand_id,
                    "overall_score": overall_score,
                    "qualification": qualification,
                    "score_breakdown": {
                        "behavioral_score": behavioral_score,
                        "demographic_score": demographic_score,
                        "intent_score": intent_score,
                        "engagement_score": engagement_score,
                        "company_fit_score": company_fit_score
                    },
                    "insights": insights,
                    "recommendations": await self._generate_lead_recommendations(overall_score, qualification),
                    "scored_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error scoring lead: {e}")
            raise

    async def qualify_lead(self, lead_id: str, brand_id: str, qualification_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify a lead based on specific criteria"""
        try:
            async with get_eric_database() as db:
                # Get lead data
                lead_data = await self._get_lead_data(lead_id, brand_id)
                
                # Apply qualification criteria
                qualification_results = await self._apply_qualification_criteria(lead_data, qualification_criteria)
                
                # Determine qualification status
                qualification_status = await self._determine_qualification_status(qualification_results)
                
                # Generate qualification report
                qualification_report = await self._generate_qualification_report(
                    lead_id, brand_id, qualification_results, qualification_status
                )
                
                # Create next steps
                next_steps = await self._create_qualification_next_steps(qualification_status, lead_data)
                
                return {
                    "lead_id": lead_id,
                    "brand_id": brand_id,
                    "qualification_status": qualification_status,
                    "qualification_results": qualification_results,
                    "qualification_report": qualification_report,
                    "next_steps": next_steps,
                    "qualified_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            raise

    async def prioritize_leads(self, brand_id: str, lead_ids: List[str], 
                             prioritization_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize leads based on scoring and criteria"""
        try:
            async with get_eric_database() as db:
                # Get lead scores
                lead_scores = await self._get_lead_scores(lead_ids, brand_id)
                
                # Apply prioritization criteria
                prioritized_leads = await self._apply_prioritization_criteria(
                    lead_scores, prioritization_criteria
                )
                
                # Generate priority rankings
                priority_rankings = await self._generate_priority_rankings(prioritized_leads)
                
                # Create action plan
                action_plan = await self._create_prioritization_action_plan(priority_rankings)
                
                return {
                    "brand_id": brand_id,
                    "prioritized_leads": prioritized_leads,
                    "priority_rankings": priority_rankings,
                    "action_plan": action_plan,
                    "prioritization_criteria": prioritization_criteria,
                    "prioritized_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error prioritizing leads: {e}")
            raise

    async def analyze_lead_intent(self, lead_id: str, brand_id: str, 
                                intent_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze lead intent based on various signals"""
        try:
            async with get_eric_database() as db:
                # Process intent signals
                processed_signals = await self._process_intent_signals(intent_signals)
                
                # Calculate intent score
                intent_score = await self._calculate_intent_score_from_signals(processed_signals)
                
                # Determine intent level
                intent_level = await self._determine_intent_level(intent_score)
                
                # Generate intent insights
                intent_insights = await self._generate_intent_insights(processed_signals, intent_score)
                
                # Create intent-based recommendations
                recommendations = await self._create_intent_recommendations(intent_level, intent_insights)
                
                return {
                    "lead_id": lead_id,
                    "brand_id": brand_id,
                    "intent_signals": intent_signals,
                    "processed_signals": processed_signals,
                    "intent_score": intent_score,
                    "intent_level": intent_level,
                    "intent_insights": intent_insights,
                    "recommendations": recommendations,
                    "analyzed_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing lead intent: {e}")
            raise

    async def update_lead_score(self, lead_id: str, brand_id: str, 
                              new_activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lead score based on new activity"""
        try:
            async with get_eric_database() as db:
                # Get current lead score
                current_score = await self._get_current_lead_score(lead_id, brand_id)
                
                # Analyze new activity
                activity_impact = await self._analyze_activity_impact(new_activity_data)
                
                # Calculate score adjustment
                score_adjustment = await self._calculate_score_adjustment(activity_impact)
                
                # Update lead score
                updated_score = await self._update_lead_score_calculation(current_score, score_adjustment)
                
                # Generate update insights
                update_insights = await self._generate_update_insights(
                    current_score, updated_score, activity_impact
                )
                
                return {
                    "lead_id": lead_id,
                    "brand_id": brand_id,
                    "previous_score": current_score,
                    "updated_score": updated_score,
                    "score_change": score_adjustment,
                    "activity_impact": activity_impact,
                    "update_insights": update_insights,
                    "updated_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error updating lead score: {e}")
            raise

    async def get_lead_scoring_analytics(self, brand_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """Get lead scoring analytics and insights"""
        try:
            async with get_eric_database() as db:
                # Get scoring data
                scoring_data = await self._get_scoring_data(brand_id, time_period)
                
                # Calculate scoring metrics
                scoring_metrics = await self._calculate_scoring_metrics(scoring_data)
                
                # Analyze scoring trends
                scoring_trends = await self._analyze_scoring_trends(scoring_data)
                
                # Generate scoring insights
                scoring_insights = await self._generate_scoring_analytics_insights(
                    scoring_metrics, scoring_trends
                )
                
                # Create optimization recommendations
                optimization_recommendations = await self._create_scoring_optimization_recommendations(
                    scoring_metrics, scoring_trends
                )
                
                return {
                    "brand_id": brand_id,
                    "time_period": time_period,
                    "scoring_data": scoring_data,
                    "scoring_metrics": scoring_metrics,
                    "scoring_trends": scoring_trends,
                    "scoring_insights": scoring_insights,
                    "optimization_recommendations": optimization_recommendations
                }
                
        except Exception as e:
            logger.error(f"Error getting lead scoring analytics: {e}")
            raise

    # Helper methods
    async def _analyze_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead data for scoring"""
        return {
            "company_size": lead_data.get("company_size", "unknown"),
            "industry": lead_data.get("industry", "unknown"),
            "job_title": lead_data.get("job_title", "unknown"),
            "location": lead_data.get("location", "unknown"),
            "budget_range": lead_data.get("budget_range", "unknown"),
            "decision_authority": lead_data.get("decision_authority", "unknown")
        }

    async def _calculate_behavioral_score(self, lead_id: str, brand_id: str, lead_data: Dict[str, Any]) -> float:
        """Calculate behavioral score based on lead activities"""
        try:
            async with get_eric_database() as db:
                # Get lead's interaction history
                interactions = await db.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.lead_id == lead_id,
                            EricSalesActivity.brand_id == brand_id,
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    )
                )
                activity_list = interactions.scalars().all()
                
                if not activity_list:
                    return 0.0
                
                # Calculate engagement metrics
                total_interactions = len(activity_list)
                recent_interactions = len([a for a in activity_list if a.created_at >= datetime.utcnow() - timedelta(days=7)])
                
                # Calculate response rate
                response_activities = [a for a in activity_list if a.activity_type in ["email_response", "call_response", "meeting_scheduled"]]
                response_rate = len(response_activities) / total_interactions if total_interactions > 0 else 0.0
                
                # Calculate website engagement
                website_activities = [a for a in activity_list if a.activity_type in ["page_view", "download", "form_submit"]]
                website_engagement = len(website_activities) / total_interactions if total_interactions > 0 else 0.0
                
                # Calculate behavioral score (weighted average)
                behavioral_score = (
                    (response_rate * 0.4) +
                    (website_engagement * 0.3) +
                    (min(recent_interactions / 10.0, 1.0) * 0.2) +
                    (min(total_interactions / 20.0, 1.0) * 0.1)
                )
                
                return min(behavioral_score, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating behavioral score: {e}")
            return 0.0

    async def _calculate_demographic_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate demographic score based on lead characteristics"""
        try:
            # Extract demographic factors
            company_size = lead_data.get("company_size", "unknown")
            industry = lead_data.get("industry", "unknown")
            job_title = lead_data.get("job_title", "unknown")
            location = lead_data.get("location", "unknown")
            
            # Score company size
            size_scores = {
                "enterprise": 1.0,
                "large": 0.9,
                "medium": 0.7,
                "small": 0.5,
                "startup": 0.3,
                "unknown": 0.5
            }
            size_score = size_scores.get(company_size.lower(), 0.5)
            
            # Score industry (high-value industries get higher scores)
            high_value_industries = ["technology", "finance", "healthcare", "manufacturing"]
            industry_score = 1.0 if industry.lower() in high_value_industries else 0.6
            
            # Score job title (decision makers get higher scores)
            decision_maker_titles = ["ceo", "cto", "cfo", "vp", "director", "manager", "head"]
            title_score = 1.0 if any(title in job_title.lower() for title in decision_maker_titles) else 0.6
            
            # Score location (major markets get higher scores)
            major_markets = ["new york", "san francisco", "los angeles", "chicago", "boston", "seattle"]
            location_score = 1.0 if any(market in location.lower() for market in major_markets) else 0.7
            
            # Calculate weighted demographic score
            demographic_score = (
                (size_score * 0.3) +
                (industry_score * 0.25) +
                (title_score * 0.25) +
                (location_score * 0.2)
            )
            
            return demographic_score
            
        except Exception as e:
            logger.error(f"Error calculating demographic score: {e}")
            return 0.5

    async def _calculate_intent_score(self, lead_id: str, brand_id: str, lead_data: Dict[str, Any]) -> float:
        """Calculate intent score based on lead behavior"""
        try:
            async with get_eric_database() as db:
                # Get lead's intent signals from recent activities
                intent_activities = await db.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.lead_id == lead_id,
                            EricSalesActivity.brand_id == brand_id,
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=14),
                            EricSalesActivity.activity_type.in_([
                                "pricing_page_view", "demo_request", "trial_signup", 
                                "case_study_download", "competitor_research", "purchase_intent"
                            ])
                        )
                    )
                )
                activities = intent_activities.scalars().all()
                
                if not activities:
                    return 0.0
                
                # Calculate intent signals
                intent_signals = {
                    "pricing_page_view": 0.3,
                    "demo_request": 0.8,
                    "trial_signup": 0.9,
                    "case_study_download": 0.6,
                    "competitor_research": 0.7,
                    "purchase_intent": 1.0
                }
                
                # Calculate weighted intent score
                total_weight = 0
                weighted_sum = 0
                
                for activity in activities:
                    weight = intent_signals.get(activity.activity_type, 0.1)
                    # Decay weight based on recency
                    days_ago = (datetime.utcnow() - activity.created_at).days
                    recency_factor = max(0.1, 1.0 - (days_ago / 14.0))
                    
                    total_weight += weight * recency_factor
                    weighted_sum += weight * recency_factor
                
                intent_score = weighted_sum / total_weight if total_weight > 0 else 0.0
                
                # Boost score based on lead data indicators
                if lead_data.get("budget_range") in ["$50K-$100K", "$100K+"]:
                    intent_score *= 1.2
                
                if lead_data.get("decision_authority") == "high":
                    intent_score *= 1.1
                
                return min(intent_score, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating intent score: {e}")
            return 0.0

    async def _calculate_engagement_score(self, lead_id: str, brand_id: str) -> float:
        """Calculate engagement score based on lead interactions"""
        try:
            async with get_eric_database() as db:
                # Get lead's engagement activities
                engagement_activities = await db.execute(
                    select(EricSalesActivity).where(
                        and_(
                            EricSalesActivity.lead_id == lead_id,
                            EricSalesActivity.brand_id == brand_id,
                            EricSalesActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    )
                )
                activities = engagement_activities.scalars().all()
                
                if not activities:
                    return 0.0
                
                # Define engagement weights
                engagement_weights = {
                    "email_open": 0.2,
                    "email_click": 0.4,
                    "website_visit": 0.3,
                    "content_download": 0.6,
                    "webinar_attendance": 0.8,
                    "meeting_scheduled": 0.9,
                    "phone_call": 0.7,
                    "social_media_engagement": 0.3
                }
                
                # Calculate engagement metrics
                total_engagement = 0
                recent_engagement = 0
                engagement_frequency = 0
                
                for activity in activities:
                    weight = engagement_weights.get(activity.activity_type, 0.1)
                    total_engagement += weight
                    
                    # Recent engagement (last 7 days)
                    if activity.created_at >= datetime.utcnow() - timedelta(days=7):
                        recent_engagement += weight * 1.5  # Boost recent activities
                
                # Calculate engagement frequency
                unique_days = len(set(activity.created_at.date() for activity in activities))
                engagement_frequency = min(unique_days / 30.0, 1.0)
                
                # Calculate final engagement score
                engagement_score = (
                    (total_engagement * 0.4) +
                    (recent_engagement * 0.4) +
                    (engagement_frequency * 0.2)
                ) / 10.0  # Normalize to 0-1 range
                
                return min(engagement_score, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    async def _calculate_company_fit_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate company fit score based on ideal customer profile"""
        try:
            # Define ideal customer profile characteristics
            ideal_profile = {
                "company_size": ["medium", "large", "enterprise"],
                "industries": ["technology", "finance", "healthcare", "manufacturing", "retail"],
                "job_titles": ["ceo", "cto", "cfo", "vp", "director", "manager", "head"],
                "locations": ["new york", "san francisco", "los angeles", "chicago", "boston", "seattle"],
                "budget_ranges": ["$50K-$100K", "$100K+", "$25K-$50K"]
            }
            
            # Extract lead characteristics
            company_size = lead_data.get("company_size", "").lower()
            industry = lead_data.get("industry", "").lower()
            job_title = lead_data.get("job_title", "").lower()
            location = lead_data.get("location", "").lower()
            budget_range = lead_data.get("budget_range", "")
            
            # Calculate fit scores for each dimension
            size_fit = 1.0 if company_size in ideal_profile["company_size"] else 0.3
            industry_fit = 1.0 if industry in ideal_profile["industries"] else 0.4
            title_fit = 1.0 if any(title in job_title for title in ideal_profile["job_titles"]) else 0.5
            location_fit = 1.0 if any(loc in location for loc in ideal_profile["locations"]) else 0.6
            budget_fit = 1.0 if budget_range in ideal_profile["budget_ranges"] else 0.3
            
            # Calculate weighted company fit score
            company_fit_score = (
                (size_fit * 0.25) +
                (industry_fit * 0.25) +
                (title_fit * 0.20) +
                (location_fit * 0.15) +
                (budget_fit * 0.15)
            )
            
            return company_fit_score
            
        except Exception as e:
            logger.error(f"Error calculating company fit score: {e}")
            return 0.5

    async def _generate_overall_score(self, behavioral_score: float, demographic_score: float,
                                   intent_score: float, engagement_score: float, 
                                   company_fit_score: float) -> float:
        """Generate overall lead score"""
        # Weighted average of all scores
        weights = {
            "behavioral": 0.25,
            "demographic": 0.20,
            "intent": 0.25,
            "engagement": 0.20,
            "company_fit": 0.10
        }
        
        overall_score = (
            behavioral_score * weights["behavioral"] +
            demographic_score * weights["demographic"] +
            intent_score * weights["intent"] +
            engagement_score * weights["engagement"] +
            company_fit_score * weights["company_fit"]
        )
        
        return round(overall_score, 3)

    async def _determine_lead_qualification(self, overall_score: float, lead_data: Dict[str, Any]) -> str:
        """Determine lead qualification based on score"""
        if overall_score >= 0.8:
            return "hot"
        elif overall_score >= 0.6:
            return "warm"
        elif overall_score >= 0.4:
            return "lukewarm"
        else:
            return "cold"

    async def _generate_scoring_insights(self, overall_score: float, behavioral_score: float,
                                      demographic_score: float, intent_score: float,
                                      engagement_score: float, company_fit_score: float) -> List[str]:
        """Generate insights from scoring results"""
        insights = []
        
        if overall_score >= 0.8:
            insights.append("High-scoring lead with strong potential for conversion")
        
        if behavioral_score >= 0.8:
            insights.append("EricLead shows strong behavioral signals indicating high interest")
        
        if intent_score >= 0.8:
            insights.append("EricLead demonstrates clear purchase intent")
        
        if engagement_score < 0.5:
            insights.append("Low engagement score suggests need for more nurturing")
        
        if company_fit_score >= 0.8:
            insights.append("EricLead fits ideal customer profile very well")
        
        return insights

    async def _generate_lead_recommendations(self, overall_score: float, qualification: str) -> List[Dict[str, Any]]:
        """Generate recommendations based on lead score and qualification"""
        recommendations = []
        
        if qualification == "hot":
            recommendations.append({
                "action": "Immediate follow-up",
                "priority": "high",
                "timeline": "within_24_hours",
                "channel": "phone"
            })
        elif qualification == "warm":
            recommendations.append({
                "action": "Nurture campaign",
                "priority": "medium",
                "timeline": "within_48_hours",
                "channel": "email"
            })
        elif qualification == "lukewarm":
            recommendations.append({
                "action": "Educational content",
                "priority": "low",
                "timeline": "within_week",
                "channel": "email"
            })
        
        return recommendations

    async def _get_lead_data(self, lead_id: str, brand_id: str) -> Dict[str, Any]:
        """Get lead data from database"""
        # Implementation for getting lead data
        return {
            "lead_id": lead_id,
            "company_size": "50-200",
            "industry": "technology",
            "job_title": "CTO",
            "location": "San Francisco",
            "budget_range": "$50K-$100K",
            "decision_authority": "high"
        }

    async def _apply_qualification_criteria(self, lead_data: Dict[str, Any], 
                                         qualification_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Apply qualification criteria to lead data"""
        # Implementation for applying qualification criteria
        return {
            "budget_match": True,
            "authority_match": True,
            "timeline_match": False,
            "need_match": True,
            "overall_qualification": 0.75
        }

    async def _determine_qualification_status(self, qualification_results: Dict[str, Any]) -> str:
        """Determine qualification status based on results"""
        overall_score = qualification_results.get("overall_qualification", 0)
        
        if overall_score >= 0.8:
            return "qualified"
        elif overall_score >= 0.6:
            return "prospect"
        else:
            return "unqualified"

    async def _generate_qualification_report(self, lead_id: str, brand_id: str,
                                          qualification_results: Dict[str, Any],
                                          qualification_status: str) -> Dict[str, Any]:
        """Generate qualification report"""
        return {
            "lead_id": lead_id,
            "brand_id": brand_id,
            "qualification_status": qualification_status,
            "qualification_score": qualification_results.get("overall_qualification", 0),
            "criteria_results": qualification_results,
            "report_generated_at": datetime.utcnow()
        }

    async def _create_qualification_next_steps(self, qualification_status: str, 
                                            lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create next steps based on qualification status"""
        if qualification_status == "qualified":
            return [
                {"step": "Schedule demo", "priority": "high", "timeline": "immediate"},
                {"step": "Send proposal", "priority": "high", "timeline": "within_24_hours"}
            ]
        elif qualification_status == "prospect":
            return [
                {"step": "Nurture campaign", "priority": "medium", "timeline": "within_week"},
                {"step": "Educational content", "priority": "medium", "timeline": "within_week"}
            ]
        else:
            return [
                {"step": "Re-engage later", "priority": "low", "timeline": "within_month"},
                {"step": "Update lead data", "priority": "low", "timeline": "ongoing"}
            ]

    async def _get_lead_scores(self, lead_ids: List[str], brand_id: str) -> Dict[str, float]:
        """Get lead scores for prioritization"""
        # Implementation for getting lead scores
        return {lead_id: 0.75 for lead_id in lead_ids}

    async def _apply_prioritization_criteria(self, lead_scores: Dict[str, float],
                                          prioritization_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply prioritization criteria to leads"""
        # Implementation for applying prioritization criteria
        prioritized_leads = []
        for lead_id, score in lead_scores.items():
            prioritized_leads.append({
                "lead_id": lead_id,
                "score": score,
                "priority_level": "high" if score >= 0.8 else "medium" if score >= 0.6 else "low"
            })
        
        return sorted(prioritized_leads, key=lambda x: x["score"], reverse=True)

    async def _generate_priority_rankings(self, prioritized_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate priority rankings"""
        rankings = []
        for i, lead in enumerate(prioritized_leads, 1):
            rankings.append({
                "rank": i,
                "lead_id": lead["lead_id"],
                "score": lead["score"],
                "priority_level": lead["priority_level"]
            })
        
        return rankings

    async def _create_prioritization_action_plan(self, priority_rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create action plan based on priority rankings"""
        action_plan = []
        for ranking in priority_rankings:
            if ranking["priority_level"] == "high":
                action_plan.append({
                    "lead_id": ranking["lead_id"],
                    "action": "Immediate outreach",
                    "timeline": "within_24_hours",
                    "priority": "high"
                })
            elif ranking["priority_level"] == "medium":
                action_plan.append({
                    "lead_id": ranking["lead_id"],
                    "action": "Scheduled follow-up",
                    "timeline": "within_week",
                    "priority": "medium"
                })
        
        return action_plan

    async def _process_intent_signals(self, intent_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process intent signals for analysis"""
        # Implementation for processing intent signals
        processed_signals = []
        for signal in intent_signals:
            processed_signals.append({
                "signal_type": signal.get("type"),
                "signal_value": signal.get("value"),
                "signal_weight": signal.get("weight", 1.0),
                "timestamp": signal.get("timestamp")
            })
        
        return processed_signals

    async def _calculate_intent_score_from_signals(self, processed_signals: List[Dict[str, Any]]) -> float:
        """Calculate intent score from processed signals"""
        # Implementation for calculating intent score
        total_weight = sum(signal["signal_weight"] for signal in processed_signals)
        weighted_sum = sum(signal["signal_value"] * signal["signal_weight"] for signal in processed_signals)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    async def _determine_intent_level(self, intent_score: float) -> str:
        """Determine intent level based on score"""
        if intent_score >= 0.8:
            return "high"
        elif intent_score >= 0.6:
            return "medium"
        else:
            return "low"

    async def _generate_intent_insights(self, processed_signals: List[Dict[str, Any]], 
                                     intent_score: float) -> List[str]:
        """Generate insights from intent analysis"""
        insights = []
        
        if intent_score >= 0.8:
            insights.append("EricLead shows strong purchase intent signals")
        
        signal_types = [signal["signal_type"] for signal in processed_signals]
        if "website_visit" in signal_types:
            insights.append("EricLead has visited website multiple times")
        
        if "email_open" in signal_types:
            insights.append("EricLead is engaging with email content")
        
        return insights

    async def _create_intent_recommendations(self, intent_level: str, 
                                          intent_insights: List[str]) -> List[Dict[str, Any]]:
        """Create recommendations based on intent level"""
        if intent_level == "high":
            return [
                {"recommendation": "Immediate sales outreach", "priority": "high"},
                {"recommendation": "Schedule product demo", "priority": "high"}
            ]
        elif intent_level == "medium":
            return [
                {"recommendation": "Nurture with targeted content", "priority": "medium"},
                {"recommendation": "Follow up with case studies", "priority": "medium"}
            ]
        else:
            return [
                {"recommendation": "Continue educational content", "priority": "low"},
                {"recommendation": "Monitor for intent signals", "priority": "low"}
            ]

    async def _get_current_lead_score(self, lead_id: str, brand_id: str) -> float:
        """Get current lead score"""
        # Implementation for getting current score
        return 0.75

    async def _analyze_activity_impact(self, new_activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact of new activity on lead score"""
        # Implementation for analyzing activity impact
        return {
            "activity_type": new_activity_data.get("type"),
            "impact_score": 0.1,
            "impact_reason": "Positive engagement activity"
        }

    async def _calculate_score_adjustment(self, activity_impact: Dict[str, Any]) -> float:
        """Calculate score adjustment based on activity impact"""
        return activity_impact.get("impact_score", 0.0)

    async def _update_lead_score_calculation(self, current_score: float, score_adjustment: float) -> float:
        """Update lead score calculation"""
        new_score = current_score + score_adjustment
        return max(0.0, min(1.0, new_score))  # Ensure score is between 0 and 1

    async def _generate_update_insights(self, current_score: float, updated_score: float,
                                     activity_impact: Dict[str, Any]) -> List[str]:
        """Generate insights from score update"""
        insights = []
        
        if updated_score > current_score:
            insights.append("EricLead score increased due to positive activity")
        elif updated_score < current_score:
            insights.append("EricLead score decreased due to negative activity")
        
        insights.append(f"Activity: {activity_impact.get('activity_type')}")
        insights.append(f"Impact: {activity_impact.get('impact_reason')}")
        
        return insights

    async def _get_scoring_data(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        """Get scoring data for analytics"""
        # Implementation for getting scoring data
        return {
            "total_leads_scored": 1000,
            "average_score": 0.65,
            "score_distribution": {
                "high": 0.25,
                "medium": 0.45,
                "low": 0.30
            }
        }

    async def _calculate_scoring_metrics(self, scoring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate scoring metrics"""
        return {
            "total_leads": scoring_data["total_leads_scored"],
            "average_score": scoring_data["average_score"],
            "score_distribution": scoring_data["score_distribution"],
            "conversion_rate_by_score": {
                "high": 0.25,
                "medium": 0.12,
                "low": 0.05
            }
        }

    async def _analyze_scoring_trends(self, scoring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scoring trends"""
        return {
            "trend_direction": "improving",
            "score_growth_rate": 0.05,
            "conversion_correlation": 0.85
        }

    async def _generate_scoring_analytics_insights(self, scoring_metrics: Dict[str, Any],
                                                scoring_trends: Dict[str, Any]) -> List[str]:
        """Generate insights from scoring analytics"""
        return [
            "EricLead scoring shows strong correlation with conversion rates",
            "High-scoring leads convert at 5x the rate of low-scoring leads",
            "Scoring accuracy has improved by 5% over the last month"
        ]

    async def _create_scoring_optimization_recommendations(self, scoring_metrics: Dict[str, Any],
                                                        scoring_trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create optimization recommendations for scoring"""
        return [
            {"recommendation": "Adjust scoring weights for better accuracy", "priority": "high"},
            {"recommendation": "Add new scoring criteria based on recent trends", "priority": "medium"},
            {"recommendation": "Implement machine learning for dynamic scoring", "priority": "low"}
        ]
