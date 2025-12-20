from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..services.objection_prediction_service import (
    ObjectionPredictionService, PredictedObjection, ObjectionType, ObjectionPredictionModel
)
from ..database import get_db
from core.authentication.auth import get_current_user

router = APIRouter(prefix="/objection-prediction", tags=["Objection Prediction"])

# Initialize service
objection_service = ObjectionPredictionService()


class ModelTrainingRequest(BaseModel):
    model_name: str = "objection_predictor_v2"


@router.get("/predict/{lead_id}")
async def predict_objections(
    lead_id: int,
    sales_rep_id: int = Query(..., description="Sales representative ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[PredictedObjection]:
    """Predict potential objections for a specific lead"""
    try:
        predictions = await objection_service.predict_objections(
            db=db,
            lead_id=lead_id,
            sales_rep_id=sales_rep_id
        )
        return predictions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict objections: {str(e)}")


@router.get("/objection-types")
async def get_objection_types(
    category: Optional[str] = Query(None, description="Filter by objection category"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[ObjectionType]:
    """Get available objection types and categories"""
    try:
        objection_types = await objection_service.get_objection_types(
            db=db,
            category=category
        )
        return objection_types
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get objection types: {str(e)}")


@router.get("/analytics/{sales_rep_id}")
async def get_prediction_analytics(
    sales_rep_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics for objection prediction performance"""
    try:
        analytics = await objection_service.get_prediction_analytics(
            db=db,
            sales_rep_id=sales_rep_id,
            date_range=date_range
        )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.post("/train-model")
async def train_prediction_model(
    request: ModelTrainingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ObjectionPredictionModel:
    """Train or retrain the objection prediction model"""
    try:
        model = await objection_service.train_prediction_model(
            db=db,
            model_name=request.model_name
        )
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to train model: {str(e)}")


@router.get("/responses/{objection_type}")
async def get_objection_responses(
    objection_type: str,
    company_size: str = Query(..., description="Company size: small, medium, large, enterprise"),
    industry: str = Query(..., description="Industry"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[str]:
    """Get suggested responses for specific objection types"""
    try:
        customer_profile = {
            "company_size": company_size,
            "industry": industry
        }
        
        responses = await objection_service.get_objection_responses(
            db=db,
            objection_type=objection_type,
            customer_profile=customer_profile
        )
        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get responses: {str(e)}")


@router.get("/categories")
async def get_objection_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available objection categories"""
    try:
        objection_types = await objection_service.get_objection_types(db=db)
        
        # Group by category
        categories = {}
        for obj_type in objection_types:
            category = obj_type.category
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "objection_id": obj_type.objection_id,
                "description": obj_type.description,
                "impact_level": obj_type.impact_level
            })
        
        return {
            "categories": categories,
            "total_objection_types": len(objection_types),
            "total_categories": len(categories)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/performance/team/{team_id}")
async def get_team_prediction_performance(
    team_id: int,
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get team-wide objection prediction performance"""
    try:
        # Get all sales reps in the team
        sales_reps = db.query(SalesRep).filter(SalesRep.team_id == team_id).all()
        
        if not sales_reps:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team_analytics = []
        total_predictions = 0
        total_accurate = 0
        
        for rep in sales_reps:
            try:
                analytics = await objection_service.get_prediction_analytics(
                    db=db,
                    sales_rep_id=rep.id,
                    date_range=date_range
                )
                team_analytics.append({
                    "sales_rep_id": rep.id,
                    "sales_rep_name": f"{rep.first_name} {rep.last_name}",
                    "analytics": analytics
                })
                
                total_predictions += analytics["metrics"]["total_predictions"]
                total_accurate += analytics["metrics"]["accurate_predictions"]
                
            except Exception as e:
                # Continue with other reps if one fails
                continue
        
        # Calculate team averages
        team_accuracy = (total_accurate / total_predictions * 100) if total_predictions > 0 else 0
        
        return {
            "team_id": team_id,
            "date_range": date_range,
            "team_summary": {
                "total_predictions": total_predictions,
                "total_accurate": total_accurate,
                "team_accuracy": team_accuracy,
                "active_sales_reps": len(sales_reps)
            },
            "individual_performance": team_analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team performance: {str(e)}")


@router.get("/insights/{lead_id}")
async def get_lead_objection_insights(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed objection insights for a specific lead"""
    try:
        # Get lead information
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get customer profile
        customer = db.query(CustomerProfile).filter(
            CustomerProfile.id == lead.customer_id
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get predictions for this lead
        predictions = await objection_service.predict_objections(
            db=db,
            lead_id=lead_id,
            sales_rep_id=lead.sales_rep_id
        )
        
        # Get objection types
        objection_types = await objection_service.get_objection_types(db=db)
        
        # Analyze lead characteristics
        lead_analysis = {
            "lead_value": lead.value,
            "company_size": lead.company_size,
            "industry": lead.industry,
            "region": lead.region,
            "risk_factors": []
        }
        
        # Identify risk factors
        if lead.value > 100000:
            lead_analysis["risk_factors"].append("high_value_deal")
        if lead.company_size == "small":
            lead_analysis["risk_factors"].append("small_company_budget")
        if lead.industry in ["technology", "finance"]:
            lead_analysis["risk_factors"].append("competitive_industry")
        
        return {
            "lead_id": lead_id,
            "lead_analysis": lead_analysis,
            "customer_profile": {
                "company_name": customer.company_name,
                "industry": customer.industry,
                "company_size": customer.company_size
            },
            "predicted_objections": [pred.dict() for pred in predictions],
            "objection_types_available": len(objection_types),
            "recommendations": [
                "Focus on value proposition for high-value deals",
                "Provide flexible payment options for small companies",
                "Address competitive concerns proactively"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lead insights: {str(e)}")


@router.get("/trends/objection-types")
async def get_objection_type_trends(
    date_range: str = Query("30d", description="Date range: 7d, 30d, 90d"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get trends in objection types over time"""
    try:
        # This would typically query historical prediction data
        # For now, return simulated trend data
        trends = {
            "date_range": date_range,
            "trends": {
                "price": {"trend": "increasing", "change_percentage": 15},
                "timing": {"trend": "stable", "change_percentage": 2},
                "authority": {"trend": "decreasing", "change_percentage": -8},
                "competition": {"trend": "increasing", "change_percentage": 12},
                "need": {"trend": "stable", "change_percentage": 1}
            },
            "most_common_objection": "price",
            "least_common_objection": "authority",
            "insights": [
                "Price objections are increasing due to economic factors",
                "Authority objections are decreasing as decision-making becomes more streamlined",
                "Competition objections are rising in competitive markets"
            ]
        }
        
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for the objection prediction service"""
    try:
        health_status = await objection_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "objection_prediction",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
