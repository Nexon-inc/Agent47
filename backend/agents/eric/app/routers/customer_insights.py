from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.customer_insights_service import CustomerInsightsService
from ..database import get_db

router = APIRouter(prefix="/customer-insights", tags=["Customer Insights"])
customer_insights_service = CustomerInsightsService()

class CustomerBehaviorRequest(BaseModel):
    brand_id: int
    analysis_period: str = "30d"

class LeadJourneyRequest(BaseModel):
    brand_id: int
    lead_id: Optional[int] = None

class CustomerPreferencesRequest(BaseModel):
    brand_id: int
    customer_segment: Optional[str] = None

class CustomerChurnRequest(BaseModel):
    brand_id: int
    prediction_horizon: str = "30d"

@router.post("/analyze-behavior")
async def analyze_customer_behavior(request: CustomerBehaviorRequest):
    """Analyze customer behavior patterns"""
    try:
        result = await customer_insights_service.analyze_customer_behavior(
            brand_id=request.brand_id,
            analysis_period=request.analysis_period
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze customer behavior: {str(e)}")

@router.post("/analyze-lead-journey")
async def analyze_lead_journey(request: LeadJourneyRequest):
    """Analyze lead journey and touchpoints"""
    try:
        result = await customer_insights_service.analyze_lead_journey(
            brand_id=request.brand_id,
            lead_id=request.lead_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze lead journey: {str(e)}")

@router.post("/identify-preferences")
async def identify_customer_preferences(request: CustomerPreferencesRequest):
    """Identify customer preferences and buying patterns"""
    try:
        result = await customer_insights_service.identify_customer_preferences(
            brand_id=request.brand_id,
            customer_segment=request.customer_segment
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify customer preferences: {str(e)}")

@router.post("/predict-churn")
async def predict_customer_churn(request: CustomerChurnRequest):
    """Predict customer churn risk"""
    try:
        result = await customer_insights_service.predict_customer_churn(
            brand_id=request.brand_id,
            prediction_horizon=request.prediction_horizon
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict customer churn: {str(e)}")

@router.get("/customer-segments")
async def get_customer_segments(brand_id: int):
    """Get customer segments and their characteristics"""
    try:
        return {
            "brand_id": brand_id,
            "segments": {
                "high_value": {
                    "description": "High-value customers with significant revenue potential",
                    "characteristics": [
                        "High lead score (>0.8)",
                        "Large deal values",
                        "Strong engagement"
                    ],
                    "count": 25,
                    "avg_value": 50000
                },
                "engaged": {
                    "description": "Highly engaged customers with frequent interactions",
                    "characteristics": [
                        "High interaction frequency",
                        "Positive sentiment",
                        "Active participation"
                    ],
                    "count": 45,
                    "avg_value": 25000
                },
                "at_risk": {
                    "description": "Customers showing signs of churn risk",
                    "characteristics": [
                        "Low engagement",
                        "Negative sentiment",
                        "Declining activity"
                    ],
                    "count": 15,
                    "avg_value": 10000
                },
                "new": {
                    "description": "Recently acquired customers",
                    "characteristics": [
                        "Recent acquisition",
                        "Learning phase",
                        "High potential"
                    ],
                    "count": 30,
                    "avg_value": 15000
                }
            },
            "insights": [
                "High-value segment represents 20% of customers but 60% of revenue",
                "Engaged segment shows highest retention rates",
                "At-risk segment requires immediate attention"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer segments: {str(e)}")

@router.get("/behavior-patterns")
async def get_behavior_patterns(brand_id: int, pattern_type: str = "all"):
    """Get specific behavior patterns and trends"""
    try:
        return {
            "brand_id": brand_id,
            "pattern_type": pattern_type,
            "patterns": {
                "communication_preferences": {
                    "email": 0.45,
                    "phone": 0.25,
                    "chat": 0.20,
                    "social": 0.10
                },
                "engagement_timing": {
                    "peak_hours": [9, 14, 16],
                    "peak_days": ["Tuesday", "Wednesday", "Thursday"],
                    "response_times": {
                        "email": "2.5 hours",
                        "chat": "30 seconds",
                        "phone": "immediate"
                    }
                },
                "interaction_frequency": {
                    "high_engagement": 0.30,
                    "medium_engagement": 0.45,
                    "low_engagement": 0.25
                },
                "conversion_patterns": {
                    "avg_touchpoints_to_conversion": 8.5,
                    "avg_time_to_conversion": "45 days",
                    "conversion_by_channel": {
                        "email": 0.35,
                        "phone": 0.40,
                        "chat": 0.15,
                        "social": 0.10
                    }
                }
            },
            "trends": {
                "engagement_increasing": True,
                "response_times_improving": True,
                "conversion_rates_stable": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get behavior patterns: {str(e)}")

@router.get("/journey-maps")
async def get_journey_maps(brand_id: int):
    """Get customer journey maps and touchpoints"""
    try:
        return {
            "brand_id": brand_id,
            "journey_maps": {
                "awareness": {
                    "touchpoints": [
                        "Website visit",
                        "Social media engagement",
                        "Content consumption"
                    ],
                    "avg_duration": "7 days",
                    "conversion_rate": 0.15
                },
                "consideration": {
                    "touchpoints": [
                        "Product demo",
                        "Case study review",
                        "Pricing inquiry"
                    ],
                    "avg_duration": "14 days",
                    "conversion_rate": 0.35
                },
                "decision": {
                    "touchpoints": [
                        "Sales call",
                        "Proposal review",
                        "Contract negotiation"
                    ],
                    "avg_duration": "21 days",
                    "conversion_rate": 0.60
                },
                "onboarding": {
                    "touchpoints": [
                        "Account setup",
                        "Training session",
                        "First success milestone"
                    ],
                    "avg_duration": "30 days",
                    "success_rate": 0.85
                }
            },
            "bottlenecks": [
                {
                    "stage": "consideration",
                    "issue": "Long response times to inquiries",
                    "impact": "Medium",
                    "recommendation": "Implement automated response system"
                },
                {
                    "stage": "decision",
                    "issue": "Complex contract process",
                    "impact": "High",
                    "recommendation": "Simplify contract terms and process"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get journey maps: {str(e)}")

@router.get("/preference-analysis")
async def get_preference_analysis(brand_id: int):
    """Get detailed customer preference analysis"""
    try:
        return {
            "brand_id": brand_id,
            "preferences": {
                "communication_channels": {
                    "email": {
                        "preference_score": 0.45,
                        "response_rate": 0.25,
                        "best_times": ["9-11 AM", "2-4 PM"]
                    },
                    "phone": {
                        "preference_score": 0.25,
                        "response_rate": 0.80,
                        "best_times": ["10-12 PM", "3-5 PM"]
                    },
                    "chat": {
                        "preference_score": 0.20,
                        "response_rate": 0.90,
                        "best_times": ["All day"]
                    },
                    "social": {
                        "preference_score": 0.10,
                        "response_rate": 0.15,
                        "best_times": ["Evening hours"]
                    }
                },
                "content_preferences": {
                    "case_studies": 0.35,
                    "product_demos": 0.30,
                    "pricing_guides": 0.20,
                    "technical_docs": 0.15
                },
                "interaction_style": {
                    "formal": 0.40,
                    "casual": 0.35,
                    "technical": 0.25
                },
                "decision_factors": {
                    "price": 0.30,
                    "features": 0.25,
                    "support": 0.20,
                    "reputation": 0.15,
                    "ease_of_use": 0.10
                }
            },
            "recommendations": [
                "Focus on email communication during business hours",
                "Provide case studies for high-value prospects",
                "Maintain formal tone for enterprise customers",
                "Emphasize support quality in sales conversations"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preference analysis: {str(e)}")

@router.get("/churn-indicators")
async def get_churn_indicators(brand_id: int):
    """Get churn risk indicators and early warning signs"""
    try:
        return {
            "brand_id": brand_id,
            "churn_indicators": {
                "high_risk": [
                    {
                        "indicator": "No activity for 30+ days",
                        "risk_score": 0.9,
                        "affected_customers": 15,
                        "intervention": "Immediate re-engagement campaign"
                    },
                    {
                        "indicator": "Negative sentiment in interactions",
                        "risk_score": 0.8,
                        "affected_customers": 8,
                        "intervention": "Escalation to customer success team"
                    },
                    {
                        "indicator": "Declining usage patterns",
                        "risk_score": 0.7,
                        "affected_customers": 12,
                        "intervention": "Usage optimization consultation"
                    }
                ],
                "medium_risk": [
                    {
                        "indicator": "Reduced interaction frequency",
                        "risk_score": 0.6,
                        "affected_customers": 25,
                        "intervention": "Proactive check-in calls"
                    },
                    {
                        "indicator": "Support ticket escalation",
                        "risk_score": 0.5,
                        "affected_customers": 10,
                        "intervention": "Enhanced support and training"
                    }
                ],
                "low_risk": [
                    {
                        "indicator": "Minor feature requests",
                        "risk_score": 0.3,
                        "affected_customers": 30,
                        "intervention": "Regular feature updates"
                    }
                ]
            },
            "retention_strategies": [
                "Implement proactive customer success program",
                "Develop personalized re-engagement campaigns",
                "Create customer health scoring system",
                "Establish early warning alert system"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get churn indicators: {str(e)}")

@router.get("/insights-dashboard")
async def get_insights_dashboard(brand_id: int):
    """Get comprehensive customer insights dashboard"""
    try:
        return {
            "brand_id": brand_id,
            "dashboard": {
                "overview": {
                    "total_customers": 150,
                    "active_customers": 135,
                    "at_risk_customers": 15,
                    "avg_customer_lifetime_value": 35000
                },
                "key_metrics": {
                    "customer_satisfaction": 0.85,
                    "net_promoter_score": 72,
                    "customer_retention_rate": 0.90,
                    "avg_time_to_value": "45 days"
                },
                "trends": {
                    "customer_growth": "+15%",
                    "engagement_increase": "+25%",
                    "churn_reduction": "-10%",
                    "satisfaction_improvement": "+5%"
                },
                "alerts": [
                    {
                        "type": "high_risk",
                        "message": "5 customers showing churn indicators",
                        "priority": "high",
                        "action_required": True
                    },
                    {
                        "type": "opportunity",
                        "message": "20 customers ready for upsell",
                        "priority": "medium",
                        "action_required": False
                    }
                ]
            },
            "recommendations": [
                "Focus on at-risk customer segment",
                "Develop upsell opportunities",
                "Improve onboarding process",
                "Enhance customer success program"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights dashboard: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for customer insights service"""
    return {
        "status": "healthy",
        "service": "customer_insights",
        "timestamp": datetime.now().isoformat()
    }
