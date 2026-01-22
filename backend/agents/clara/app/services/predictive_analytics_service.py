import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast, Date
from sqlalchemy.orm import selectinload
from core.ai import get_ai_service_manager, AIServiceManager
from ..database import get_clara_database
from ..models import (
    ClaraSupportTicket, ClaraCustomerInteraction, ClaraSupportAnalytics, CustomerProfile,
    TicketCategory, TicketPriority, SupportChannel, SentimentType
)

logger = logging.getLogger(__name__)

class PredictiveAnalyticsService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize predictive analytics service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Predictive analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize predictive analytics service: {e}")
            raise
    
    async def forecast_ticket_volume(
        self,
        days_ahead: int = 30,
        category: Optional[TicketCategory] = None,
        channel: Optional[SupportChannel] = None
    ) -> Dict[str, Any]:
        """Forecast ticket volume for the next N days"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get historical data for the last 90 days
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=90)
                
                # Build query
                query = select(
                    cast(ClaraSupportTicket.created_at, Date).label("date"),
                    func.count(ClaraSupportTicket.id).label("count")
                ).where(ClaraSupportTicket.created_at >= start_date)
                
                if category:
                    query = query.where(ClaraSupportTicket.category == category)
                if channel:
                    query = query.where(ClaraSupportTicket.channel == channel)
                
                query = query.group_by(cast(ClaraSupportTicket.created_at, Date)).order_by(
                    cast(ClaraSupportTicket.created_at, Date)
                )
                
                historical_data = await session.execute(query)
                historical_data = historical_data.all()
                
                # Calculate daily averages and trends
                if historical_data:
                    daily_counts = [row.count for row in historical_data]
                    avg_daily = sum(daily_counts) / len(daily_counts)
                    
                    # Simple trend calculation
                    if len(daily_counts) > 1:
                        trend = (daily_counts[-1] - daily_counts[0]) / len(daily_counts)
                    else:
                        trend = 0
                    
                    # Forecast based on trend
                    forecast = []
                    current_date = end_date
                    
                    for day in range(days_ahead):
                        current_date += timedelta(days=1)
                        # Adjust for day of week patterns
                        day_of_week = current_date.weekday()
                        day_factor = 1.0
                        
                        # Weekend factor (lower volume)
                        if day_of_week >= 5:  # Saturday = 5, Sunday = 6
                            day_factor = 0.7
                        
                        # Monday factor (higher volume)
                        elif day_of_week == 0:
                            day_factor = 1.2
                        
                        predicted_count = max(0, int((avg_daily + (trend * day)) * day_factor))
                        
                        forecast.append({
                            "date": current_date.strftime("%Y-%m-%d"),
                            "predicted_tickets": predicted_count,
                            "confidence": 0.8 - (day * 0.01)  # Confidence decreases over time
                        })
                    
                    return {
                        "success": True,
                        "forecast": forecast,
                        "metrics": {
                            "historical_avg_daily": round(avg_daily, 2),
                            "trend_per_day": round(trend, 2),
                            "confidence_level": "high" if days_ahead <= 7 else "medium" if days_ahead <= 14 else "low"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Insufficient historical data for forecasting"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to forecast ticket volume: {e}")
            return {"success": False, "error": str(e)}
    
    async def predict_customer_churn(
        self,
        customer_id: int,
        analysis_period_days: int = 90
    ) -> Dict[str, Any]:
        """Predict customer churn risk"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile and recent activity
                profile = await session.execute(
                    select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    return {"success": False, "error": "Customer profile not found"}
                
                # Get recent tickets
                cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)
                recent_tickets = await session.execute(
                    select(ClaraSupportTicket).where(
                        and_(
                            ClaraSupportTicket.customer_id == customer_id,
                            ClaraSupportTicket.created_at >= cutoff_date
                        )
                    ).order_by(ClaraSupportTicket.created_at.desc())
                )
                recent_tickets = recent_tickets.scalars().all()
                
                # Calculate churn risk factors
                risk_factors = []
                risk_score = 0.0
                
                # Factor 1: Recent activity (last 30 days)
                last_30_days = datetime.utcnow() - timedelta(days=30)
                recent_activity = [t for t in recent_tickets if t.created_at >= last_30_days]
                
                if not recent_activity:
                    risk_factors.append("no_recent_activity")
                    risk_score += 0.3
                
                # Factor 2: Satisfaction trend
                if profile.average_satisfaction and profile.average_satisfaction < 3.0:
                    risk_factors.append("low_satisfaction")
                    risk_score += 0.25
                
                # Factor 3: Resolution rate
                if profile.total_support_tickets > 0:
                    resolution_rate = profile.resolved_tickets / profile.total_support_tickets
                    if resolution_rate < 0.8:
                        risk_factors.append("low_resolution_rate")
                        risk_score += 0.2
                
                # Factor 4: Support frequency
                if len(recent_tickets) > 10:  # High support frequency
                    risk_factors.append("high_support_frequency")
                    risk_score += 0.15
                
                # Factor 5: Trust score
                if profile.trust_score and profile.trust_score < 0.5:
                    risk_factors.append("low_trust_score")
                    risk_score += 0.1
                
                # Determine risk level
                if risk_score >= 0.7:
                    risk_level = "high"
                elif risk_score >= 0.4:
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                # Generate recommendations
                recommendations = []
                if "no_recent_activity" in risk_factors:
                    recommendations.append("Reach out proactively to re-engage customer")
                if "low_satisfaction" in risk_factors:
                    recommendations.append("Review recent interactions and improve service quality")
                if "low_resolution_rate" in risk_factors:
                    recommendations.append("Focus on first-contact resolution and follow-up")
                if "high_support_frequency" in risk_factors:
                    recommendations.append("Provide proactive solutions to reduce support needs")
                if "low_trust_score" in risk_factors:
                    recommendations.append("Build trust through consistent, reliable service")
                
                return {
                    "success": True,
                    "churn_prediction": {
                        "customer_id": customer_id,
                        "risk_level": risk_level,
                        "risk_score": round(risk_score, 2),
                        "risk_factors": risk_factors,
                        "recommendations": recommendations,
                        "confidence": 0.85
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to predict customer churn: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_potential_issues(
        self,
        analysis_period_days: int = 7
    ) -> Dict[str, Any]:
        """Detect potential issues before they become widespread"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get recent tickets for pattern analysis
                cutoff_date = datetime.utcnow() - timedelta(days=analysis_period_days)
                recent_tickets = await session.execute(
                    select(ClaraSupportTicket).where(
                        ClaraSupportTicket.created_at >= cutoff_date
                    ).order_by(ClaraSupportTicket.created_at.desc())
                )
                recent_tickets = recent_tickets.scalars().all()
                
                if not recent_tickets:
                    return {"success": False, "error": "No recent tickets for analysis"}
                
                # Analyze patterns
                issues = []
                
                # Pattern 1: Sudden spike in specific category
                category_counts = {}
                for ticket in recent_tickets:
                    category = ticket.category.value
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                # Get historical averages for comparison
                historical_start = cutoff_date - timedelta(days=analysis_period_days * 2)
                historical_tickets = await session.execute(
                    select(ClaraSupportTicket).where(
                        ClaraSupportTicket.created_at >= historical_start
                    )
                )
                historical_tickets = historical_tickets.scalars().all()
                
                historical_category_counts = {}
                for ticket in historical_tickets:
                    if ticket.created_at < cutoff_date:
                        category = ticket.category.value
                        historical_category_counts[category] = historical_category_counts.get(category, 0) + 1
                
                # Calculate spikes
                for category, current_count in category_counts.items():
                    historical_count = historical_category_counts.get(category, 0)
                    if historical_count > 0:
                        increase_ratio = current_count / historical_count
                        if increase_ratio > 2.0:  # 100% increase
                            issues.append({
                                "type": "category_spike",
                                "category": category,
                                "current_count": current_count,
                                "historical_count": historical_count,
                                "increase_ratio": round(increase_ratio, 2),
                                "severity": "high" if increase_ratio > 3.0 else "medium",
                                "description": f"Sudden increase in {category} tickets"
                            })
                
                # Pattern 2: High priority ticket clusters
                high_priority_tickets = [t for t in recent_tickets if t.priority in [TicketPriority.HIGH, TicketPriority.URGENT, TicketPriority.CRITICAL]]
                if len(high_priority_tickets) > len(recent_tickets) * 0.3:  # More than 30% high priority
                    issues.append({
                        "type": "priority_cluster",
                        "high_priority_count": len(high_priority_tickets),
                        "total_count": len(recent_tickets),
                        "percentage": round((len(high_priority_tickets) / len(recent_tickets)) * 100, 1),
                        "severity": "high",
                        "description": "Unusually high number of high-priority tickets"
                    })
                
                # Pattern 3: Sentiment deterioration
                negative_tickets = [t for t in recent_tickets if t.sentiment_score and t.sentiment_score < -0.3]
                if negative_tickets:
                    avg_negative_sentiment = sum(t.sentiment_score for t in negative_tickets) / len(negative_tickets)
                    if avg_negative_sentiment < -0.5:
                        issues.append({
                            "type": "sentiment_deterioration",
                            "negative_tickets_count": len(negative_tickets),
                            "average_sentiment": round(avg_negative_sentiment, 2),
                            "severity": "medium",
                            "description": "Customer sentiment is deteriorating"
                        })
                
                # Pattern 4: Channel-specific issues
                channel_counts = {}
                for ticket in recent_tickets:
                    channel = ticket.channel.value
                    channel_counts[channel] = channel_counts.get(channel, 0) + 1
                
                for channel, count in channel_counts.items():
                    if count > len(recent_tickets) * 0.5:  # More than 50% from one channel
                        issues.append({
                            "type": "channel_dominance",
                            "channel": channel,
                            "count": count,
                            "percentage": round((count / len(recent_tickets)) * 100, 1),
                            "severity": "low",
                            "description": f"Unusual concentration of tickets from {channel} channel"
                        })
                
                return {
                    "success": True,
                    "potential_issues": issues,
                    "analysis_period_days": analysis_period_days,
                    "total_tickets_analyzed": len(recent_tickets),
                    "issues_found": len(issues)
                }
                
        except Exception as e:
            logger.error(f"Failed to detect potential issues: {e}")
            return {"success": False, "error": str(e)}
    
    async def benchmark_against_industry(
        self,
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Benchmark support performance against industry standards"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Default metrics to benchmark
                if not metrics:
                    metrics = [
                        "first_response_time",
                        "resolution_time",
                        "customer_satisfaction",
                        "first_contact_resolution_rate"
                    ]
                
                # Get current metrics
                current_metrics = {}
                
                if "first_response_time" in metrics:
                    # Calculate average first response time
                    response_times = await session.execute(
                        select(ClaraSupportTicket.first_response_time).where(
                            and_(
                                ClaraSupportTicket.first_response_time.isnot(None),
                                ClaraSupportTicket.created_at >= datetime.utcnow() - timedelta(days=30)
                            )
                        )
                    )
                    response_times = response_times.scalars().all()
                    if response_times:
                        avg_response_time = sum(response_times) / len(response_times)
                        current_metrics["first_response_time"] = round(avg_response_time, 2)
                
                if "resolution_time" in metrics:
                    # Calculate average resolution time
                    resolution_times = await session.execute(
                        select(ClaraSupportTicket.actual_resolution_time).where(
                            and_(
                                ClaraSupportTicket.actual_resolution_time.isnot(None),
                                ClaraSupportTicket.resolved_at >= datetime.utcnow() - timedelta(days=30)
                            )
                        )
                    )
                    resolution_times = resolution_times.scalars().all()
                    if resolution_times:
                        avg_resolution_time = sum(resolution_times) / len(resolution_times)
                        current_metrics["resolution_time"] = round(avg_resolution_time, 2)
                
                if "customer_satisfaction" in metrics:
                    # Calculate average satisfaction
                    satisfaction_scores = await session.execute(
                        select(ClaraSupportTicket.satisfaction_score).where(
                            and_(
                                ClaraSupportTicket.satisfaction_score.isnot(None),
                                ClaraSupportTicket.updated_at >= datetime.utcnow() - timedelta(days=30)
                            )
                        )
                    )
                    satisfaction_scores = satisfaction_scores.scalars().all()
                    if satisfaction_scores:
                        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                        current_metrics["customer_satisfaction"] = round(avg_satisfaction, 2)
                
                if "first_contact_resolution_rate" in metrics:
                    # Calculate FCR rate
                    total_tickets = await session.execute(
                        select(func.count(ClaraSupportTicket.id)).where(
                            ClaraSupportTicket.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    )
                    total_tickets = total_tickets.scalar()
                    
                    fcr_tickets = await session.execute(
                        select(func.count(ClaraSupportTicket.id)).where(
                            and_(
                                ClaraSupportTicket.created_at >= datetime.utcnow() - timedelta(days=30),
                                ClaraSupportTicket.interactions.any(ClaraCustomerInteraction.interaction_type == "resolution")
                            )
                        )
                    )
                    fcr_tickets = fcr_tickets.scalar()
                    
                    if total_tickets > 0:
                        fcr_rate = (fcr_tickets / total_tickets) * 100
                        current_metrics["first_contact_resolution_rate"] = round(fcr_rate, 2)
                
                # Industry benchmarks (from external data sources)
                industry_benchmarks = {
                    "first_response_time": {
                        "excellent": 15,  # minutes
                        "good": 30,
                        "average": 60,
                        "poor": 120
                    },
                    "resolution_time": {
                        "excellent": 120,  # minutes
                        "good": 240,
                        "average": 480,
                        "poor": 960
                    },
                    "customer_satisfaction": {
                        "excellent": 4.5,  # out of 5
                        "good": 4.0,
                        "average": 3.5,
                        "poor": 3.0
                    },
                    "first_contact_resolution_rate": {
                        "excellent": 85,  # percentage
                        "good": 75,
                        "average": 65,
                        "poor": 55
                    }
                }
                
                # Compare against benchmarks
                benchmark_results = {}
                for metric, value in current_metrics.items():
                    if metric in industry_benchmarks:
                        benchmark = industry_benchmarks[metric]
                        
                        # Determine performance level
                        if value >= benchmark["excellent"]:
                            performance_level = "excellent"
                        elif value >= benchmark["good"]:
                            performance_level = "good"
                        elif value >= benchmark["average"]:
                            performance_level = "average"
                        else:
                            performance_level = "poor"
                        
                        benchmark_results[metric] = {
                            "current_value": value,
                            "performance_level": performance_level,
                            "benchmarks": benchmark,
                            "gap_to_excellent": benchmark["excellent"] - value if value < benchmark["excellent"] else 0
                        }
                
                return {
                    "success": True,
                    "benchmark_results": benchmark_results,
                    "current_metrics": current_metrics,
                    "industry_benchmarks": industry_benchmarks,
                    "overall_performance": "excellent" if all(
                        result["performance_level"] in ["excellent", "good"] 
                        for result in benchmark_results.values()
                    ) else "good" if all(
                        result["performance_level"] in ["excellent", "good", "average"] 
                        for result in benchmark_results.values()
                    ) else "needs_improvement"
                }
                
        except Exception as e:
            logger.error(f"Failed to benchmark against industry: {e}")
            return {"success": False, "error": str(e)}
