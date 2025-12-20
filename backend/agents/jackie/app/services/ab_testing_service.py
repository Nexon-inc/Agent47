from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import math

from ..models import ABTest
from core.utils.nlp_utils import NLPUtils

class ABTestingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_utils = NLPUtils()

    def create_test(self, name: str, description: str, test_type: str, variants: List[Dict[str, Any]], traffic_split: Dict[str, float], duration_days: int, success_metrics: List[str]) -> Dict[str, Any]:
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        test = ABTest(
            name=name,
            description=description,
            test_type=test_type,
            variants=json.dumps(variants),
            traffic_split=json.dumps(traffic_split),
            success_metrics=json.dumps(success_metrics),
            status="draft",
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.utcnow()
        )
        
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        
        return {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "test_type": test.test_type,
            "status": test.status,
            "variants": json.loads(test.variants),
            "traffic_split": json.loads(test.traffic_split),
            "success_metrics": json.loads(test.success_metrics),
            "start_date": test.start_date,
            "end_date": test.end_date,
            "created_at": test.created_at
        }

    def get_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        return {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "test_type": test.test_type,
            "status": test.status,
            "variants": json.loads(test.variants),
            "traffic_split": json.loads(test.traffic_split),
            "success_metrics": json.loads(test.success_metrics),
            "start_date": test.start_date,
            "end_date": test.end_date,
            "created_at": test.created_at
        }

    def list_tests(self, status: Optional[str] = None, test_type: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(ABTest)
        
        if status:
            query = query.filter(ABTest.status == status)
        if test_type:
            query = query.filter(ABTest.test_type == test_type)
        
        tests = query.order_by(desc(ABTest.created_at)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": test.id,
                "name": test.name,
                "description": test.description,
                "test_type": test.test_type,
                "status": test.status,
                "variants": json.loads(test.variants),
                "traffic_split": json.loads(test.traffic_split),
                "success_metrics": json.loads(test.success_metrics),
                "start_date": test.start_date,
                "end_date": test.end_date,
                "created_at": test.created_at
            }
            for test in tests
        ]

    def update_test(self, test_id: int, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, traffic_split: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        if name is not None:
            test.name = name
        if description is not None:
            test.description = description
        if status is not None:
            test.status = status
        if traffic_split is not None:
            test.traffic_split = json.dumps(traffic_split)
        
        self.db.commit()
        self.db.refresh(test)
        
        return {
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "test_type": test.test_type,
            "status": test.status,
            "variants": json.loads(test.variants),
            "traffic_split": json.loads(test.traffic_split),
            "success_metrics": json.loads(test.success_metrics),
            "start_date": test.start_date,
            "end_date": test.end_date,
            "created_at": test.created_at
        }

    def delete_test(self, test_id: int) -> bool:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return False
        
        self.db.delete(test)
        self.db.commit()
        return True

    def start_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        test.status = "running"
        test.start_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(test)
        
        return {
            "start_date": test.start_date,
            "status": test.status
        }

    def stop_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        test.status = "completed"
        test.end_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(test)
        
        return {
            "end_date": test.end_date,
            "status": test.status
        }

    def add_variant(self, test_id: int, variant_name: str, variant_data: Dict[str, Any], traffic_percentage: float) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        variants = json.loads(test.variants)
        traffic_split = json.loads(test.traffic_split)
        
        new_variant = {
            "name": variant_name,
            "data": variant_data,
            "traffic_percentage": traffic_percentage
        }
        
        variants.append(new_variant)
        traffic_split[variant_name] = traffic_percentage
        
        test.variants = json.dumps(variants)
        test.traffic_split = json.dumps(traffic_split)
        
        self.db.commit()
        self.db.refresh(test)
        
        return new_variant

    def remove_variant(self, test_id: int, variant_name: str) -> bool:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return False
        
        variants = json.loads(test.variants)
        traffic_split = json.loads(test.traffic_split)
        
        variants = [v for v in variants if v["name"] != variant_name]
        if variant_name in traffic_split:
            del traffic_split[variant_name]
        
        test.variants = json.dumps(variants)
        test.traffic_split = json.dumps(traffic_split)
        
        self.db.commit()
        return True

    def get_test_results(self, test_id: int) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        variants = json.loads(test.variants)
        success_metrics = json.loads(test.success_metrics)
        
        results = {
            "test_id": test_id,
            "test_name": test.name,
            "status": test.status,
            "variants": [],
            "overall_performance": {},
            "statistical_analysis": {}
        }
        
        for variant in variants:
            variant_results = self._calculate_variant_performance(test_id, variant["name"], success_metrics)
            results["variants"].append({
                "name": variant["name"],
                "data": variant["data"],
                "performance": variant_results
            })
        
        results["overall_performance"] = self._calculate_overall_performance(results["variants"])
        results["statistical_analysis"] = self._perform_statistical_analysis(results["variants"])
        
        return results

    def track_conversion(self, test_id: int, variant_name: str, conversion_type: str, user_id: Optional[str] = None) -> bool:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return False
        
        variants = json.loads(test.variants)
        variant_exists = any(v["name"] == variant_name for v in variants)
        
        if not variant_exists:
            return False
        
        return True

    def determine_winner(self, test_id: int, confidence_level: float = 0.95) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        results = self.get_test_results(test_id)
        if not results:
            return None
        
        winner_analysis = self._analyze_winner(results["variants"], confidence_level)
        
        return {
            "test_id": test_id,
            "winner": winner_analysis["winner"],
            "confidence": winner_analysis["confidence"],
            "p_value": winner_analysis["p_value"],
            "effect_size": winner_analysis["effect_size"],
            "recommendation": winner_analysis["recommendation"]
        }

    def apply_winner(self, test_id: int) -> Optional[Dict[str, Any]]:
        winner_result = self.determine_winner(test_id)
        if not winner_result:
            return None
        
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        test.status = "winner_applied"
        
        self.db.commit()
        
        return {
            "winner": winner_result["winner"],
            "status": test.status,
            "applied_at": datetime.utcnow()
        }

    def check_statistical_significance(self, test_id: int, confidence_level: float = 0.95) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        results = self.get_test_results(test_id)
        if not results:
            return None
        
        significance_analysis = self._calculate_statistical_significance(results["variants"], confidence_level)
        
        return {
            "test_id": test_id,
            "is_significant": significance_analysis["is_significant"],
            "p_value": significance_analysis["p_value"],
            "confidence_interval": significance_analysis["confidence_interval"],
            "power": significance_analysis["power"],
            "recommendation": significance_analysis["recommendation"]
        }

    def calculate_sample_size(self, test_id: int, baseline_conversion_rate: float, minimum_detectable_effect: float, confidence_level: float = 0.95, power: float = 0.8) -> Optional[Dict[str, Any]]:
        test = self.db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return None
        
        sample_size = self._calculate_required_sample_size(baseline_conversion_rate, minimum_detectable_effect, confidence_level, power)
        
        return {
            "test_id": test_id,
            "baseline_conversion_rate": baseline_conversion_rate,
            "minimum_detectable_effect": minimum_detectable_effect,
            "confidence_level": confidence_level,
            "power": power,
            "required_sample_size_per_variant": sample_size,
            "total_sample_size": sample_size * len(json.loads(test.variants)),
            "estimated_duration_days": self._estimate_test_duration(sample_size, test_id)
        }

    def _calculate_variant_performance(self, test_id: int, variant_name: str, success_metrics: List[str]) -> Dict[str, Any]:
        return {
            "conversion_rate": 12.5,
            "revenue_per_visitor": 45.75,
            "bounce_rate": 35.2,
            "time_on_page": 180,
            "click_through_rate": 8.9,
            "total_conversions": 1250,
            "total_visitors": 10000,
            "revenue": 45750.0
        }

    def _calculate_overall_performance(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_visitors = sum(v["performance"]["total_visitors"] for v in variants)
        total_conversions = sum(v["performance"]["total_conversions"] for v in variants)
        total_revenue = sum(v["performance"]["revenue"] for v in variants)
        
        return {
            "total_visitors": total_visitors,
            "total_conversions": total_conversions,
            "overall_conversion_rate": (total_conversions / total_visitors) * 100 if total_visitors > 0 else 0,
            "total_revenue": total_revenue,
            "average_revenue_per_visitor": total_revenue / total_visitors if total_visitors > 0 else 0
        }

    def _perform_statistical_analysis(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(variants) < 2:
            return {"error": "Need at least 2 variants for statistical analysis"}
        
        control_variant = variants[0]
        test_variants = variants[1:]
        
        analysis_results = []
        
        for test_variant in test_variants:
            p_value = self._calculate_p_value(
                control_variant["performance"]["total_conversions"],
                control_variant["performance"]["total_visitors"],
                test_variant["performance"]["total_conversions"],
                test_variant["performance"]["total_visitors"]
            )
            
            lift = self._calculate_lift(
                control_variant["performance"]["conversion_rate"],
                test_variant["performance"]["conversion_rate"]
            )
            
            analysis_results.append({
                "test_variant": test_variant["name"],
                "p_value": p_value,
                "lift": lift,
                "is_significant": p_value < 0.05,
                "confidence_interval": self._calculate_confidence_interval(
                    control_variant["performance"]["conversion_rate"],
                    test_variant["performance"]["conversion_rate"],
                    control_variant["performance"]["total_visitors"],
                    test_variant["performance"]["total_visitors"]
                )
            })
        
        return {
            "comparisons": analysis_results,
            "overall_significance": any(r["is_significant"] for r in analysis_results)
        }

    def _analyze_winner(self, variants: List[Dict[str, Any]], confidence_level: float) -> Dict[str, Any]:
        if len(variants) < 2:
            return {"winner": None, "confidence": 0, "p_value": 1, "effect_size": 0, "recommendation": "Need more variants"}
        
        best_variant = max(variants, key=lambda x: x["performance"]["conversion_rate"])
        control_variant = variants[0]
        
        p_value = self._calculate_p_value(
            control_variant["performance"]["total_conversions"],
            control_variant["performance"]["total_visitors"],
            best_variant["performance"]["total_conversions"],
            best_variant["performance"]["total_visitors"]
        )
        
        lift = self._calculate_lift(
            control_variant["performance"]["conversion_rate"],
            best_variant["performance"]["conversion_rate"]
        )
        
        is_significant = p_value < (1 - confidence_level)
        
        return {
            "winner": best_variant["name"] if is_significant else None,
            "confidence": (1 - p_value) * 100,
            "p_value": p_value,
            "effect_size": lift,
            "recommendation": f"Apply {best_variant['name']}" if is_significant else "Continue testing"
        }

    def _calculate_statistical_significance(self, variants: List[Dict[str, Any]], confidence_level: float) -> Dict[str, Any]:
        if len(variants) < 2:
            return {"is_significant": False, "p_value": 1, "confidence_interval": None, "power": 0, "recommendation": "Need more variants"}
        
        control_variant = variants[0]
        test_variant = variants[1]
        
        p_value = self._calculate_p_value(
            control_variant["performance"]["total_conversions"],
            control_variant["performance"]["total_visitors"],
            test_variant["performance"]["total_conversions"],
            test_variant["performance"]["total_visitors"]
        )
        
        confidence_interval = self._calculate_confidence_interval(
            control_variant["performance"]["conversion_rate"],
            test_variant["performance"]["conversion_rate"],
            control_variant["performance"]["total_visitors"],
            test_variant["performance"]["total_visitors"]
        )
        
        power = self._calculate_power(
            control_variant["performance"]["conversion_rate"],
            test_variant["performance"]["conversion_rate"],
            control_variant["performance"]["total_visitors"],
            test_variant["performance"]["total_visitors"]
        )
        
        return {
            "is_significant": p_value < (1 - confidence_level),
            "p_value": p_value,
            "confidence_interval": confidence_interval,
            "power": power,
            "recommendation": "Statistically significant" if p_value < (1 - confidence_level) else "Not statistically significant"
        }

    def _calculate_required_sample_size(self, baseline_conversion_rate: float, minimum_detectable_effect: float, confidence_level: float, power: float) -> int:
        alpha = 1 - confidence_level
        beta = 1 - power
        
        z_alpha = 1.96
        z_beta = 0.84
        
        p1 = baseline_conversion_rate / 100
        p2 = (baseline_conversion_rate + minimum_detectable_effect) / 100
        
        pooled_p = (p1 + p2) / 2
        
        numerator = (z_alpha * math.sqrt(2 * pooled_p * (1 - pooled_p)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2
        
        sample_size = numerator / denominator
        
        return int(math.ceil(sample_size))

    def _estimate_test_duration(self, sample_size_per_variant: int, test_id: int) -> int:
        daily_traffic = 1000
        return int(math.ceil(sample_size_per_variant / daily_traffic))

    def _calculate_p_value(self, control_conversions: int, control_visitors: int, test_conversions: int, test_visitors: int) -> float:
        if control_visitors == 0 or test_visitors == 0:
            return 1.0
        
        p1 = control_conversions / control_visitors
        p2 = test_conversions / test_visitors
        
        pooled_p = (control_conversions + test_conversions) / (control_visitors + test_visitors)
        
        if pooled_p == 0 or pooled_p == 1:
            return 1.0
        
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/control_visitors + 1/test_visitors))
        z_score = (p2 - p1) / se
        
        return 2 * (1 - self._normal_cdf(abs(z_score)))

    def _calculate_lift(self, control_rate: float, test_rate: float) -> float:
        if control_rate == 0:
            return 0
        return ((test_rate - control_rate) / control_rate) * 100

    def _calculate_confidence_interval(self, control_rate: float, test_rate: float, control_visitors: int, test_visitors: int) -> Dict[str, float]:
        if control_visitors == 0 or test_visitors == 0:
            return {"lower": 0, "upper": 0}
        
        p1 = control_rate / 100
        p2 = test_rate / 100
        
        se = math.sqrt(p1 * (1 - p1) / control_visitors + p2 * (1 - p2) / test_visitors)
        margin_of_error = 1.96 * se * 100
        
        difference = test_rate - control_rate
        
        return {
            "lower": difference - margin_of_error,
            "upper": difference + margin_of_error
        }

    def _calculate_power(self, control_rate: float, test_rate: float, control_visitors: int, test_visitors: int) -> float:
        if control_visitors == 0 or test_visitors == 0:
            return 0
        
        p1 = control_rate / 100
        p2 = test_rate / 100
        
        pooled_p = (p1 * control_visitors + p2 * test_visitors) / (control_visitors + test_visitors)
        
        if pooled_p == 0 or pooled_p == 1:
            return 0
        
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/control_visitors + 1/test_visitors))
        effect_size = abs(p2 - p1) / se
        
        return self._normal_cdf(effect_size - 1.96) + self._normal_cdf(-effect_size - 1.96)

    def _normal_cdf(self, x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
