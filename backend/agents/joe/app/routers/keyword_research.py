from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.keyword_research_service import KeywordResearchService

router = APIRouter(prefix="/keyword-research", tags=["Keyword Research"])

class KeywordResearchRequest(BaseModel):
    seed_keywords: List[str] = Field(..., description="Seed keywords to research")
    language: str = Field(default="en", description="JoeLanguage for research")
    country: str = Field(default="US", description="Country for research")

class KeywordSuggestionsRequest(BaseModel):
    topic: str = Field(..., description="Topic to get suggestions for")
    max_suggestions: int = Field(default=20, description="Maximum number of suggestions")

# Dependency
async def get_keyword_research_service() -> KeywordResearchService:
    service = KeywordResearchService()
    await service.initialize()
    return service

@router.post("/research")
async def research_keywords(
    request: KeywordResearchRequest,
    service: KeywordResearchService = Depends(get_keyword_research_service)
):
    """Research keywords based on seed keywords"""
    try:
        result = await service.research_keywords(
            user_id=1,  # TODO: Get from authentication
            seed_keywords=request.seed_keywords,
            language=request.language,
            country=request.country
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["keyword_data"],
                "message": f"Keyword research completed for {len(request.seed_keywords)} seed keywords"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Keyword research failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to research keywords: {str(e)}"
        )

@router.get("/suggestions")
async def get_keyword_suggestions(
    topic: str,
    max_suggestions: int = 20,
    service: KeywordResearchService = Depends(get_keyword_research_service)
):
    """Get keyword suggestions for a topic"""
    try:
        result = await service.get_keyword_suggestions(
            user_id=1,  # TODO: Get from authentication
            topic=topic,
            max_suggestions=max_suggestions
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["suggestions"],
                "message": f"Retrieved {len(result['suggestions'])} keyword suggestions for '{topic}'"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get keyword suggestions: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get keyword suggestions: {str(e)}"
        )

@router.get("/trending-keywords")
async def get_trending_keywords(service: KeywordResearchService = Depends(get_keyword_research_service)):
    """Get currently trending keywords"""
    trending_keywords = [
        {
            "keyword": "artificial intelligence",
            "search_volume": 50000,
            "growth_rate": 25,
            "competition": "high"
        },
        {
            "keyword": "machine learning",
            "search_volume": 35000,
            "growth_rate": 18,
            "competition": "high"
        },
        {
            "keyword": "blockchain",
            "search_volume": 28000,
            "growth_rate": 12,
            "competition": "medium"
        }
    ]
    
    return {
        "status": "success",
        "data": trending_keywords,
        "message": f"Retrieved {len(trending_keywords)} trending keywords"
    }
