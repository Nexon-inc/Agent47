import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieBudgetAllocation, AllocationRule, JackiePerformanceThreshold, JackieBudgetAdjustment

class DynamicBudgetService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_budget_allocation(self, campaign_id: str, total_budget: float, allocation_rules: Dict[str, Any]) -> Dict[str, Any]:
        allocation_id = str(uuid.uuid4())
        
        prompt = f"""
        Campaign ID: {campaign_id}
        Total Budget: {total_budget}
        Allocation Rules: {allocation_rules}
        
        Create a dynamic budget allocation strategy based on performance rules.
        """
        
        allocation_result = self.nlp_processor.create_budget_allocation(prompt)
        
        allocation = JackieBudgetAllocation(
            id=allocation_id, campaign_id=campaign_id, total_budget=total_budget,
            allocation_rules=json.dumps(allocation_rules), allocation_data=json.dumps(allocation_result),
            created_at=datetime.utcnow()
        )
        self.db.add(allocation)
        self.db.commit()
        
        return {"allocation_id": allocation_id, "allocation_data": allocation_result}
    
    def adjust_budget_based_on_performance(self, campaign_id: str, current_performance: Dict[str, Any]) -> Dict[str, Any]:
        adjustment_id = str(uuid.uuid4())
        
        prompt = f"""
        Campaign ID: {campaign_id}
        Current Performance: {current_performance}
        
        Adjust budget allocation based on real-time performance metrics.
        """
        
        adjustment_result = self.nlp_processor.adjust_budget_based_on_performance(prompt)
        
        adjustment = JackieBudgetAdjustment(
            id=adjustment_id, campaign_id=campaign_id, current_performance=json.dumps(current_performance),
            adjustment_data=json.dumps(adjustment_result), created_at=datetime.utcnow()
        )
        self.db.add(adjustment)
        self.db.commit()
        
        return {"adjustment_id": adjustment_id, "adjustment_data": adjustment_result}
    
    def set_performance_thresholds(self, threshold_type: str, threshold_values: Dict[str, Any]) -> Dict[str, Any]:
        threshold_id = str(uuid.uuid4())
        
        prompt = f"""
        Threshold Type: {threshold_type}
        Threshold Values: {threshold_values}
        
        Set performance thresholds for automatic budget adjustments.
        """
        
        threshold_result = self.nlp_processor.set_performance_thresholds(prompt)
        
        threshold = JackiePerformanceThreshold(
            id=threshold_id, threshold_type=threshold_type, threshold_values=json.dumps(threshold_values),
            threshold_config=json.dumps(threshold_result), created_at=datetime.utcnow()
        )
        self.db.add(threshold)
        self.db.commit()
        
        return {"threshold_id": threshold_id, "threshold_config": threshold_result}
    
    def get_dynamic_budget_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        allocations_created = self.db.query(JackieBudgetAllocation).filter(JackieBudgetAllocation.created_at >= cutoff_date).count()
        adjustments_made = self.db.query(JackieBudgetAdjustment).filter(JackieBudgetAdjustment.created_at >= cutoff_date).count()
        thresholds_set = self.db.query(JackiePerformanceThreshold).filter(JackiePerformanceThreshold.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "allocations_created": allocations_created,
            "adjustments_made": adjustments_made, "thresholds_set": thresholds_set
        }
