from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.ai_lead_prioritization_service import AILeadPrioritizationService
from ..database import get_eric_database

router = APIRouter()

class PrioritizeLeadsRequest(BaseModel):
    lead_ids: Optional[List[int]] = None
    rep_id: Optional[int] = None
    limit: int = 50

class IntentSignalRequest(BaseModel):
    lead_id: int
    signal_type: str
    signal_data: Dict[str, Any]

class UpdateWeightsRequest(BaseModel):
    new_weights: Dict[str, Dict[str, Any]]

class PrioritizeLeadsResponse(BaseModel):
    success: bool
    prioritized_leads: List[Dict[str, Any]]
    total_leads: int
    prioritization_date: str
    error: Optional[str] = None

class IntentSignalResponse(BaseModel):
    success: bool
    signal_tracked: bool
    lead_id: int
    signal_type: str
    timestamp: str
    error: Optional[str] = None

class LeadPriorityDetailsResponse(BaseModel):
    success: bool
    lead_id: int
    lead_info: Dict[str, Any]
    priority_analysis: Dict[str, Any]
    recent_intent_signals: List[Dict[str, Any]]
    engagement_history: List[Dict[str, Any]]
    similar_leads_comparison: Dict[str, Any]
    recommendations: List[str]
    error: Optional[str] = None

class PrioritizationInsightsResponse(BaseModel):
    success: bool
    insights: Dict[str, Any]
    analysis_period: str
    error: Optional[str] = None

@router.post("/prioritization/prioritize", response_model=PrioritizeLeadsResponse)
async def prioritize_leads(request: PrioritizeLeadsRequest):
    """Prioritize leads based on AI analysis of intent signals and characteristics"""
    try:
        service = AILeadPrioritizationService()
        result = await service.prioritize_leads(
            request.lead_ids,
            request.rep_id,
            request.limit
        )
        
        if result["success"]:
            return PrioritizeLeadsResponse(
                success=True,
                prioritized_leads=result["prioritized_leads"],
                total_leads=result["total_leads"],
                prioritization_date=result["prioritization_date"]
            )
        else:
            return PrioritizeLeadsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prioritization/track-signal", response_model=IntentSignalResponse)
async def track_intent_signal(request: IntentSignalRequest):
    """Track an intent signal for a lead"""
    try:
        service = AILeadPrioritizationService()
        result = await service.track_intent_signal(
            request.lead_id,
            request.signal_type,
            request.signal_data
        )
        
        if result["success"]:
            return IntentSignalResponse(
                success=True,
                signal_tracked=result["signal_tracked"],
                lead_id=result["lead_id"],
                signal_type=result["signal_type"],
                timestamp=result["timestamp"]
            )
        else:
            return IntentSignalResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/lead-details/{lead_id}", response_model=LeadPriorityDetailsResponse)
async def get_lead_priority_details(lead_id: int):
    """Get detailed priority analysis for a specific lead"""
    try:
        service = AILeadPrioritizationService()
        result = await service.get_lead_priority_details(lead_id)
        
        if result["success"]:
            return LeadPriorityDetailsResponse(
                success=True,
                lead_id=result["lead_id"],
                lead_info=result["lead_info"],
                priority_analysis=result["priority_analysis"],
                recent_intent_signals=result["recent_intent_signals"],
                engagement_history=result["engagement_history"],
                similar_leads_comparison=result["similar_leads_comparison"],
                recommendations=result["recommendations"]
            )
        else:
            return LeadPriorityDetailsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prioritization/update-weights")
async def update_prioritization_weights(request: UpdateWeightsRequest):
    """Update the weights for intent signals and characteristics"""
    try:
        service = AILeadPrioritizationService()
        result = await service.update_prioritization_weights(request.new_weights)
        
        if result["success"]:
            return {
                "success": True,
                "weights_updated": result["weights_updated"],
                "current_weights": result["current_weights"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/insights", response_model=PrioritizationInsightsResponse)
async def get_prioritization_insights(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get insights about lead prioritization performance"""
    try:
        service = AILeadPrioritizationService()
        result = await service.get_prioritization_insights(rep_id, days)
        
        if result["success"]:
            return PrioritizationInsightsResponse(
                success=True,
                insights=result["insights"],
                analysis_period=result["analysis_period"]
            )
        else:
            return PrioritizationInsightsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/signal-types")
async def get_available_signal_types():
    """Get available intent signal types and their configurations"""
    try:
        service = AILeadPrioritizationService()
        return {
            "success": True,
            "signal_types": service.intent_signals,
            "total_signals": len(service.intent_signals)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/characteristics")
async def get_lead_characteristics():
    """Get lead characteristics scoring configuration"""
    try:
        service = AILeadPrioritizationService()
        return {
            "success": True,
            "characteristics": service.lead_characteristics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/priority-levels")
async def get_priority_levels():
    """Get priority level definitions and score ranges"""
    try:
        return {
            "success": True,
            "priority_levels": {
                "critical": {
                    "score_range": "80-100",
                    "description": "Highest priority, immediate action required",
                    "recommended_action": "immediate_call"
                },
                "high": {
                    "score_range": "60-79",
                    "description": "High priority, schedule follow-up",
                    "recommended_action": "schedule_demo"
                },
                "medium": {
                    "score_range": "40-59",
                    "description": "Medium priority, nurture engagement",
                    "recommended_action": "send_personalized_email"
                },
                "low": {
                    "score_range": "20-39",
                    "description": "Low priority, continue nurturing",
                    "recommended_action": "nurture_sequence"
                },
                "very_low": {
                    "score_range": "0-19",
                    "description": "Very low priority, re-engagement needed",
                    "recommended_action": "re-engage_campaign"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/performance-metrics")
async def get_performance_metrics(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get performance metrics for lead prioritization"""
    try:
        service = AILeadPrioritizationService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity, Lead
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get prioritization activities
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "lead_prioritization",
                    SalesActivity.created_at >= start_date
                )
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Calculate metrics
            total_prioritizations = len(activities)
            average_scores = []
            priority_distribution = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "very_low": 0
            }
            
            for activity in activities:
                metadata = activity.metadata or {}
                if "total_score" in metadata:
                    average_scores.append(metadata["total_score"])
                
                priority_level = metadata.get("priority_level", "medium")
                if priority_level in priority_distribution:
                    priority_distribution[priority_level] += 1
            
            avg_score = sum(average_scores) / len(average_scores) if average_scores else 0
            
            # Calculate conversion rate
            conversion_query = select(func.count(Lead.id)).where(
                and_(
                    Lead.status == "converted",
                    Lead.updated_at >= start_date
                )
            )
            
            if rep_id:
                conversion_query = conversion_query.where(Lead.assigned_rep_id == rep_id)
            
            conversion_result = await session.execute(conversion_query)
            converted_leads = conversion_result.scalar()
            
            conversion_rate = (converted_leads / total_prioritizations * 100) if total_prioritizations > 0 else 0
            
            return {
                "success": True,
                "metrics": {
                    "total_prioritizations": total_prioritizations,
                    "average_priority_score": round(avg_score, 2),
                    "conversion_rate": round(conversion_rate, 2),
                    "priority_distribution": priority_distribution,
                    "analysis_period_days": days
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/trends")
async def get_prioritization_trends(
    days: int = Query(30, description="Number of days to analyze"),
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID")
):
    """Get trends in lead prioritization over time"""
    try:
        service = AILeadPrioritizationService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily prioritization counts
            query = select(
                func.date(SalesActivity.created_at).label("date"),
                func.count(SalesActivity.id).label("count"),
                func.avg(SalesActivity.metadata["total_score"].astext.cast(func.float)).label("avg_score")
            ).where(
                and_(
                    SalesActivity.activity_type == "lead_prioritization",
                    SalesActivity.created_at >= start_date
                )
            ).group_by(
                func.date(SalesActivity.created_at)
            ).order_by(
                func.date(SalesActivity.created_at)
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            result = await session.execute(query)
            trends = result.all()
            
            # Format trends data
            trends_data = []
            for trend in trends:
                trends_data.append({
                    "date": trend.date.isoformat(),
                    "prioritization_count": trend.count,
                    "average_score": round(float(trend.avg_score or 0), 2)
                })
            
            return {
                "success": True,
                "trends": trends_data,
                "analysis_period_days": days
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prioritization/recommendations")
async def get_prioritization_recommendations(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID")
):
    """Get recommendations for improving lead prioritization"""
    try:
        service = AILeadPrioritizationService()
        
        # Get insights for recommendations
        insights_result = await service.get_prioritization_insights(rep_id, 30)
        
        if not insights_result["success"]:
            return {"success": False, "error": insights_result["error"]}
        
        insights = insights_result["insights"]
        recommendations = []
        
        # Generate recommendations based on insights
        if insights["total_prioritizations"] < 10:
            recommendations.append({
                "category": "frequency",
                "recommendation": "Increase lead prioritization frequency for better insights",
                "priority": "medium"
            })
        
        if insights["average_priority_score"] < 50:
            recommendations.append({
                "category": "scoring",
                "recommendation": "Review and adjust intent signal weights",
                "priority": "high"
            })
            recommendations.append({
                "category": "qualification",
                "recommendation": "Focus on improving lead qualification criteria",
                "priority": "high"
            })
        
        if insights["conversion_rate"] < 10:
            recommendations.append({
                "category": "nurturing",
                "recommendation": "Improve lead nurturing processes",
                "priority": "high"
            })
            recommendations.append({
                "category": "follow_up",
                "recommendation": "Review sales follow-up procedures",
                "priority": "medium"
            })
        
        # Add general recommendations
        recommendations.append({
            "category": "monitoring",
            "recommendation": "Continue monitoring and optimizing prioritization",
            "priority": "low"
        })
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
