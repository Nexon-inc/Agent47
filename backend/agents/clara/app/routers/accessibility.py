from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.accessibility_service import AccessibilityService

router = APIRouter()

# Pydantic models for request/response
class AccessibilityEnhancementRequest(BaseModel):
    response_text: str
    accessibility_features: Optional[List[str]] = None

class AccessibilityScoreRequest(BaseModel):
    text: str

# Dependency
async def get_accessibility_service() -> AccessibilityService:
    service = AccessibilityService()
    await service.initialize()
    return service

@router.post("/enhance/response", response_model=Dict[str, Any])
async def enhance_response_accessibility(
    request: AccessibilityEnhancementRequest,
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Enhance response text for accessibility"""
    try:
        result = await service.enhance_response_accessibility(
            response_text=request.response_text,
            accessibility_features=request.accessibility_features
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score/calculate", response_model=Dict[str, Any])
async def calculate_accessibility_score(
    request: AccessibilityScoreRequest,
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Calculate accessibility score for text"""
    try:
        # Use the enhance method to get the score
        result = await service.enhance_response_accessibility(
            response_text=request.text,
            accessibility_features=["screen_reader", "high_contrast", "plain_language"]
        )
        
        if result["success"]:
            return {
                "success": True,
                "text": request.text,
                "accessibility_score": result["accessibility_score"],
                "enhanced_text": result["enhanced_response"],
                "features_applied": result["accessibility_features_applied"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/features/available", response_model=Dict[str, Any])
async def get_available_accessibility_features(
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Get list of available accessibility features"""
    try:
        features = {
            "success": True,
            "available_features": [
                {
                    "id": "screen_reader",
                    "name": "Screen Reader Support",
                    "description": "Adds semantic markers and structure for screen readers",
                    "icon": "🔊",
                    "enabled": True
                },
                {
                    "id": "high_contrast",
                    "description": "Adds visual indicators for high contrast mode",
                    "icon": "🎨",
                    "enabled": True
                },
                {
                    "id": "plain_language",
                    "name": "Plain Language",
                    "description": "Simplifies complex language for better comprehension",
                    "icon": "📝",
                    "enabled": True
                }
            ],
            "feature_descriptions": {
                "screen_reader": "Marks headings, lists, actions, and important information for screen readers",
                "high_contrast": "Adds visual indicators like emojis and labels for better visibility",
                "plain_language": "Uses AI to simplify complex sentences and improve readability"
            }
        }
        
        return features
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guidelines/compliance", response_model=Dict[str, Any])
async def get_accessibility_guidelines(
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Get accessibility compliance guidelines"""
    try:
        guidelines = {
            "success": True,
            "accessibility_guidelines": {
                "wcag_2_1": {
                    "level": "AA",
                    "compliance": "Compliant",
                    "criteria": [
                        "1.1.1 Non-text Content",
                        "1.3.1 Info and Relationships",
                        "1.4.1 Use of Color",
                        "2.1.1 Keyboard",
                        "2.4.4 Link Purpose (In Context)",
                        "3.1.2 Language of Parts"
                    ]
                },
                "best_practices": [
                    "Use clear, simple language",
                    "Provide alternative text for images",
                    "Ensure sufficient color contrast",
                    "Use semantic HTML structure",
                    "Provide keyboard navigation",
                    "Test with screen readers"
                ],
                "tools": [
                    "Screen reader testing",
                    "Color contrast checkers",
                    "Keyboard navigation testing",
                    "Language complexity analysis"
                ]
            }
        }
        
        return guidelines
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/usage", response_model=Dict[str, Any])
async def get_accessibility_usage_statistics(
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Get accessibility feature usage statistics"""
    try:
        # Get accessibility usage statistics from the service
        stats = await service.get_accessibility_usage_statistics()
        
        return {
            "success": True,
            "accessibility_usage_stats": stats
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demo/enhancement", response_model=Dict[str, Any])
async def demonstrate_accessibility_enhancement(
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Demonstrate accessibility enhancement with sample text"""
    try:
        sample_text = "Important: Please click here to submit your request. Note that this process may take several minutes to complete."
        
        result = await service.enhance_response_accessibility(
            response_text=sample_text,
            accessibility_features=["screen_reader", "high_contrast", "plain_language"]
        )
        
        if result["success"]:
            demo = {
                "success": True,
                "demonstration": {
                    "original_text": sample_text,
                    "enhanced_text": result["enhanced_response"],
                    "accessibility_score": result["accessibility_score"],
                    "features_applied": result["accessibility_features_applied"],
                    "improvements_made": [
                        "Added semantic markers for screen readers",
                        "Enhanced visual indicators for high contrast",
                        "Simplified language for better comprehension"
                    ]
                }
            }
            
            return demo
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
