from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.budget_control_service import BudgetControlService

router = APIRouter(prefix="/budget-control", tags=["Real-Time Budget Control"])

@router.post("/budget-rule")
def create_budget_rule(rule_name: str, budget_amount: float, rule_type: str = "daily", 
                      db: Session = Depends(get_db)):
    service = BudgetControlService(db)
    return service.create_budget_rule(rule_name, budget_amount, rule_type)

@router.post("/spending-limit")
def set_spending_limit(campaign_id: str, limit_amount: float, limit_period: str = "daily", 
                      db: Session = Depends(get_db)):
    service = BudgetControlService(db)
    return service.set_spending_limit(campaign_id, limit_amount, limit_period)

@router.post("/pacing-rule")
def create_pacing_rule(pacing_type: str, pacing_parameters: Dict[str, Any], 
                      db: Session = Depends(get_db)):
    service = BudgetControlService(db)
    return service.create_pacing_rule(pacing_type, pacing_parameters)

@router.post("/monitor-spending")
def monitor_budget_spending(campaign_id: str, current_spend: float, 
                           db: Session = Depends(get_db)):
    service = BudgetControlService(db)
    return service.monitor_budget_spending(campaign_id, current_spend)

@router.get("/analytics")
def get_budget_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = BudgetControlService(db)
    return service.get_budget_analytics(timeframe)
