import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import CustomerSearch, SearchResult, SocialProfile, CustomerMatch

class CustomerSearchService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def search_customers_by_product(self, product_description: str, search_criteria: Dict[str, Any],
                                  search_platforms: List[str]) -> Dict[str, Any]:
        search_id = str(uuid.uuid4())
        
        prompt = f"""
        Product Description: {product_description}
        Search Criteria: {search_criteria}
        Search Platforms: {search_platforms}
        
        Search for potential customers based on product description and criteria.
        """
        
        search_result = self.nlp_processor.search_customers_by_product(prompt)
        
        search = CustomerSearch(
            id=search_id, product_description=product_description, search_criteria=json.dumps(search_criteria),
            search_platforms=json.dumps(search_platforms), search_results=json.dumps(search_result),
            created_at=datetime.utcnow()
        )
        self.db.add(search)
        self.db.commit()
        
        return {"search_id": search_id, "search_results": search_result}
    
    def analyze_social_profiles(self, profile_data: List[Dict[str, Any]], analysis_focus: List[str]) -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        
        prompt = f"""
        Profile Data: {profile_data}
        Analysis Focus: {analysis_focus}
        
        Analyze social media profiles to identify potential customers.
        """
        
        analysis_result = self.nlp_processor.analyze_social_profiles(prompt)
        
        for profile in profile_data:
            social_profile = SocialProfile(
                id=str(uuid.uuid4()), profile_data=json.dumps(profile),
                analysis_focus=json.dumps(analysis_focus), analysis_results=json.dumps(analysis_result),
                created_at=datetime.utcnow()
            )
            self.db.add(social_profile)
        
        self.db.commit()
        
        return {"analysis_id": analysis_id, "analysis_results": analysis_result}
    
    def find_customer_matches(self, customer_criteria: Dict[str, Any], match_threshold: float = 0.7) -> Dict[str, Any]:
        match_id = str(uuid.uuid4())
        
        prompt = f"""
        Customer Criteria: {customer_criteria}
        Match Threshold: {match_threshold}
        
        Find customer matches based on specified criteria and threshold.
        """
        
        match_result = self.nlp_processor.find_customer_matches(prompt)
        
        match = CustomerMatch(
            id=match_id, customer_criteria=json.dumps(customer_criteria), match_threshold=match_threshold,
            match_results=json.dumps(match_result), created_at=datetime.utcnow()
        )
        self.db.add(match)
        self.db.commit()
        
        return {"match_id": match_id, "match_results": match_result}
    
    def search_by_demographics(self, demographic_data: Dict[str, Any], search_radius: str = "global") -> Dict[str, Any]:
        prompt = f"""
        Demographic Data: {demographic_data}
        Search Radius: {search_radius}
        
        Search for customers based on demographic criteria.
        """
        
        demographic_result = self.nlp_processor.search_by_demographics(prompt)
        
        return {
            "demographic_data": demographic_data, "search_radius": search_radius,
            "demographic_results": demographic_result
        }
    
    def search_by_interests(self, interest_data: List[str], search_platforms: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Interest Data: {interest_data}
        Search Platforms: {search_platforms}
        
        Search for customers based on interest criteria.
        """
        
        interest_result = self.nlp_processor.search_by_interests(prompt)
        
        return {
            "interest_data": interest_data, "search_platforms": search_platforms,
            "interest_results": interest_result
        }
    
    def get_customer_search_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        searches_conducted = self.db.query(CustomerSearch).filter(
            CustomerSearch.created_at >= cutoff_date
        ).count()
        
        profiles_analyzed = self.db.query(SocialProfile).filter(
            SocialProfile.created_at >= cutoff_date
        ).count()
        
        matches_found = self.db.query(CustomerMatch).filter(
            CustomerMatch.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "searches_conducted": searches_conducted,
            "profiles_analyzed": profiles_analyzed, "matches_found": matches_found
        }
