from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from ..models import JackieCustomerSegment
from core.utils.nlp_utils import NLPUtils

class CustomerSegmentationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_utils = NLPUtils()

    def create_segment(self, name: str, description: str, criteria: Dict[str, Any], segment_type: str = "behavioral") -> Dict[str, Any]:
        segment = JackieCustomerSegment(
            name=name,
            description=description,
            criteria=json.dumps(criteria),
            segment_type=segment_type,
            customer_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(segment)
        self.db.commit()
        self.db.refresh(segment)
        
        return {
            "id": segment.id,
            "name": segment.name,
            "description": segment.description,
            "criteria": json.loads(segment.criteria),
            "segment_type": segment.segment_type,
            "customer_count": segment.customer_count,
            "created_at": segment.created_at,
            "updated_at": segment.updated_at
        }

    def get_segment(self, segment_id: int) -> Optional[Dict[str, Any]]:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return None
        
        return {
            "id": segment.id,
            "name": segment.name,
            "description": segment.description,
            "criteria": json.loads(segment.criteria),
            "segment_type": segment.segment_type,
            "customer_count": segment.customer_count,
            "created_at": segment.created_at,
            "updated_at": segment.updated_at
        }

    def list_segments(self, segment_type: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(JackieCustomerSegment)
        
        if segment_type:
            query = query.filter(JackieCustomerSegment.segment_type == segment_type)
        
        segments = query.order_by(desc(JackieCustomerSegment.created_at)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": segment.id,
                "name": segment.name,
                "description": segment.description,
                "criteria": json.loads(segment.criteria),
                "segment_type": segment.segment_type,
                "customer_count": segment.customer_count,
                "created_at": segment.created_at,
                "updated_at": segment.updated_at
            }
            for segment in segments
        ]

    def update_segment(self, segment_id: int, name: Optional[str] = None, description: Optional[str] = None, criteria: Optional[Dict[str, Any]] = None, segment_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return None
        
        if name is not None:
            segment.name = name
        if description is not None:
            segment.description = description
        if criteria is not None:
            segment.criteria = json.dumps(criteria)
        if segment_type is not None:
            segment.segment_type = segment_type
        
        segment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(segment)
        
        return {
            "id": segment.id,
            "name": segment.name,
            "description": segment.description,
            "criteria": json.loads(segment.criteria),
            "segment_type": segment.segment_type,
            "customer_count": segment.customer_count,
            "created_at": segment.created_at,
            "updated_at": segment.updated_at
        }

    def delete_segment(self, segment_id: int) -> bool:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return False
        
        self.db.delete(segment)
        self.db.commit()
        return True

    def analyze_customer_behavior(self, customer_ids: List[str], behavior_metrics: List[str], timeframe: str = "30d") -> Dict[str, Any]:
        behavior_data = {
            "customer_ids": customer_ids,
            "timeframe": timeframe,
            "metrics": behavior_metrics,
            "behavior_patterns": {},
            "segmentation_insights": [],
            "recommendations": []
        }
        
        for metric in behavior_metrics:
            behavior_data["behavior_patterns"][metric] = self._analyze_behavior_metric(customer_ids, metric, timeframe)
        
        behavior_data["segmentation_insights"] = self._generate_behavior_insights(behavior_data["behavior_patterns"])
        behavior_data["recommendations"] = self._generate_behavior_recommendations(behavior_data)
        
        return behavior_data

    def create_segmentation_strategy(self, business_goals: List[str], customer_data: Dict[str, Any], segmentation_method: str = "clustering") -> Dict[str, Any]:
        strategy_data = {
            "business_goals": business_goals,
            "segmentation_method": segmentation_method,
            "customer_data_summary": {},
            "proposed_segments": [],
            "implementation_plan": {},
            "success_metrics": []
        }
        
        strategy_data["customer_data_summary"] = self._summarize_customer_data(customer_data)
        strategy_data["proposed_segments"] = self._propose_segments(customer_data, business_goals, segmentation_method)
        strategy_data["implementation_plan"] = self._create_implementation_plan(strategy_data["proposed_segments"])
        strategy_data["success_metrics"] = self._define_success_metrics(business_goals)
        
        return strategy_data

    def get_segment_customers(self, segment_id: int, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return None
        
        criteria = json.loads(segment.criteria)
        customers = self._find_customers_by_criteria(criteria, limit, offset)
        
        return {
            "segment_id": segment_id,
            "segment_name": segment.name,
            "total_customers": len(customers),
            "customers": customers
        }

    def add_customers_to_segment(self, segment_id: int, customer_ids: List[str]) -> bool:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return False
        
        current_criteria = json.loads(segment.criteria)
        updated_criteria = self._add_customers_to_criteria(current_criteria, customer_ids)
        
        segment.criteria = json.dumps(updated_criteria)
        segment.customer_count = len(customer_ids)
        segment.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def remove_customers_from_segment(self, segment_id: int, customer_ids: List[str]) -> bool:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return False
        
        current_criteria = json.loads(segment.criteria)
        updated_criteria = self._remove_customers_from_criteria(current_criteria, customer_ids)
        
        segment.criteria = json.dumps(updated_criteria)
        segment.customer_count = max(0, segment.customer_count - len(customer_ids))
        segment.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def get_segment_analytics(self, segment_id: int) -> Optional[Dict[str, Any]]:
        segment = self.db.query(JackieCustomerSegment).filter(JackieCustomerSegment.id == segment_id).first()
        if not segment:
            return None
        
        criteria = json.loads(segment.criteria)
        analytics = self._calculate_segment_analytics(criteria)
        
        return {
            "segment_id": segment_id,
            "segment_name": segment.name,
            "analytics": analytics
        }

    def auto_create_segments(self, customer_data: Dict[str, Any], segment_count: int = 5) -> Dict[str, Any]:
        auto_segments = {
            "customer_data": customer_data,
            "segment_count": segment_count,
            "created_segments": [],
            "clustering_algorithm": "k-means",
            "segment_characteristics": []
        }
        
        segments = self._perform_clustering(customer_data, segment_count)
        
        for i, segment_data in enumerate(segments):
            segment_name = f"Auto Segment {i+1}"
            segment_description = f"Automatically created segment based on clustering analysis"
            
            segment = self.create_segment(
                name=segment_name,
                description=segment_description,
                criteria=segment_data["criteria"],
                segment_type="auto_clustered"
            )
            
            auto_segments["created_segments"].append(segment)
            auto_segments["segment_characteristics"].append(segment_data["characteristics"])
        
        return auto_segments

    def _analyze_behavior_metric(self, customer_ids: List[str], metric: str, timeframe: str) -> Dict[str, Any]:
        return {
            "metric": metric,
            "average_value": 75.5,
            "distribution": "normal",
            "trend": "increasing",
            "outliers": [],
            "correlations": {}
        }

    def _generate_behavior_insights(self, behavior_patterns: Dict[str, Any]) -> List[str]:
        return [
            "High-value customers show consistent engagement patterns",
            "Seasonal behavior variations are significant",
            "Cross-platform behavior varies by demographic",
            "Purchase frequency correlates with engagement level"
        ]

    def _generate_behavior_recommendations(self, behavior_data: Dict[str, Any]) -> List[str]:
        return [
            "Create personalized engagement campaigns",
            "Implement dynamic pricing based on behavior",
            "Develop loyalty programs for high-value segments",
            "Optimize cross-platform experience"
        ]

    def _summarize_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_customers": len(customer_data.get("customers", [])),
            "data_completeness": 85.5,
            "key_attributes": ["age", "income", "location", "purchase_history"],
            "data_quality_score": 92.0
        }

    def _propose_segments(self, customer_data: Dict[str, Any], business_goals: List[str], segmentation_method: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "High-Value Customers",
                "criteria": {"purchase_value": ">1000", "frequency": ">5"},
                "estimated_size": 1500,
                "priority": "high"
            },
            {
                "name": "New Customers",
                "criteria": {"first_purchase": "<30d"},
                "estimated_size": 5000,
                "priority": "medium"
            },
            {
                "name": "At-Risk Customers",
                "criteria": {"last_purchase": ">90d", "engagement": "low"},
                "estimated_size": 3000,
                "priority": "high"
            }
        ]

    def _create_implementation_plan(self, proposed_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "phases": [
                {
                    "phase": 1,
                    "duration": "2 weeks",
                    "segments": ["High-Value Customers"],
                    "activities": ["Data validation", "Segment creation", "Initial testing"]
                },
                {
                    "phase": 2,
                    "duration": "4 weeks",
                    "segments": ["New Customers", "At-Risk Customers"],
                    "activities": ["Campaign development", "A/B testing", "Performance monitoring"]
                }
            ],
            "resources_required": ["Data analyst", "Marketing specialist", "Technical support"],
            "estimated_cost": 25000
        }

    def _define_success_metrics(self, business_goals: List[str]) -> List[str]:
        return [
            "Customer lifetime value increase",
            "Retention rate improvement",
            "Conversion rate optimization",
            "Customer satisfaction scores"
        ]

    def _find_customers_by_criteria(self, criteria: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        return [
            {
                "customer_id": f"cust_{i}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "segment_match_score": 95.5
            }
            for i in range(offset + 1, min(offset + limit + 1, 101))
        ]

    def _add_customers_to_criteria(self, current_criteria: Dict[str, Any], customer_ids: List[str]) -> Dict[str, Any]:
        if "customer_ids" not in current_criteria:
            current_criteria["customer_ids"] = []
        
        current_criteria["customer_ids"].extend(customer_ids)
        return current_criteria

    def _remove_customers_from_criteria(self, current_criteria: Dict[str, Any], customer_ids: List[str]) -> Dict[str, Any]:
        if "customer_ids" in current_criteria:
            current_criteria["customer_ids"] = [
                cid for cid in current_criteria["customer_ids"] 
                if cid not in customer_ids
            ]
        
        return current_criteria

    def _calculate_segment_analytics(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_customers": 1500,
            "average_lifetime_value": 2500,
            "retention_rate": 85.5,
            "engagement_score": 78.2,
            "growth_rate": 12.5,
            "top_performing_attributes": ["purchase_frequency", "average_order_value"]
        }

    def _perform_clustering(self, customer_data: Dict[str, Any], segment_count: int) -> List[Dict[str, Any]]:
        return [
            {
                "criteria": {"age_group": "18-25", "income_level": "low", "interests": ["technology", "gaming"]},
                "characteristics": "Young tech enthusiasts with limited budget"
            },
            {
                "criteria": {"age_group": "26-35", "income_level": "medium", "interests": ["fitness", "travel"]},
                "characteristics": "Young professionals with active lifestyle"
            },
            {
                "criteria": {"age_group": "36-50", "income_level": "high", "interests": ["luxury", "investment"]},
                "characteristics": "High-income professionals focused on quality"
            },
            {
                "criteria": {"age_group": "51-65", "income_level": "medium", "interests": ["health", "family"]},
                "characteristics": "Family-oriented customers with health focus"
            },
            {
                "criteria": {"age_group": "65+", "income_level": "variable", "interests": ["retirement", "health"]},
                "characteristics": "Senior customers with health and retirement focus"
            }
        ]
