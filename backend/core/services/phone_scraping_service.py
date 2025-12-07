"""
Phone Number Scraping Service
Scrapes phone numbers from web pages and Google Maps
"""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from ..config import settings
from ..utils.validation import ValidationUtils

logger = logging.getLogger(__name__)

# Access settings correctly
phone_scraping_enabled = settings.phone_scraping.phone_scraping_enabled
google_maps_api_key = settings.google_maps.google_maps_api_key

class PhoneScrapingService:
    """Service for scraping phone numbers from various sources"""
    
    def __init__(self):
        self.validation = ValidationUtils()
        self._initialized = False
    
    async def initialize(self):
        """Initialize phone scraping service"""
        if not phone_scraping_enabled:
            logger.warning("Phone scraping is disabled in settings")
            return
        
        self._initialized = True
        logger.info("Phone scraping service initialized")
    
    async def scrape_from_url(
        self,
        url: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scrape phone numbers from a URL
        
        Args:
            url: URL to scrape
            user_id: User ID for tracking
            
        Returns:
            Dict with success, phone_numbers list, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract phone numbers
                phone_numbers = self._extract_phone_numbers(response.text)
                
                # Validate phone numbers
                validated_numbers = []
                for phone in phone_numbers:
                    if self.validation.validate_phone_number(phone):
                        validated_numbers.append({
                            "phone": phone,
                            "source": url,
                            "validated": True
                        })
                
                return {
                    "success": True,
                    "phone_numbers": validated_numbers,
                    "total_found": len(phone_numbers),
                    "valid_count": len(validated_numbers),
                    "source_url": url,
                    "metadata": {
                        "scraped_at": datetime.utcnow().isoformat(),
                        "user_id": user_id
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to scrape phone numbers from {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_numbers": []
            }
    
    async def scrape_from_google_maps(
        self,
        place_id: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape phone number from Google Maps place
        
        Args:
            place_id: Google Maps place ID
            api_key: Google Maps API key (uses settings if not provided)
            
        Returns:
            Dict with success, phone_number, and business details
        """
        if not self._initialized:
            await self.initialize()
        
        api_key = api_key or google_maps_api_key
        if not api_key:
            return {
                "success": False,
                "error": "Google Maps API key not configured"
            }
        
        try:
            # Use Google Places API to get place details
            url = f"https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_phone_number,international_phone_number,website",
                "key": api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    return {
                        "success": False,
                        "error": f"Google Maps API error: {data.get('status')}"
                    }
                
                result = data.get("result", {})
                phone_number = result.get("formatted_phone_number") or result.get("international_phone_number")
                
                if phone_number:
                    # Validate phone number
                    if self.validation.validate_phone_number(phone_number):
                        return {
                            "success": True,
                            "phone_number": phone_number,
                            "business_name": result.get("name"),
                            "website": result.get("website"),
                            "place_id": place_id,
                            "metadata": {
                                "scraped_at": datetime.utcnow().isoformat(),
                                "source": "google_maps"
                            }
                        }
                
                return {
                    "success": False,
                    "error": "No phone number found for this place",
                    "business_name": result.get("name")
                }
                
        except Exception as e:
            logger.error(f"Failed to scrape phone from Google Maps: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text using regex patterns"""
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # General pattern
            r'\+?\d{10,15}',  # Simple digit pattern
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',  # US format (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # US format 123-456-7890
        ]
        
        phone_numbers = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phone_numbers.extend(matches)
        
        # Clean and deduplicate
        cleaned = []
        seen = set()
        for phone in phone_numbers:
            # Remove common separators
            cleaned_phone = re.sub(r'[-.\s()]', '', phone)
            if cleaned_phone not in seen and len(cleaned_phone) >= 10:
                cleaned.append(phone)
                seen.add(cleaned_phone)
        
        return cleaned

# Singleton instance
_phone_scraping_service: Optional[PhoneScrapingService] = None

async def get_phone_scraping_service() -> PhoneScrapingService:
    """Get or create phone scraping service instance"""
    global _phone_scraping_service
    if not _phone_scraping_service:
        _phone_scraping_service = PhoneScrapingService()
        await _phone_scraping_service.initialize()
    return _phone_scraping_service

