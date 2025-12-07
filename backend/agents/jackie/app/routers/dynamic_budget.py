from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.dynamic_budget_service import DynamicBudgetService

router = APIRouter(prefix="/dynamic-budget", tags=["Dynamic Budget Allocator"])

@router.post("/budget-allocation")
def create_budget_allocation(campaign_id: str, total_budget: float, allocation_rules: Dict[str, Any], 
                           db: Session = Depends(get_db)):
    service = DynamicBudgetService(db)
    return service.create_budget_allocation(campaign_id, total_budget, allocation_rules)

@router.post("/adjust-budget")
def adjust_budget_based_on_performance(campaign_id: str, current_performance: Dict[str, Any], 
                                     db: Session = Depends(get_db)):
    service = DynamicBudgetService(db)
    return service.adjust_budget_based_on_performance(campaign_id, current_performance)

@router.post("/performance-thresholds")
def set_performance_thresholds(threshold_type: str, threshold_values: Dict[str, Any], 
                             db: Session = Depends(get_db)):
    service = DynamicBudgetService(db)
    return service.set_performance_thresholds(threshold_type, threshold_values)

@router.get("/analytics")
def get_dynamic_budget_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = DynamicBudgetService(db)
    return service.get_dynamic_budget_analytics(timeframe)
