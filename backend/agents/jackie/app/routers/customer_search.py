from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.customer_search_service import CustomerSearchService

router = APIRouter(prefix="/customer-search", tags=["Customer Search"])

@router.post("/search-by-product")
def search_customers_by_product(product_description: str, search_criteria: Dict[str, Any], 
                              search_platforms: List[str], db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.search_customers_by_product(product_description, search_criteria, search_platforms)

@router.post("/analyze-social-profiles")
def analyze_social_profiles(profile_data: List[Dict[str, Any]], analysis_focus: List[str], 
                          db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.analyze_social_profiles(profile_data, analysis_focus)

@router.post("/find-matches")
def find_customer_matches(customer_criteria: Dict[str, Any], match_threshold: float = 0.7, 
                        db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.find_customer_matches(customer_criteria, match_threshold)

@router.post("/search-by-demographics")
def search_by_demographics(demographic_data: Dict[str, Any], search_radius: str = "global", 
                         db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.search_by_demographics(demographic_data, search_radius)

@router.post("/search-by-interests")
def search_by_interests(interest_data: List[str], search_platforms: List[str], 
                       db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.search_by_interests(interest_data, search_platforms)

@router.get("/analytics")
def get_customer_search_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = CustomerSearchService(db)
    return service.get_customer_search_analytics(timeframe)
