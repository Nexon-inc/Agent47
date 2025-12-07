"""
Google Maps Integration Service
Provides business search, place details, and location-based features
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from ..config import settings
from ..database import get_database
from ..database.models import User

logger = logging.getLogger(__name__)

class GoogleMapsService:
    """Service for Google Maps API integration"""
    
    def __init__(self):
        self.api_key = settings.google_maps.google_maps_api_key
        self.enabled = settings.google_maps.google_maps_enabled
        self.rate_limit = settings.google_maps.google_maps_rate_limit
        self._initialized = False
    
    async def initialize(self):
        """Initialize Google Maps service"""
        if not self.enabled:
            logger.warning("Google Maps is disabled in settings")
            return
        
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return
        
        self._initialized = True
        logger.info("Google Maps service initialized")
    
    async def search_businesses(
        self,
        query: str,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for businesses using Google Places API
        
        Args:
            query: Business name or type (e.g., "restaurants", "coffee shops")
            location: Location string or lat,lng coordinates
            radius: Search radius in meters (max 50000)
            user_id: User ID for tracking
            
        Returns:
            Dict with success, businesses list, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.enabled or not self.api_key:
            return {
                "success": False,
                "error": "Google Maps service not available"
            }
        
        try:
            # Use Places API Text Search
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key
            }
            
            if location:
                params["location"] = location
            
            if radius:
                params["radius"] = min(radius, 50000)  # Max 50km
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    return {
                        "success": False,
                        "error": f"Google Maps API error: {data.get('status')}",
                        "status": data.get("status")
                    }
                
                businesses = []
                for place in data.get("results", []):
                    business = {
                        "place_id": place.get("place_id"),
                        "name": place.get("name"),
                        "formatted_address": place.get("formatted_address"),
                        "location": {
                            "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                            "lng": place.get("geometry", {}).get("location", {}).get("lng")
                        },
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                        "types": place.get("types", []),
                        "business_status": place.get("business_status")
                    }
                    businesses.append(business)
                
                return {
                    "success": True,
                    "businesses": businesses,
                    "total": len(businesses),
                    "query": query,
                    "metadata": {
                        "searched_at": datetime.utcnow().isoformat(),
                        "user_id": user_id,
                        "location": location,
                        "radius": radius
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to search businesses: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_business_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a business
        
        Args:
            place_id: Google Maps place ID
            fields: Specific fields to retrieve (default: all)
            
        Returns:
            Dict with business details
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.enabled or not self.api_key:
            return {
                "success": False,
                "error": "Google Maps service not available"
            }
        
        try:
            # Default fields
            if not fields:
                fields = [
                    "name", "formatted_address", "formatted_phone_number",
                    "international_phone_number", "website", "rating",
                    "user_ratings_total", "opening_hours", "photos",
                    "reviews", "geometry", "types", "business_status",
                    "price_level", "vicinity"
                ]
            
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": ",".join(fields),
                "key": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    return {
                        "success": False,
                        "error": f"Google Maps API error: {data.get('status')}",
                        "status": data.get("status")
                    }
                
                result = data.get("result", {})
                
                return {
                    "success": True,
                    "business": {
                        "place_id": place_id,
                        "name": result.get("name"),
                        "formatted_address": result.get("formatted_address"),
                        "formatted_phone_number": result.get("formatted_phone_number"),
                        "international_phone_number": result.get("international_phone_number"),
                        "website": result.get("website"),
                        "rating": result.get("rating"),
                        "user_ratings_total": result.get("user_ratings_total"),
                        "opening_hours": result.get("opening_hours", {}),
                        "photos": result.get("photos", []),
                        "reviews": result.get("reviews", []),
                        "location": {
                            "lat": result.get("geometry", {}).get("location", {}).get("lat"),
                            "lng": result.get("geometry", {}).get("location", {}).get("lng")
                        },
                        "types": result.get("types", []),
                        "business_status": result.get("business_status"),
                        "price_level": result.get("price_level"),
                        "vicinity": result.get("vicinity")
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get business details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def contact_business(
        self,
        place_id: str,
        agent_key: str,
        message: str,
        user_id: int,
        contact_method: str = "phone"
    ) -> Dict[str, Any]:
        """
        Contact a business using agent voice
        
        Args:
            place_id: Google Maps place ID
            agent_key: Agent to use for contact
            message: Message to deliver
            user_id: User making the contact
            contact_method: "phone" or "email"
            
        Returns:
            Dict with success and contact details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get business details
            details_result = await self.get_business_details(
                place_id=place_id,
                fields=["name", "formatted_phone_number", "international_phone_number", "website"]
            )
            
            if not details_result.get("success"):
                return details_result
            
            business = details_result.get("business", {})
            
            if contact_method == "phone":
                phone_number = business.get("formatted_phone_number") or business.get("international_phone_number")
                
                if not phone_number:
                    return {
                        "success": False,
                        "error": "Business phone number not available"
                    }
                
                # Use phone calling service
                from .phone_calling_service import get_phone_calling_service
                calling_service = await get_phone_calling_service()
                
                call_result = await calling_service.make_agent_call(
                    phone_number=phone_number,
                    agent_key=agent_key,
                    message=message,
                    user_id=user_id
                )
                
                return {
                    "success": call_result.get("success"),
                    "contact_method": "phone",
                    "phone_number": phone_number,
                    "business_name": business.get("name"),
                    "call_sid": call_result.get("call_sid"),
                    "error": call_result.get("error")
                }
            
            elif contact_method == "email":
                # Email contact would require email service
                # For now, return business email if available
                website = business.get("website")
                
                return {
                    "success": True,
                    "contact_method": "email",
                    "business_name": business.get("name"),
                    "website": website,
                    "message": "Email contact requires website/email extraction"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown contact method: {contact_method}"
                }
                
        except Exception as e:
            logger.error(f"Failed to contact business: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def find_nearby_businesses(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1000,
        business_type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Find businesses near a location
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in meters (max 50000)
            business_type: Type of business (e.g., "restaurant", "store")
            user_id: User ID for tracking
            
        Returns:
            Dict with nearby businesses
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": min(radius, 50000),
                "key": self.api_key
            }
            
            if business_type:
                params["type"] = business_type
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    return {
                        "success": False,
                        "error": f"Google Maps API error: {data.get('status')}",
                        "status": data.get("status")
                    }
                
                businesses = []
                for place in data.get("results", []):
                    business = {
                        "place_id": place.get("place_id"),
                        "name": place.get("name"),
                        "formatted_address": place.get("vicinity") or place.get("formatted_address"),
                        "location": {
                            "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                            "lng": place.get("geometry", {}).get("location", {}).get("lng")
                        },
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                        "types": place.get("types", []),
                        "business_status": place.get("business_status")
                    }
                    businesses.append(business)
                
                return {
                    "success": True,
                    "businesses": businesses,
                    "total": len(businesses),
                    "center": {
                        "lat": latitude,
                        "lng": longitude
                    },
                    "radius": radius,
                    "metadata": {
                        "searched_at": datetime.utcnow().isoformat(),
                        "user_id": user_id
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to find nearby businesses: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
_google_maps_service: Optional[GoogleMapsService] = None

async def get_google_maps_service() -> GoogleMapsService:
    """Get or create Google Maps service instance"""
    global _google_maps_service
    if not _google_maps_service:
        _google_maps_service = GoogleMapsService()
        await _google_maps_service.initialize()
    return _google_maps_service

