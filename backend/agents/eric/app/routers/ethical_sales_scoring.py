from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..services.ethical_sales_scoring_service import (
    EthicalSalesScoringService, EthicalScore, SalesActivityEthicalAnalysis
)
from ..database import get_db
from core.authentication.auth import get_current_user

router = APIRouter(prefix="/ethical-sales-scoring", tags=["Ethical Sales Scoring"])

# Initialize service
ethical_scoring_service = EthicalSalesScoringService()


class ActivityAnalysisRequest(BaseModel):
    activity_id: int


@router.get("/score/{sales_rep_id}")
async def calculate_ethical_score(
    sales_rep_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> EthicalScore:
    """Calculate comprehensive ethical sales score for a sales rep"""
    try:
        score = await ethical_scoring_service.calculate_ethical_score(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        return score
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate ethical score: {str(e)}")


@router.get("/analyze-activity/{activity_id}")
async def analyze_activity_ethics(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SalesActivityEthicalAnalysis:
    """Analyze the ethical aspects of a specific sales activity"""
    try:
        analysis = await ethical_scoring_service.analyze_activity_ethics(
            db=db,
            activity_id=activity_id
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze activity ethics: {str(e)}")


@router.get("/team-report/{team_id}")
async def get_team_ethical_report(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive ethical report for entire team"""
    try:
        report = await ethical_scoring_service.get_team_ethical_report(
            db=db,
            team_id=team_id,
            date_range=date_range
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team ethical report: {str(e)}")


@router.get("/flag-aggressive-tactics/{sales_rep_id}")
async def flag_aggressive_tactics(
    sales_rep_id: int,
    date_range: str = Query("7d", description="Date range: 7d, 30d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Flag potentially aggressive sales tactics"""
    try:
        flagged_activities = await ethical_scoring_service.flag_aggressive_tactics(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        return flagged_activities
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to flag aggressive tactics: {str(e)}")


@router.post("/suggest-alternatives/{activity_id}")
async def suggest_ethical_alternatives(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Suggest ethical alternatives for a specific activity"""
    try:
        alternatives = await ethical_scoring_service.suggest_ethical_alternatives(
            db=db,
            activity_id=activity_id
        )
        return alternatives
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest alternatives: {str(e)}")


@router.get("/risk-assessment/{sales_rep_id}")
async def get_risk_assessment(
    sales_rep_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed risk assessment for a sales rep"""
    try:
        # Get ethical score
        ethical_score = await ethical_scoring_service.calculate_ethical_score(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        
        # Get flagged activities
        flagged_activities = await ethical_scoring_service.flag_aggressive_tactics(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        
        # Calculate risk metrics
        high_severity_count = len([a for a in flagged_activities if a["severity"] == "high"])
        medium_severity_count = len([a for a in flagged_activities if a["severity"] == "medium"])
        low_severity_count = len([a for a in flagged_activities if a["severity"] == "low"])
        
        # Determine overall risk level
        if ethical_score.risk_level == "critical" or high_severity_count > 5:
            overall_risk = "critical"
        elif ethical_score.risk_level == "high" or high_severity_count > 2:
            overall_risk = "high"
        elif ethical_score.risk_level == "medium" or medium_severity_count > 3:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        return {
            "sales_rep_id": sales_rep_id,
            "date_range": date_range,
            "overall_risk_level": overall_risk,
            "ethical_score": ethical_score.dict(),
            "flagged_activities_count": len(flagged_activities),
            "severity_breakdown": {
                "high": high_severity_count,
                "medium": medium_severity_count,
                "low": low_severity_count
            },
            "risk_factors": {
                "pressure_tactics": ethical_score.pressure_tactics_score < 70,
                "transparency_issues": ethical_score.transparency_score < 70,
                "honesty_concerns": ethical_score.honesty_score < 70,
                "customer_focus_issues": ethical_score.customer_focus_score < 70,
                "compliance_risks": ethical_score.compliance_score < 70
            },
            "recommendations": ethical_score.recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk assessment: {str(e)}")


@router.get("/compliance-report/{team_id}")
async def get_compliance_report(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get compliance-focused ethical report"""
    try:
        # Get team report
        team_report = await ethical_scoring_service.get_team_ethical_report(
            db=db,
            team_id=team_id,
            date_range=date_range
        )
        
        # Focus on compliance aspects
        compliance_scores = [score["compliance_score"] for score in team_report["individual_scores"]]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        # Identify compliance risks
        compliance_risks = [score for score in team_report["individual_scores"] if score["compliance_score"] < 70]
        
        # Generate compliance recommendations
        compliance_recommendations = []
        if avg_compliance < 80:
            compliance_recommendations.append("Implement mandatory compliance training for all team members")
        if len(compliance_risks) > 0:
            compliance_recommendations.append("Schedule individual compliance reviews for high-risk team members")
        compliance_recommendations.append("Establish regular compliance audits and monitoring")
        compliance_recommendations.append("Create clear compliance guidelines and best practices")
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "compliance_metrics": {
                "average_compliance_score": avg_compliance,
                "team_members_at_risk": len(compliance_risks),
                "compliance_risk_percentage": (len(compliance_risks) / len(team_report["individual_scores"]) * 100) if team_report["individual_scores"] else 0
            },
            "compliance_risks": compliance_risks,
            "compliance_recommendations": compliance_recommendations,
            "regulatory_considerations": [
                "Ensure all sales practices comply with industry regulations",
                "Maintain accurate records of all customer interactions",
                "Implement proper disclosure requirements",
                "Follow data protection and privacy laws"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance report: {str(e)}")


@router.get("/training-recommendations/{sales_rep_id}")
async def get_training_recommendations(
    sales_rep_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get personalized training recommendations based on ethical scores"""
    try:
        # Get ethical score
        ethical_score = await ethical_scoring_service.calculate_ethical_score(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        
        # Generate training recommendations based on scores
        training_modules = []
        
        if ethical_score.transparency_score < 70:
            training_modules.append({
                "module": "Transparency in Sales",
                "priority": "high",
                "description": "Learn to communicate clearly and honestly with customers",
                "topics": ["Clear communication", "Honest pricing", "Full disclosure", "Building trust"]
            })
        
        if ethical_score.pressure_tactics_score < 70:
            training_modules.append({
                "module": "Consultative Selling",
                "priority": "high",
                "description": "Focus on customer needs rather than pressure tactics",
                "topics": ["Needs analysis", "Value proposition", "Customer-centric approach", "Relationship building"]
            })
        
        if ethical_score.honesty_score < 70:
            training_modules.append({
                "module": "Ethical Communication",
                "priority": "high",
                "description": "Ensure all claims are accurate and verifiable",
                "topics": ["Fact-checking", "Evidence-based selling", "Avoiding exaggeration", "Credible testimonials"]
            })
        
        if ethical_score.customer_focus_score < 70:
            training_modules.append({
                "module": "Customer-Centric Selling",
                "priority": "medium",
                "description": "Put customer needs first in all interactions",
                "topics": ["Active listening", "Problem solving", "Customer advocacy", "Long-term relationships"]
            })
        
        if ethical_score.compliance_score < 70:
            training_modules.append({
                "module": "Sales Compliance",
                "priority": "high",
                "description": "Understand and follow all relevant regulations",
                "topics": ["Industry regulations", "Legal requirements", "Documentation", "Best practices"]
            })
        
        # Add general ethics training if overall score is low
        if ethical_score.overall_score < 75:
            training_modules.append({
                "module": "Sales Ethics Fundamentals",
                "priority": "high",
                "description": "Core principles of ethical selling",
                "topics": ["Ethical decision making", "Professional integrity", "Customer trust", "Long-term success"]
            })
        
        return {
            "sales_rep_id": sales_rep_id,
            "date_range": date_range,
            "ethical_score": ethical_score.overall_score,
            "risk_level": ethical_score.risk_level,
            "training_modules": training_modules,
            "total_modules": len(training_modules),
            "estimated_training_hours": len(training_modules) * 2,  # 2 hours per module
            "recommended_timeline": "Complete within 30 days" if ethical_score.risk_level in ["high", "critical"] else "Complete within 60 days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training recommendations: {str(e)}")


@router.get("/ethical-benchmarks")
async def get_ethical_benchmarks(
    industry: str = Query("general", description="Industry sector"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get industry benchmarks for ethical sales practices"""
    # Define industry benchmarks (in a real system, these would come from external data)
    benchmarks = {
        "general": {
            "transparency_score": 85,
            "pressure_tactics_score": 80,
            "honesty_score": 90,
            "customer_focus_score": 85,
            "compliance_score": 95
        },
        "technology": {
            "transparency_score": 80,
            "pressure_tactics_score": 75,
            "honesty_score": 85,
            "customer_focus_score": 80,
            "compliance_score": 90
        },
        "finance": {
            "transparency_score": 90,
            "pressure_tactics_score": 85,
            "honesty_score": 95,
            "customer_focus_score": 80,
            "compliance_score": 98
        },
        "healthcare": {
            "transparency_score": 95,
            "pressure_tactics_score": 90,
            "honesty_score": 98,
            "customer_focus_score": 90,
            "compliance_score": 99
        }
    }
    
    industry_benchmarks = benchmarks.get(industry, benchmarks["general"])
    
    return {
        "industry": industry,
        "benchmarks": industry_benchmarks,
        "description": f"Industry benchmarks for {industry} sector",
        "data_source": "Industry research and compliance standards",
        "last_updated": "2024-01-01"
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the ethical sales scoring service"""
    try:
        health_status = await ethical_scoring_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "ethical_sales_scoring",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
