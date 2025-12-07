"""
Geo-location Service for Business Targeting
Helps users target businesses and audiences by location for marketing and outreach
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, and_, func

from ..config import settings
from ..database import get_database as get_db_manager
from ..database.models import User
from .google_maps_service import get_google_maps_service

logger = logging.getLogger(__name__)

class GeolocationService:
    """Service for business geo-location targeting and marketing"""
    
    def __init__(self):
        self.enabled = settings.geolocation.geolocation_enabled
        self._initialized = False
    
    async def initialize(self):
        """Initialize geo-location service"""
        if not self.enabled:
            logger.warning("Geo-location is disabled in settings")
            return
        
        self._initialized = True
        logger.info("Geo-location service initialized")
    
    async def target_businesses_by_location(
        self,
        user_id: int,
        location: str,
        business_type: Optional[str] = None,
        radius_meters: int = 5000,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Find businesses in a location for targeting
        
        Args:
            user_id: User ID making the request
            location: Location string or coordinates
            business_type: Type of business to target
            radius_meters: Search radius in meters
            filters: Additional filters (rating, price_level, etc.)
            
        Returns:
            Dict with targeted businesses and targeting data
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.enabled:
            return {
                "success": False,
                "error": "Geo-location is disabled"
            }
        
        try:
            # Use Google Maps to find businesses
            maps_service = await get_google_maps_service()
            
            # Parse location (could be address, city, or lat,lng)
            if "," in location and location.replace(",", "").replace(".", "").replace("-", "").replace(" ", "").isdigit():
                # Assume it's coordinates
                parts = location.split(",")
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                result = await maps_service.find_nearby_businesses(
                    latitude=lat,
                    longitude=lng,
                    radius=radius_meters,
                    business_type=business_type,
                    user_id=user_id
                )
            else:
                # Assume it's a location string
                query = business_type or "businesses"
                if business_type:
                    query = f"{business_type} in {location}"
                else:
                    query = f"businesses in {location}"
                
                result = await maps_service.search_businesses(
                    query=query,
                    location=location,
                    radius=radius_meters,
                    user_id=user_id
                )
            
            if not result.get("success"):
                return result
            
            businesses = result.get("businesses", [])
            
            # Apply additional filters if provided
            if filters:
                if "min_rating" in filters:
                    businesses = [b for b in businesses if b.get("rating", 0) >= filters["min_rating"]]
                if "max_rating" in filters:
                    businesses = [b for b in businesses if b.get("rating", 0) <= filters["max_rating"]]
                if "has_phone" in filters and filters["has_phone"]:
                    # Filter businesses that have phone numbers
                    businesses_with_phone = []
                    for business in businesses:
                        details_result = await maps_service.get_business_details(
                            place_id=business.get("place_id"),
                            user_id=user_id
                        )
                        if details_result.get("success"):
                            business_data = details_result.get("details", {})
                            if business_data.get("phone_number"):
                                business["phone_number"] = business_data["phone_number"]
                                businesses_with_phone.append(business)
                    businesses = businesses_with_phone
            
            # Calculate targeting metrics
            total_businesses = len(businesses)
            avg_rating = sum([b.get("rating", 0) for b in businesses if b.get("rating")]) / len([b for b in businesses if b.get("rating")]) if businesses else 0
            
            return {
                "success": True,
                "targeted_businesses": businesses,
                "targeting_metrics": {
                    "total_businesses": total_businesses,
                    "average_rating": round(avg_rating, 2),
                    "location": location,
                    "radius_meters": radius_meters,
                    "business_type": business_type
                },
                "metadata": {
                    "targeted_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "filters_applied": filters or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to target businesses by location: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_geo_targeted_campaign(
        self,
        user_id: int,
        campaign_name: str,
        target_locations: List[str],
        campaign_type: str = "outreach",
        agent_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a geo-targeted campaign for business outreach
        
        Args:
            user_id: User ID creating the campaign
            campaign_name: Name of the campaign
            target_locations: List of locations to target
            campaign_type: Type of campaign (outreach, marketing, etc.)
            agent_key: Agent to use for the campaign
            
        Returns:
            Dict with campaign details and targeted businesses
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            all_targeted_businesses = []
            location_results = []
            
            # Target businesses in each location
            for location in target_locations:
                result = await self.target_businesses_by_location(
                    user_id=user_id,
                    location=location,
                    filters={"has_phone": True}  # Only businesses with phone numbers
                )
                
                if result.get("success"):
                    businesses = result.get("targeted_businesses", [])
                    all_targeted_businesses.extend(businesses)
                    location_results.append({
                        "location": location,
                        "businesses_found": len(businesses),
                        "success": True
                    })
                else:
                    location_results.append({
                        "location": location,
                        "businesses_found": 0,
                        "success": False,
                        "error": result.get("error")
                    })
            
            # Store campaign in database
            db = await get_db_manager()
            async with db.get_session() as session:
                from sqlalchemy import text
                await session.execute(
                    text("""
                        INSERT INTO geo_targeted_campaigns (
                            user_id, campaign_name, target_locations, campaign_type,
                            agent_key, total_businesses, status, created_at
                        ) VALUES (
                            :user_id, :campaign_name, :target_locations, :campaign_type,
                            :agent_key, :total_businesses, 'active', NOW()
                        )
                    """),
                    {
                        "user_id": user_id,
                        "campaign_name": campaign_name,
                        "target_locations": str(target_locations),
                        "campaign_type": campaign_type,
                        "agent_key": agent_key,
                        "total_businesses": len(all_targeted_businesses)
                    }
                )
                await session.commit()
            
            return {
                "success": True,
                "campaign": {
                    "name": campaign_name,
                    "type": campaign_type,
                    "agent_key": agent_key,
                    "target_locations": target_locations,
                    "total_businesses": len(all_targeted_businesses),
                    "status": "active"
                },
                "targeted_businesses": all_targeted_businesses,
                "location_results": location_results,
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create geo-targeted campaign: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def amplify_reach_by_location(
        self,
        user_id: int,
        base_location: str,
        expansion_radius_km: int = 10,
        business_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Amplify reach by expanding to nearby locations
        
        Args:
            user_id: User ID
            base_location: Starting location
            expansion_radius_km: How far to expand (in kilometers)
            business_type: Type of business to target
            
        Returns:
            Dict with expanded targeting data
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get base location businesses
            base_result = await self.target_businesses_by_location(
                user_id=user_id,
                location=base_location,
                business_type=business_type,
                radius_meters=expansion_radius_km * 1000
            )
            
            if not base_result.get("success"):
                return base_result
            
            base_businesses = base_result.get("targeted_businesses", [])
            
            # Group businesses by area/neighborhood for better targeting
            businesses_by_area = {}
            for business in base_businesses:
                address = business.get("formatted_address", "")
                # Extract area from address (simplified)
                area = address.split(",")[-2].strip() if len(address.split(",")) > 2 else "Unknown"
                if area not in businesses_by_area:
                    businesses_by_area[area] = []
                businesses_by_area[area].append(business)
            
            return {
                "success": True,
                "base_location": base_location,
                "expansion_radius_km": expansion_radius_km,
                "total_businesses": len(base_businesses),
                "businesses_by_area": {
                    area: {
                        "count": len(businesses),
                        "businesses": businesses[:10]  # Limit for response size
                    }
                    for area, businesses in businesses_by_area.items()
                },
                "targeting_strategy": {
                    "primary_location": base_location,
                    "expansion_radius": f"{expansion_radius_km}km",
                    "total_areas": len(businesses_by_area),
                    "recommended_approach": "Target each area separately for better engagement"
                },
                "metadata": {
                    "amplified_at": datetime.utcnow().isoformat(),
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to amplify reach: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_location_analytics(
        self,
        user_id: int,
        location: str,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific location
        
        Args:
            user_id: User ID
            location: Location to analyze
            timeframe_days: Timeframe for analytics
            
        Returns:
            Dict with location analytics
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get businesses in location
            businesses_result = await self.target_businesses_by_location(
                user_id=user_id,
                location=location
            )
            
            if not businesses_result.get("success"):
                return businesses_result
            
            businesses = businesses_result.get("targeted_businesses", [])
            
            # Calculate analytics
            total_businesses = len(businesses)
            businesses_with_ratings = [b for b in businesses if b.get("rating")]
            avg_rating = sum([b.get("rating") for b in businesses_with_ratings]) / len(businesses_with_ratings) if businesses_with_ratings else 0
            
            # Group by business type
            business_types = {}
            for business in businesses:
                types = business.get("types", [])
                for btype in types:
                    if btype not in ["establishment", "point_of_interest"]:
                        if btype not in business_types:
                            business_types[btype] = 0
                        business_types[btype] += 1
            
            return {
                "success": True,
                "location": location,
                "analytics": {
                    "total_businesses": total_businesses,
                    "average_rating": round(avg_rating, 2),
                    "businesses_with_ratings": len(businesses_with_ratings),
                    "top_business_types": dict(sorted(business_types.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "targeting_potential": {
                        "high_value": len([b for b in businesses if b.get("rating", 0) >= 4.0]),
                        "medium_value": len([b for b in businesses if 3.0 <= b.get("rating", 0) < 4.0]),
                        "low_value": len([b for b in businesses if b.get("rating", 0) < 3.0])
                    }
                },
                "metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "timeframe_days": timeframe_days
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get location analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
_geolocation_service: Optional[GeolocationService] = None

async def get_geolocation_service() -> GeolocationService:
    """Get or create geo-location service instance"""
    global _geolocation_service
    if not _geolocation_service:
        _geolocation_service = GeolocationService()
        await _geolocation_service.initialize()
    return _geolocation_service
