from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.geo_localization_service import GeoLocalizationService

router = APIRouter(prefix="/geo-localization", tags=["Geo-Localization"])

geo_localization_service = GeoLocalizationService()


@router.post("/detect-location")
async def detect_customer_location(
    ip_address: Optional[str] = None,
    timezone: Optional[str] = None,
    language: Optional[str] = None
):
    """Detect customer location and preferred language"""
    try:
        result = await geo_localization_service.detect_customer_location(
            ip_address=ip_address,
            timezone=timezone,
            language=language
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["location"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect location: {str(e)}")


@router.post("/localize")
async def get_localized_response(
    message: str,
    target_language: str,
    formality_level: str = "casual"
):
    """Get localized response in the target language"""
    try:
        result = await geo_localization_service.get_localized_response(
            message=message,
            target_language=target_language,
            formality_level=formality_level
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "original_message": message,
                    "localized_message": result["localized_message"],
                    "target_language": result["target_language"],
                    "language_name": result["language_name"],
                    "rtl": result["rtl"]
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to localize message: {str(e)}")


@router.get("/languages/supported")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        result = await geo_localization_service.get_supported_languages()
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "languages": result["languages"],
                    "total_languages": result["total_languages"]
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported languages: {str(e)}")


@router.get("/regions/{region}/support-info")
async def get_regional_support_info(region: str):
    """Get regional support information"""
    try:
        result = await geo_localization_service.get_regional_support_info(region=region)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["info"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regional support info: {str(e)}")


@router.get("/languages/{language_code}/info")
async def get_language_info(language_code: str):
    """Get detailed information about a specific language"""
    try:
        result = await geo_localization_service.get_supported_languages()
        
        if result["success"]:
            language_info = None
            for lang in result["languages"]:
                if lang["code"] == language_code:
                    language_info = lang
                    break
            
            if language_info:
                return {
                    "success": True,
                    "data": language_info,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=404, detail=f"Language not found: {language_code}")
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language info: {str(e)}")


@router.post("/batch-localize")
async def batch_localize_messages(
    messages: List[str],
    target_languages: List[str],
    formality_level: str = "casual"
):
    """Localize multiple messages to multiple languages"""
    try:
        results = []
        
        for message in messages:
            for language in target_languages:
                result = await geo_localization_service.get_localized_response(
                    message=message,
                    target_language=language,
                    formality_level=formality_level
                )
                
                if result["success"]:
                    results.append({
                        "original_message": message,
                        "target_language": language,
                        "localized_message": result["localized_message"],
                        "success": True
                    })
                else:
                    results.append({
                        "original_message": message,
                        "target_language": language,
                        "error": result["error"],
                        "success": False
                    })
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_messages": len(messages),
                "total_languages": len(target_languages),
                "successful_translations": len([r for r in results if r["success"]])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch localize: {str(e)}")


@router.get("/health")
async def geo_localization_health():
    """Health check for geo-localization service"""
    try:
        await geo_localization_service.initialize()
        
        return {
            "success": True,
            "service": "geo-localization",
            "status": "healthy",
            "supported_languages": len(geo_localization_service.language_regions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "service": "geo-localization",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
