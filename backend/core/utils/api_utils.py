import httpx
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class APIUtils:
    def __init__(self):
        self._initialized = False
        self._rate_limit_cache = {}
        self._api_clients = {}
        
    async def initialize(self):
        """Initialize API utilities"""
        try:
            self._initialized = True
            logger.info("API utilities initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API utilities: {e}")
            raise
    
    async def make_api_request(
        self, 
        url: str, 
        method: str = "GET",
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        timeout: float = 30.0,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make a generic API request with retry logic"""
        try:
            if not self._initialized:
                return {"success": False, "error": "API utilities not initialized"}
            
            # Prepare request data
            request_headers = headers or {}
            request_params = params or {}
            request_data = data or {}
            request_json = json_data or {}
            
            # Add default headers if not provided
            if "User-Agent" not in request_headers:
                request_headers["User-Agent"] = f"Agent47/{settings.version}"
            
            if "Accept" not in request_headers:
                request_headers["Accept"] = "application/json"
            
            # Make request with retry logic
            for attempt in range(retries):
                try:
                    async with httpx.AsyncClient() as client:
                        if method.upper() == "GET":
                            response = await client.get(
                                url, 
                                params=request_params, 
                                headers=request_headers, 
                                timeout=timeout
                            )
                        elif method.upper() == "POST":
                            if request_json:
                                response = await client.post(
                                    url, 
                                    json=request_json, 
                                    params=request_params, 
                                    headers=request_headers, 
                                    timeout=timeout
                                )
                            else:
                                response = await client.post(
                                    url, 
                                    data=request_data, 
                                    params=request_params, 
                                    headers=request_headers, 
                                    timeout=timeout
                                )
                        elif method.upper() == "PUT":
                            if request_json:
                                response = await client.put(
                                    url, 
                                    json=request_json, 
                                    params=request_params, 
                                    headers=request_headers, 
                                    timeout=timeout
                                )
                            else:
                                response = await client.put(
                                    url, 
                                    data=request_data, 
                                    params=request_params, 
                                    headers=request_headers, 
                                    timeout=timeout
                                )
                        elif method.upper() == "DELETE":
                            response = await client.delete(
                                url, 
                                params=request_params, 
                                headers=request_headers, 
                                timeout=timeout
                            )
                        else:
                            return {"success": False, "error": f"Unsupported HTTP method: {method}"}
                        
                        # Process response
                        return await self._process_api_response(response)
                        
                except httpx.TimeoutException:
                    if attempt == retries - 1:
                        return {"success": False, "error": "Request timeout after all retries"}
                    logger.warning(f"API request timeout, attempt {attempt + 1}/{retries}")
                    continue
                    
                except httpx.RequestError as e:
                    if attempt == retries - 1:
                        return {"success": False, "error": f"Request error: {str(e)}"}
                    logger.warning(f"API request error, attempt {attempt + 1}/{retries}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_api_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process API response and extract relevant information"""
        try:
            response_data = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": str(response.url),
                "elapsed": response.elapsed.total_seconds() if response.elapsed else 0
            }
            
            # Try to parse response content
            if response.content:
                try:
                    if "application/json" in response.headers.get("content-type", ""):
                        response_data["data"] = response.json()
                    else:
                        response_data["data"] = response.text
                except Exception as e:
                    response_data["data"] = response.text
                    response_data["parse_error"] = str(e)
            
            # Add error information for failed requests
            if not response_data["success"]:
                response_data["error"] = f"HTTP {response.status_code}: {response.reason_phrase}"
                if response.text:
                    response_data["error_details"] = response.text
            
            return response_data
            
        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def google_search(
        self, 
        query: str, 
        api_key: str, 
        cx: str, 
        num_results: int = 10
    ) -> Dict[str, Any]:
        """Perform Google Custom Search"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(num_results, 10)  # Google CSE limit is 10
            }
            
            result = await self.make_api_request(url, params=params)
            
            if result["success"] and "data" in result:
                # Extract and format search results
                search_data = result["data"]
                formatted_results = []
                
                if "items" in search_data:
                    for item in search_data["items"]:
                        formatted_results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "display_link": item.get("displayLink", ""),
                            "image": item.get("pagemap", {}).get("cse_image", [{}])[0].get("src", "")
                        })
                
                return {
                    "success": True,
                    "results": formatted_results,
                    "total_results": search_data.get("searchInformation", {}).get("totalResults", 0),
                    "search_time": search_data.get("searchInformation", {}).get("searchTime", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def wikipedia_search(
        self, 
        query: str, 
        language: str = "en",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search Wikipedia articles"""
        try:
            # First, search for articles
            search_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{query}"
            
            result = await self.make_api_request(search_url)
            
            if result["success"] and "data" in result:
                wiki_data = result["data"]
                
                return {
                    "success": True,
                    "title": wiki_data.get("title", ""),
                    "extract": wiki_data.get("extract", ""),
                    "content_url": wiki_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "thumbnail": wiki_data.get("thumbnail", {}).get("source", ""),
                    "coordinates": wiki_data.get("coordinates", {}),
                    "language": language
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def weather_api(
        self, 
        city: str, 
        api_key: str,
        units: str = "metric"
    ) -> Dict[str, Any]:
        """Get weather information using OpenWeatherMap API"""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "units": units
            }
            
            result = await self.make_api_request(url, params=params)
            
            if result["success"] and "data" in result:
                weather_data = result["data"]
                
                return {
                    "success": True,
                    "city": weather_data.get("name", ""),
                    "country": weather_data.get("sys", {}).get("country", ""),
                    "temperature": weather_data.get("main", {}).get("temp", 0),
                    "feels_like": weather_data.get("main", {}).get("feels_like", 0),
                    "humidity": weather_data.get("main", {}).get("humidity", 0),
                    "pressure": weather_data.get("main", {}).get("pressure", 0),
                    "description": weather_data.get("weather", [{}])[0].get("description", ""),
                    "icon": weather_data.get("weather", [{}])[0].get("icon", ""),
                    "wind_speed": weather_data.get("wind", {}).get("speed", 0),
                    "wind_direction": weather_data.get("wind", {}).get("deg", 0)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Weather API call failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def currency_converter(
        self, 
        from_currency: str, 
        to_currency: str, 
        amount: float,
        api_key: str
    ) -> Dict[str, Any]:
        """Convert currency using Exchange Rate API"""
        try:
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency.upper()}/{to_currency.upper()}"
            
            result = await self.make_api_request(url)
            
            if result["success"] and "data" in result:
                exchange_data = result["data"]
                
                converted_amount = amount * exchange_data.get("conversion_rate", 0)
                
                return {
                    "success": True,
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper(),
                    "original_amount": amount,
                    "converted_amount": round(converted_amount, 4),
                    "exchange_rate": exchange_data.get("conversion_rate", 0),
                    "last_updated": exchange_data.get("time_last_update_utc", "")
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def news_api(
        self, 
        query: str, 
        api_key: str,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get news articles using NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": api_key,
                "language": language,
                "sortBy": sort_by,
                "pageSize": min(page_size, 100)  # NewsAPI limit is 100
            }
            
            result = await self.make_api_request(url, params=params)
            
            if result["success"] and "data" in result:
                news_data = result["data"]
                formatted_articles = []
                
                if "articles" in news_data:
                    for article in news_data["articles"]:
                        formatted_articles.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "url_to_image": article.get("urlToImage", ""),
                            "published_at": article.get("publishedAt", ""),
                            "source": article.get("source", {}).get("name", ""),
                            "author": article.get("author", "")
                        })
                
                return {
                    "success": True,
                    "articles": formatted_articles,
                    "total_results": news_data.get("totalResults", 0),
                    "status": news_data.get("status", "")
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"News API call failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def rate_limit_check(self, api_name: str, user_id: str) -> Dict[str, Any]:
        """Check if API rate limit has been exceeded"""
        try:
            current_time = datetime.utcnow()
            cache_key = f"{api_name}:{user_id}"
            
            if cache_key not in self._rate_limit_cache:
                self._rate_limit_cache[cache_key] = {
                    "requests": [],
                    "limit": 100,  # Default limit
                    "window": 3600  # 1 hour window
                }
            
            cache_entry = self._rate_limit_cache[cache_key]
            
            # Remove old requests outside the window
            window_start = current_time - timedelta(seconds=cache_entry["window"])
            cache_entry["requests"] = [
                req_time for req_time in cache_entry["requests"] 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(cache_entry["requests"]) >= cache_entry["limit"]:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": window_start + timedelta(seconds=cache_entry["window"])
                }
            
            # Add current request
            cache_entry["requests"].append(current_time)
            
            return {
                "allowed": True,
                "remaining": cache_entry["limit"] - len(cache_entry["requests"]),
                "reset_time": window_start + timedelta(seconds=cache_entry["window"])
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {"allowed": True, "remaining": 999, "reset_time": None}
    
    async def validate_api_response(self, response_data: Dict[str, Any], expected_fields: List[str]) -> Dict[str, Any]:
        """Validate API response structure and required fields"""
        try:
            if not response_data.get("success", False):
                return {"valid": False, "error": "API request was not successful"}
            
            if "data" not in response_data:
                return {"valid": False, "error": "No data field in response"}
            
            data = response_data["data"]
            missing_fields = []
            
            for field in expected_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "missing_fields": missing_fields
                }
            
            return {"valid": True, "message": "Response validation passed"}
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return {"valid": False, "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check API utilities health"""
        try:
            if not self._initialized:
                return False
            
            # Test with a simple request to a reliable service
            test_result = await self.make_api_request(
                "https://httpbin.org/get",
                timeout=5.0
            )
            
            return test_result["success"]
            
        except Exception as e:
            logger.error(f"API utilities health check failed: {e}")
            return False

api_utils = APIUtils()

async def get_api_utils() -> APIUtils:
    return api_utils

async def init_api_utils():
    await api_utils.initialize()
