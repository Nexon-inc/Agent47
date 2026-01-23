import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieBudgetRule, SpendingLimit, BudgetAlert, PacingRule

class BudgetControlService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_budget_rule(self, rule_name: str, budget_amount: float, rule_type: str = "daily") -> Dict[str, Any]:
        rule_id = str(uuid.uuid4())
        
        prompt = f"""
        Rule Name: {rule_name}
        Budget Amount: {budget_amount}
        Rule Type: {rule_type}
        
        Create a budget control rule with spending limits and alerts.
        """
        
        rule_result = self.nlp_processor.create_budget_rule(prompt)
        
        rule = JackieBudgetRule(
            id=rule_id, rule_name=rule_name, budget_amount=budget_amount, rule_type=rule_type,
            rule_config=json.dumps(rule_result), created_at=datetime.utcnow()
        )
        self.db.add(rule)
        self.db.commit()
        
        return {"rule_id": rule_id, "rule_config": rule_result}
    
    def set_spending_limit(self, campaign_id: str, limit_amount: float, limit_period: str = "daily") -> Dict[str, Any]:
        limit_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Limit Amount: {limit_amount}
        Limit Period: {limit_period}
        
        Set a spending limit for the campaign with real-time monitoring.
        """
        
        limit_result = self.nlp_processor.set_spending_limit(prompt)
        
        limit = SpendingLimit(
            id=limit_id, campaign_id=campaign_id, limit_amount=limit_amount, limit_period=limit_period,
            limit_config=json.dumps(limit_result), created_at=datetime.utcnow()
        )
        self.db.add(limit)
        self.db.commit()
        
        return {"limit_id": limit_id, "limit_config": limit_result}
    
    def create_pacing_rule(self, pacing_type: str, pacing_parameters: Dict[str, Any]) -> Dict[str, Any]:
        pacing_id = str(uuid.uuid4())
        
        prompt = f"""
        Pacing Type: {pacing_type}
        Pacing Parameters: {pacing_parameters}
        
        Create a budget pacing rule to control spending over time.
        """
        
        pacing_result = self.nlp_processor.create_pacing_rule(prompt)
        
        pacing = PacingRule(
            id=pacing_id, pacing_type=pacing_type, pacing_parameters=json.dumps(pacing_parameters),
            pacing_config=json.dumps(pacing_result), created_at=datetime.utcnow()
        )
        self.db.add(pacing)
        self.db.commit()
        
        return {"pacing_id": pacing_id, "pacing_config": pacing_result}
    
    def monitor_budget_spending(self, campaign_id: str, current_spend: float) -> Dict[str, Any]:
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Current Spend: {current_spend}
        
        Monitor budget spending and generate alerts if needed.
        """
        
        monitoring_result = self.nlp_processor.monitor_budget_spending(prompt)
        
        if monitoring_result.get("alert_needed", False):
            alert = BudgetAlert(
                id=str(uuid.uuid4()), campaign_id=campaign_id, current_spend=current_spend,
                alert_message=monitoring_result.get("alert_message", ""), created_at=datetime.utcnow()
            )
            self.db.add(alert)
            self.db.commit()
        
        return {
            "campaign_id": campaign_id, "current_spend": current_spend,
            "monitoring_result": monitoring_result
        }
    
    def get_budget_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        rules_created = self.db.query(JackieBudgetRule).filter(JackieBudgetRule.created_at >= cutoff_date).count()
        limits_set = self.db.query(SpendingLimit).filter(SpendingLimit.created_at >= cutoff_date).count()
        alerts_generated = self.db.query(BudgetAlert).filter(BudgetAlert.created_at >= cutoff_date).count()
        pacing_rules = self.db.query(PacingRule).filter(PacingRule.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "rules_created": rules_created,
            "limits_set": limits_set, "alerts_generated": alerts_generated,
            "pacing_rules": pacing_rules
        }
