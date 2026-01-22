from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import asyncio
import json
from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..models import (
    EricSalesRep, EricDeal, EricSalesActivity, EricLead, CustomerProfile,
    EthicalSalesScore, EricSalesAnalytics, EricSalesForecast
)
from ..database import get_eric_database
from core.event_bus.kafka_manager import EventBus as KafkaProducer
from core.cache import redis_manager
from core.config import settings


class EthicalScore(BaseModel):
    overall_score: float
    transparency_score: float
    pressure_tactics_score: float
    honesty_score: float
    customer_focus_score: float
    compliance_score: float
    risk_level: str
    recommendations: List[str]


class SalesActivityEthicalAnalysis(BaseModel):
    activity_id: int
    activity_type: str
    ethical_score: float
    risk_factors: List[str]
    suggestions: List[str]
    timestamp: datetime


class EthicalSalesScoringService:
    def __init__(self):
        self.ai_service_manager = None
        self.kafka_producer = KafkaProducer()
        self.redis_client = redis_manager.redis
        self.cache_ttl = 300  # 5 minutes
        self._initialized = False
    
    async def initialize(self):
        """Initialize ethical sales scoring service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.kafka_producer.initialize()
            # redis_manager is already initialized
            self._initialized = True
            logger.info("Ethical sales scoring service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ethical sales scoring service: {e}")
            raise

    async def calculate_ethical_score(
        self, 
        db: Session, 
        sales_rep_id: int,
        date_range: str = "30d"
    ) -> EthicalScore:
        """Calculate comprehensive ethical sales score for a sales rep"""
        cache_key = f"ethical_score:{sales_rep_id}:{date_range}"
        
        # Check cache first
        cached_data = await redis_manager.redis.get(cache_key)
        if cached_data:
            return EthicalScore(**json.loads(cached_data))
        
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
        
        # Get sales rep
        sales_rep = db.query(EricSalesRep).filter(EricSalesRep.id == sales_rep_id).first()
        if not sales_rep:
            raise HTTPException(status_code=404, detail="Sales rep not found")
        
        # Get activities for the period
        activities = db.query(EricSalesActivity).filter(
            and_(
                EricSalesActivity.sales_rep_id == sales_rep_id,
                EricSalesActivity.created_at >= start_date,
                EricSalesActivity.created_at <= end_date
            )
        ).all()
        
        # Calculate individual scores
        transparency_score = await self._calculate_transparency_score(activities)
        pressure_tactics_score = await self._calculate_pressure_tactics_score(activities)
        honesty_score = await self._calculate_honesty_score(activities)
        customer_focus_score = await self._calculate_customer_focus_score(activities)
        compliance_score = await self._calculate_compliance_score(activities)
        
        # Calculate overall score
        overall_score = (
            transparency_score * 0.25 +
            pressure_tactics_score * 0.20 +
            honesty_score * 0.25 +
            customer_focus_score * 0.20 +
            compliance_score * 0.10
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Generate recommendations
        recommendations = await self._generate_ethical_recommendations(
            transparency_score, pressure_tactics_score, honesty_score, 
            customer_focus_score, compliance_score
        )
        
        ethical_score = EthicalScore(
            overall_score=overall_score,
            transparency_score=transparency_score,
            pressure_tactics_score=pressure_tactics_score,
            honesty_score=honesty_score,
            customer_focus_score=customer_focus_score,
            compliance_score=compliance_score,
            risk_level=risk_level,
            recommendations=recommendations
        )
        
        # Cache results
        await redis_manager.redis.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(ethical_score.dict())
        )
        
        # Store in database
        await self._store_ethical_score(db, sales_rep_id, ethical_score, date_range)
        
        return ethical_score

    async def analyze_activity_ethics(
        self, 
        db: Session, 
        activity_id: int
    ) -> SalesActivityEthicalAnalysis:
        """Analyze the ethical aspects of a specific sales activity"""
        # Get activity
        activity = db.query(EricSalesActivity).filter(EricSalesActivity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Sales activity not found")
        
        # Analyze activity content
        risk_factors = await self._identify_risk_factors(activity)
        ethical_score = await self._calculate_activity_ethical_score(activity, risk_factors)
        suggestions = await self._generate_activity_suggestions(activity, risk_factors)
        
        return SalesActivityEthicalAnalysis(
            activity_id=activity_id,
            activity_type=activity.activity_type,
            ethical_score=ethical_score,
            risk_factors=risk_factors,
            suggestions=suggestions,
            timestamp=activity.created_at
        )

    async def get_team_ethical_report(
        self, 
        db: Session, 
        team_id: int,
        date_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive ethical report for entire team"""
        # Get team members
        team_members = db.query(EricSalesRep).filter(EricSalesRep.team_id == team_id).all()
        if not team_members:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Calculate ethical scores for all team members
        team_scores = []
        for rep in team_members:
            try:
                score = await self.calculate_ethical_score(db, rep.id, date_range)
                team_scores.append({
                    "rep_id": rep.id,
                    "name": f"{rep.first_name} {rep.last_name}",
                    "score": score
                })
            except Exception as e:
                # Log error but continue with other reps
                continue
        
        # Calculate team averages
        if team_scores:
            avg_overall = sum(s["score"].overall_score for s in team_scores) / len(team_scores)
            avg_transparency = sum(s["score"].transparency_score for s in team_scores) / len(team_scores)
            avg_pressure = sum(s["score"].pressure_tactics_score for s in team_scores) / len(team_scores)
            avg_honesty = sum(s["score"].honesty_score for s in team_scores) / len(team_scores)
            avg_customer_focus = sum(s["score"].customer_focus_score for s in team_scores) / len(team_scores)
            avg_compliance = sum(s["score"].compliance_score for s in team_scores) / len(team_scores)
        else:
            avg_overall = avg_transparency = avg_pressure = avg_honesty = avg_customer_focus = avg_compliance = 0
        
        # Identify high-risk reps
        high_risk_reps = [s for s in team_scores if s["score"].risk_level in ["high", "critical"]]
        
        # Generate team recommendations
        team_recommendations = await self._generate_team_recommendations(team_scores)
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "team_averages": {
                "overall_score": avg_overall,
                "transparency_score": avg_transparency,
                "pressure_tactics_score": avg_pressure,
                "honesty_score": avg_honesty,
                "customer_focus_score": avg_customer_focus,
                "compliance_score": avg_compliance
            },
            "individual_scores": [s["score"].dict() for s in team_scores],
            "high_risk_reps": len(high_risk_reps),
            "team_recommendations": team_recommendations,
            "risk_distribution": {
                "low": len([s for s in team_scores if s["score"].risk_level == "low"]),
                "medium": len([s for s in team_scores if s["score"].risk_level == "medium"]),
                "high": len([s for s in team_scores if s["score"].risk_level == "high"]),
                "critical": len([s for s in team_scores if s["score"].risk_level == "critical"])
            }
        }

    async def flag_aggressive_tactics(
        self, 
        db: Session, 
        sales_rep_id: int,
        date_range: str = "7d"
    ) -> List[Dict[str, Any]]:
        """Flag potentially aggressive sales tactics"""
        # Calculate date range
        end_date = datetime.now()
        if date_range == "7d":
            start_date = end_date - timedelta(days=7)
        elif date_range == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get recent activities
        activities = db.query(EricSalesActivity).filter(
            and_(
                EricSalesActivity.sales_rep_id == sales_rep_id,
                EricSalesActivity.created_at >= start_date,
                EricSalesActivity.created_at <= end_date
            )
        ).all()
        
        flagged_activities = []
        
        for activity in activities:
            risk_factors = await self._identify_risk_factors(activity)
            
            if risk_factors:
                flagged_activities.append({
                    "activity_id": activity.id,
                    "activity_type": activity.activity_type,
                    "timestamp": activity.created_at.isoformat(),
                    "risk_factors": risk_factors,
                    "severity": self._calculate_severity(risk_factors),
                    "suggested_alternatives": await self._suggest_ethical_alternatives(activity, risk_factors)
                })
        
        return flagged_activities

    async def suggest_ethical_alternatives(
        self, 
        db: Session, 
        activity_id: int
    ) -> Dict[str, Any]:
        """Suggest ethical alternatives for a specific activity"""
        # Get activity
        activity = db.query(EricSalesActivity).filter(EricSalesActivity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Sales activity not found")
        
        # Identify risk factors
        risk_factors = await self._identify_risk_factors(activity)
        
        # Generate alternatives
        alternatives = await self._suggest_ethical_alternatives(activity, risk_factors)
        
        return {
            "activity_id": activity_id,
            "activity_type": activity.activity_type,
            "current_approach": {
                "description": activity.description,
                "risk_factors": risk_factors
            },
            "ethical_alternatives": alternatives,
            "benefits": await self._explain_ethical_benefits(alternatives)
        }

    async def _calculate_transparency_score(self, activities: List[EricSalesActivity]) -> float:
        """Calculate transparency score based on activities"""
        if not activities:
            return 100.0
        
        transparency_indicators = 0
        total_activities = len(activities)
        
        for activity in activities:
            # Check for transparency indicators
            if activity.description:
                description_lower = activity.description.lower()
                
                # Positive indicators
                if any(phrase in description_lower for phrase in [
                    "clearly explained", "transparent", "honest", "upfront", 
                    "disclosed", "informed", "detailed", "comprehensive"
                ]):
                    transparency_indicators += 1
                
                # Negative indicators
                if any(phrase in description_lower for phrase in [
                    "hidden", "secret", "undisclosed", "fine print", 
                    "catch", "trick", "misleading"
                ]):
                    transparency_indicators -= 1
        
        # Normalize score
        base_score = (transparency_indicators / total_activities) * 100
        return max(0, min(100, base_score + 50))  # Base score of 50

    async def _calculate_pressure_tactics_score(self, activities: List[EricSalesActivity]) -> float:
        """Calculate pressure tactics score (higher is better - less pressure)"""
        if not activities:
            return 100.0
        
        pressure_indicators = 0
        total_activities = len(activities)
        
        for activity in activities:
            if activity.description:
                description_lower = activity.description.lower()
                
                # Pressure indicators (negative)
                pressure_phrases = [
                    "limited time", "act now", "expires soon", "last chance",
                    "urgent", "immediate", "today only", "final offer",
                    "pressure", "push", "force", "insist", "demand"
                ]
                
                for phrase in pressure_phrases:
                    if phrase in description_lower:
                        pressure_indicators += 1
                        break
        
        # Convert to positive score (less pressure = higher score)
        pressure_ratio = pressure_indicators / total_activities
        score = 100 - (pressure_ratio * 100)
        return max(0, min(100, score))

    async def _calculate_honesty_score(self, activities: List[EricSalesActivity]) -> float:
        """Calculate honesty score based on activities"""
        if not activities:
            return 100.0
        
        honesty_indicators = 0
        total_activities = len(activities)
        
        for activity in activities:
            if activity.description:
                description_lower = activity.description.lower()
                
                # Honesty indicators (positive)
                honest_phrases = [
                    "truthful", "accurate", "verified", "confirmed",
                    "honest", "genuine", "authentic", "real"
                ]
                
                for phrase in honest_phrases:
                    if phrase in description_lower:
                        honesty_indicators += 1
                        break
                
                # Dishonesty indicators (negative)
                dishonest_phrases = [
                    "exaggerated", "inflated", "fake", "false",
                    "misleading", "deceptive", "untrue", "lie"
                ]
                
                for phrase in dishonest_phrases:
                    if phrase in description_lower:
                        honesty_indicators -= 1
                        break
        
        # Normalize score
        base_score = (honesty_indicators / total_activities) * 100
        return max(0, min(100, base_score + 50))  # Base score of 50

    async def _calculate_customer_focus_score(self, activities: List[EricSalesActivity]) -> float:
        """Calculate customer focus score"""
        if not activities:
            return 100.0
        
        customer_focus_indicators = 0
        total_activities = len(activities)
        
        for activity in activities:
            if activity.description:
                description_lower = activity.description.lower()
                
                # Customer focus indicators (positive)
                customer_phrases = [
                    "customer needs", "help", "solve", "benefit",
                    "value", "improve", "support", "assist",
                    "understand", "listen", "consult", "advise"
                ]
                
                for phrase in customer_phrases:
                    if phrase in description_lower:
                        customer_focus_indicators += 1
                        break
                
                # Self-focused indicators (negative)
                self_phrases = [
                    "my quota", "my commission", "my target",
                    "I need", "I want", "my goal"
                ]
                
                for phrase in self_phrases:
                    if phrase in description_lower:
                        customer_focus_indicators -= 1
                        break
        
        # Normalize score
        base_score = (customer_focus_indicators / total_activities) * 100
        return max(0, min(100, base_score + 50))  # Base score of 50

    async def _calculate_compliance_score(self, activities: List[EricSalesActivity]) -> float:
        """Calculate compliance score"""
        if not activities:
            return 100.0
        
        compliance_indicators = 0
        total_activities = len(activities)
        
        for activity in activities:
            if activity.description:
                description_lower = activity.description.lower()
                
                # Compliance indicators (positive)
                compliance_phrases = [
                    "compliance", "regulations", "legal", "approved",
                    "certified", "licensed", "authorized", "permitted"
                ]
                
                for phrase in compliance_phrases:
                    if phrase in description_lower:
                        compliance_indicators += 1
                        break
                
                # Non-compliance indicators (negative)
                non_compliance_phrases = [
                    "bypass", "ignore", "skip", "avoid",
                    "unapproved", "unauthorized", "illegal"
                ]
                
                for phrase in non_compliance_phrases:
                    if phrase in description_lower:
                        compliance_indicators -= 1
                        break
        
        # Normalize score
        base_score = (compliance_indicators / total_activities) * 100
        return max(0, min(100, base_score + 50))  # Base score of 50

    def _determine_risk_level(self, overall_score: float) -> str:
        """Determine risk level based on overall score"""
        if overall_score >= 90:
            return "low"
        elif overall_score >= 75:
            return "medium"
        elif overall_score >= 60:
            return "high"
        else:
            return "critical"

    async def _generate_ethical_recommendations(
        self, 
        transparency_score: float, 
        pressure_tactics_score: float, 
        honesty_score: float, 
        customer_focus_score: float, 
        compliance_score: float
    ) -> List[str]:
        """Generate ethical recommendations based on scores"""
        recommendations = []
        
        if transparency_score < 70:
            recommendations.append("Improve transparency by clearly explaining all terms and conditions upfront")
            recommendations.append("Provide detailed product information and pricing breakdowns")
        
        if pressure_tactics_score < 70:
            recommendations.append("Reduce pressure tactics - focus on value proposition instead of urgency")
            recommendations.append("Give customers time to make informed decisions")
        
        if honesty_score < 70:
            recommendations.append("Ensure all claims are accurate and verifiable")
            recommendations.append("Avoid exaggerating product benefits or features")
        
        if customer_focus_score < 70:
            recommendations.append("Focus on understanding and solving customer problems")
            recommendations.append("Prioritize customer needs over sales targets")
        
        if compliance_score < 70:
            recommendations.append("Review and follow all relevant industry regulations")
            recommendations.append("Ensure all sales practices meet legal requirements")
        
        if not recommendations:
            recommendations.append("Continue maintaining high ethical standards")
        
        return recommendations

    async def _identify_risk_factors(self, activity: EricSalesActivity) -> List[str]:
        """Identify potential risk factors in a sales activity"""
        risk_factors = []
        
        if not activity.description:
            return risk_factors
        
        description_lower = activity.description.lower()
        
        # Define risk patterns
        risk_patterns = {
            "pressure_tactics": [
                "limited time", "act now", "expires soon", "last chance",
                "urgent", "immediate", "today only", "final offer"
            ],
            "misleading_claims": [
                "guaranteed", "100% success", "no risk", "easy money",
                "get rich quick", "miracle", "secret", "exclusive"
            ],
            "hidden_costs": [
                "additional fees", "hidden charges", "fine print",
                "terms apply", "conditions apply"
            ],
            "aggressive_behavior": [
                "pressure", "push", "force", "insist", "demand",
                "must", "have to", "no choice"
            ]
        }
        
        for risk_type, patterns in risk_patterns.items():
            for pattern in patterns:
                if pattern in description_lower:
                    risk_factors.append(f"{risk_type}: {pattern}")
                    break
        
        return risk_factors

    async def _calculate_activity_ethical_score(
        self, 
        activity: EricSalesActivity, 
        risk_factors: List[str]
    ) -> float:
        """Calculate ethical score for a specific activity"""
        base_score = 100.0
        
        # Deduct points for each risk factor
        deduction_per_risk = 15.0
        total_deduction = len(risk_factors) * deduction_per_risk
        
        score = base_score - total_deduction
        return max(0, min(100, score))

    async def _generate_activity_suggestions(
        self, 
        activity: EricSalesActivity, 
        risk_factors: List[str]
    ) -> List[str]:
        """Generate suggestions for improving activity ethics"""
        suggestions = []
        
        for risk_factor in risk_factors:
            if "pressure_tactics" in risk_factor:
                suggestions.append("Focus on value proposition rather than urgency")
                suggestions.append("Give customers time to make informed decisions")
            
            elif "misleading_claims" in risk_factor:
                suggestions.append("Use accurate, verifiable claims only")
                suggestions.append("Provide evidence to support any statements")
            
            elif "hidden_costs" in risk_factor:
                suggestions.append("Be transparent about all costs upfront")
                suggestions.append("Provide clear pricing breakdowns")
            
            elif "aggressive_behavior" in risk_factor:
                suggestions.append("Adopt a consultative approach")
                suggestions.append("Listen to customer needs and concerns")
        
        if not suggestions:
            suggestions.append("Continue with current ethical approach")
        
        return suggestions

    async def _suggest_ethical_alternatives(
        self, 
        activity: EricSalesActivity, 
        risk_factors: List[str]
    ) -> List[str]:
        """Suggest ethical alternatives for risky activities"""
        alternatives = []
        
        if "pressure_tactics" in str(risk_factors):
            alternatives.append("Present value proposition with supporting data")
            alternatives.append("Offer to follow up after customer has time to consider")
        
        if "misleading_claims" in str(risk_factors):
            alternatives.append("Use specific, verifiable statistics and testimonials")
            alternatives.append("Provide case studies with real results")
        
        if "hidden_costs" in str(risk_factors):
            alternatives.append("Present complete pricing structure upfront")
            alternatives.append("Offer transparent payment plans")
        
        if "aggressive_behavior" in str(risk_factors):
            alternatives.append("Ask questions to understand customer needs")
            alternatives.append("Provide educational content to help decision-making")
        
        return alternatives

    async def _explain_ethical_benefits(self, alternatives: List[str]) -> List[str]:
        """Explain the benefits of ethical alternatives"""
        benefits = []
        
        for alternative in alternatives:
            if "value proposition" in alternative:
                benefits.append("Builds trust and credibility with customers")
            elif "follow up" in alternative:
                benefits.append("Shows respect for customer's decision-making process")
            elif "verifiable" in alternative:
                benefits.append("Reduces risk of legal issues and builds confidence")
            elif "transparent" in alternative:
                benefits.append("Prevents customer dissatisfaction and chargebacks")
            elif "understand customer needs" in alternative:
                benefits.append("Leads to better customer relationships and repeat business")
        
        return benefits

    def _calculate_severity(self, risk_factors: List[str]) -> str:
        """Calculate severity level of risk factors"""
        if len(risk_factors) >= 3:
            return "high"
        elif len(risk_factors) >= 1:
            return "medium"
        else:
            return "low"

    async def _generate_team_recommendations(self, team_scores: List[Dict]) -> List[str]:
        """Generate team-wide ethical recommendations"""
        recommendations = []
        
        # Analyze team patterns
        low_scores = [s for s in team_scores if s["score"].overall_score < 70]
        high_risk = [s for s in team_scores if s["score"].risk_level in ["high", "critical"]]
        
        if len(low_scores) > len(team_scores) * 0.3:  # More than 30% have low scores
            recommendations.append("Consider team-wide ethics training program")
        
        if len(high_risk) > 0:
            recommendations.append("Implement regular ethics reviews and coaching")
        
        recommendations.append("Establish clear ethical guidelines and best practices")
        recommendations.append("Create peer review system for sales activities")
        
        return recommendations

    async def _store_ethical_score(
        self, 
        db: Session, 
        sales_rep_id: int, 
        ethical_score: EthicalScore, 
        date_range: str
    ):
        """Store ethical score in database"""
        try:
            # Create or update ethical score record
            existing_score = db.query(EthicalSalesScore).filter(
                and_(
                    EthicalSalesScore.sales_rep_id == sales_rep_id,
                    EthicalSalesScore.date_range == date_range
                )
            ).first()
            
            if existing_score:
                existing_score.overall_score = ethical_score.overall_score
                existing_score.transparency_score = ethical_score.transparency_score
                existing_score.pressure_tactics_score = ethical_score.pressure_tactics_score
                existing_score.honesty_score = ethical_score.honesty_score
                existing_score.customer_focus_score = ethical_score.customer_focus_score
                existing_score.compliance_score = ethical_score.compliance_score
                existing_score.risk_level = ethical_score.risk_level
                existing_score.recommendations = json.dumps(ethical_score.recommendations)
                existing_score.updated_at = datetime.now()
            else:
                new_score = EthicalSalesScore(
                    sales_rep_id=sales_rep_id,
                    date_range=date_range,
                    overall_score=ethical_score.overall_score,
                    transparency_score=ethical_score.transparency_score,
                    pressure_tactics_score=ethical_score.pressure_tactics_score,
                    honesty_score=ethical_score.honesty_score,
                    customer_focus_score=ethical_score.customer_focus_score,
                    compliance_score=ethical_score.compliance_score,
                    risk_level=ethical_score.risk_level,
                    recommendations=json.dumps(ethical_score.recommendations),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_score)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            # Log error but don't fail the main operation
            print(f"Failed to store ethical score: {str(e)}")

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
            await self.kafka_producer.send_message("health_check", {"service": "ethical_sales_scoring"})
            kafka_status = "healthy"
        except Exception as e:
            kafka_status = f"unhealthy: {str(e)}"
        
        return {
            "service": "ethical_sales_scoring",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "redis": redis_status,
                "kafka": kafka_status
            }
        }
