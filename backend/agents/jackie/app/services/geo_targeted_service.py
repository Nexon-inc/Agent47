import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from core.services.google_maps_service import get_google_maps_service
from ..models import JackieGeoTargetedAd, JackieLocalMarket, GeographicData, RegionalStrategy

class GeoTargetedService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        self.google_maps_service = None
        
    def create_geo_targeted_ad(self, ad_brief: Dict[str, Any], target_locations: List[str]) -> Dict[str, Any]:
        ad_id = str(uuid.uuid4())
        ad_result = self.nlp_processor.create_geo_targeted_ad(f"Ad Brief: {ad_brief}")
        
        ad = JackieGeoTargetedAd(
            id=ad_id, ad_brief=json.dumps(ad_brief), target_locations=json.dumps(target_locations),
            ad_content=json.dumps(ad_result), created_at=datetime.utcnow()
        )
        self.db.add(ad)
        self.db.commit()
        
        return {"ad_id": ad_id, "ad_content": ad_result}
    
    async def analyze_local_market(self, location: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze local market using Google Maps integration"""
        import asyncio
        
        # Initialize Google Maps service
        if not self.google_maps_service:
            self.google_maps_service = await get_google_maps_service()
        
        market_id = str(uuid.uuid4())
        
        # Use Google Maps to get business data for location
        maps_result = await self.google_maps_service.search_businesses(
            query=location,
            location=location
        )
        
        # Combine with NLP analysis
        market_result = self.nlp_processor.analyze_local_market(f"Location: {location}")
        
        # Enhance with Google Maps data
        if maps_result.get("success"):
            businesses = maps_result.get("businesses", [])
            market_result["google_maps_data"] = {
                "total_businesses": len(businesses),
                "business_types": list(set([b.get("types", [])[0] if b.get("types") else "unknown" for b in businesses[:10]])),
                "average_rating": sum([b.get("rating", 0) for b in businesses if b.get("rating")]) / len([b for b in businesses if b.get("rating")]) if businesses else 0
            }
        
        market = JackieLocalMarket(
            id=market_id, name=location, demographics=market_data,
            created_at=datetime.utcnow()
        )
        self.db.add(market)
        self.db.commit()
        
        return {"market_id": market_id, "market_analysis": market_result}
    
    def get_geo_targeted_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        ads_created = self.db.query(JackieGeoTargetedAd).filter(JackieGeoTargetedAd.created_at >= cutoff_date).count()
        markets_analyzed = self.db.query(JackieLocalMarket).filter(JackieLocalMarket.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "ads_created": ads_created,
            "markets_analyzed": markets_analyzed
        }
