from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, NicheOpportunity, PurityMarketResearch
from ..services.niche_finder_service import NicheFinderService

router = APIRouter(prefix="/niche-finder", tags=["Niche Finder"])

class ProfitableNicheRequest(BaseModel):
    industry: str = Field(..., description="Industry to search in")
    budget_range: str = Field(..., description="Budget range for business")
    skills: List[str] = Field(..., description="Skills and expertise")
    interests: List[str] = Field(..., description="Personal interests")
    market_size_preference: str = Field(..., description="Preferred market size")

class NicheCompetitionRequest(BaseModel):
    niche_name: str = Field(..., description="Niche name to analyze")
    geographic_market: str = Field(..., description="Geographic market")
    analysis_depth: str = Field(..., description="Analysis depth")

class MarketGapsRequest(BaseModel):
    target_market: str = Field(..., description="Target market")
    customer_pain_points: List[str] = Field(..., description="Customer pain points")
    existing_solutions: List[str] = Field(..., description="Existing solutions")

class NicheValidationRequest(BaseModel):
    niche_name: str = Field(..., description="Niche name")
    target_audience: str = Field(..., description="Target audience")
    business_model: str = Field(..., description="Business model")
    validation_criteria: List[str] = Field(..., description="Validation criteria")

@router.post("/find-profitable-niches")
async def find_profitable_niches(
    request: ProfitableNicheRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Find profitable niches based on criteria"""
    try:
        service = NicheFinderService()
        result = await service.find_profitable_niches(
            db=db,
            industry=request.industry,
            budget_range=request.budget_range,
            skills=request.skills,
            interests=request.interests,
            market_size_preference=request.market_size_preference
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Found {len(result.get('niche_opportunities', []))} profitable niches in {request.industry}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find profitable niches: {str(e)}"
        )

@router.post("/analyze-competition")
async def analyze_niche_competition(
    request: NicheCompetitionRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze competition in a specific niche"""
    try:
        service = NicheFinderService()
        result = await service.analyze_niche_competition(
            db=db,
            niche_name=request.niche_name,
            geographic_market=request.geographic_market,
            analysis_depth=request.analysis_depth
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Competition analysis completed for {request.niche_name} in {request.geographic_market}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze niche competition: {str(e)}"
        )

@router.post("/identify-market-gaps")
async def identify_market_gaps(
    request: MarketGapsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Identify market gaps and opportunities"""
    try:
        service = NicheFinderService()
        result = await service.identify_market_gaps(
            db=db,
            target_market=request.target_market,
            customer_pain_points=request.customer_pain_points,
            existing_solutions=request.existing_solutions
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Identified {len(result.get('identified_gaps', []))} market gaps in {request.target_market}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify market gaps: {str(e)}"
        )

@router.post("/validate-opportunity")
async def validate_niche_opportunity(
    request: NicheValidationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Validate a niche opportunity"""
    try:
        service = NicheFinderService()
        result = await service.validate_niche_opportunity(
            db=db,
            niche_name=request.niche_name,
            target_audience=request.target_audience,
            business_model=request.business_model,
            validation_criteria=request.validation_criteria
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Niche validation completed with score: {result.get('validation_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate niche opportunity: {str(e)}"
        )

@router.get("/niche-categories")
async def get_niche_categories(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get different niche categories and examples"""
    try:
        niche_categories = {
            "health_wellness": {
                "name": "Health & Wellness",
                "description": "Physical and mental health niches",
                "subcategories": [
                    {
                        "name": "Fitness",
                        "examples": ["Home workout equipment", "Fitness apps", "Personal training"],
                        "market_size": "Large",
                        "competition": "High",
                        "profitability": "Medium to High"
                    },
                    {
                        "name": "Mental Health",
                        "examples": ["Meditation apps", "Therapy platforms", "Stress relief products"],
                        "market_size": "Large",
                        "competition": "Medium",
                        "profitability": "High"
                    },
                    {
                        "name": "Nutrition",
                        "examples": ["Meal planning", "Supplements", "Diet coaching"],
                        "market_size": "Large",
                        "competition": "High",
                        "profitability": "Medium"
                    }
                ]
            },
            "technology": {
                "name": "Technology",
                "description": "Tech-related niches and solutions",
                "subcategories": [
                    {
                        "name": "SaaS",
                        "examples": ["Business tools", "Productivity apps", "Industry-specific software"],
                        "market_size": "Very Large",
                        "competition": "High",
                        "profitability": "High"
                    },
                    {
                        "name": "Mobile Apps",
                        "examples": ["Utility apps", "Entertainment", "Educational apps"],
                        "market_size": "Large",
                        "competition": "Very High",
                        "profitability": "Variable"
                    },
                    {
                        "name": "AI/ML",
                        "examples": ["AI tools", "Machine learning services", "Automation"],
                        "market_size": "Growing",
                        "competition": "Medium",
                        "profitability": "High"
                    }
                ]
            },
            "education": {
                "name": "Education",
                "description": "Learning and educational niches",
                "subcategories": [
                    {
                        "name": "Online Learning",
                        "examples": ["Course platforms", "Skill training", "Certification programs"],
                        "market_size": "Large",
                        "competition": "Medium",
                        "profitability": "High"
                    },
                    {
                        "name": "EdTech",
                        "examples": ["Learning management systems", "Educational games", "Assessment tools"],
                        "market_size": "Large",
                        "competition": "Medium",
                        "profitability": "High"
                    },
                    {
                        "name": "Tutoring",
                        "examples": ["Online tutoring", "Test preparation", "Language learning"],
                        "market_size": "Medium",
                        "competition": "Medium",
                        "profitability": "Medium to High"
                    }
                ]
            },
            "ecommerce": {
                "name": "E-commerce",
                "description": "Online retail and product niches",
                "subcategories": [
                    {
                        "name": "Dropshipping",
                        "examples": ["Trending products", "Niche products", "Custom products"],
                        "market_size": "Large",
                        "competition": "High",
                        "profitability": "Variable"
                    },
                    {
                        "name": "Print on Demand",
                        "examples": ["Custom t-shirts", "Art prints", "Personalized items"],
                        "market_size": "Medium",
                        "competition": "Medium",
                        "profitability": "Medium"
                    },
                    {
                        "name": "Subscription Boxes",
                        "examples": ["Monthly boxes", "Curated products", "Specialty items"],
                        "market_size": "Medium",
                        "competition": "Medium",
                        "profitability": "High"
                    }
                ]
            },
            "services": {
                "name": "Services",
                "description": "Service-based business niches",
                "subcategories": [
                    {
                        "name": "Consulting",
                        "examples": ["Business consulting", "Marketing consulting", "Financial consulting"],
                        "market_size": "Large",
                        "competition": "Medium",
                        "profitability": "High"
                    },
                    {
                        "name": "Freelance Services",
                        "examples": ["Design services", "Writing services", "Development services"],
                        "market_size": "Large",
                        "competition": "High",
                        "profitability": "Variable"
                    },
                    {
                        "name": "Local Services",
                        "examples": ["Home services", "Professional services", "Specialty services"],
                        "market_size": "Medium",
                        "competition": "Medium",
                        "profitability": "Medium to High"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": niche_categories,
            "message": "Niche categories retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve niche categories: {str(e)}"
        )

@router.get("/niche-research-tools")
async def get_niche_research_tools(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get tools and resources for niche research"""
    try:
        research_tools = {
            "keyword_research": {
                "name": "Keyword Research Tools",
                "tools": [
                    {
                        "name": "Google Keyword Planner",
                        "description": "Free keyword research tool from Google",
                        "features": ["Search volume", "Competition level", "Keyword suggestions"],
                        "cost": "Free"
                    },
                    {
                        "name": "Ahrefs",
                        "description": "Comprehensive SEO and keyword research tool",
                        "features": ["Keyword difficulty", "Search volume", "Competitor analysis"],
                        "cost": "Paid"
                    },
                    {
                        "name": "SEMrush",
                        "description": "Competitive research and keyword analysis",
                        "features": ["Keyword research", "Competitor analysis", "Market analysis"],
                        "cost": "Paid"
                    }
                ]
            },
            "market_research": {
                "name": "Market Research Tools",
                "tools": [
                    {
                        "name": "Google Trends",
                        "description": "Analyze search trends and interest over time",
                        "features": ["Trend analysis", "Geographic data", "Related topics"],
                        "cost": "Free"
                    },
                    {
                        "name": "Statista",
                        "description": "Statistics and market data platform",
                        "features": ["Market statistics", "Industry reports", "Consumer insights"],
                        "cost": "Paid"
                    },
                    {
                        "name": "IBISWorld",
                        "description": "Industry research and market analysis",
                        "features": ["Industry reports", "Market size", "Competitive landscape"],
                        "cost": "Paid"
                    }
                ]
            },
            "competitor_analysis": {
                "name": "Competitor Analysis Tools",
                "tools": [
                    {
                        "name": "SimilarWeb",
                        "description": "Website traffic and competitor analysis",
                        "features": ["Traffic analysis", "Competitor insights", "Market share"],
                        "cost": "Paid"
                    },
                    {
                        "name": "SpyFu",
                        "description": "Competitor keyword and ad research",
                        "features": ["Keyword research", "Ad analysis", "Competitor tracking"],
                        "cost": "Paid"
                    },
                    {
                        "name": "Built With",
                        "description": "Technology stack analysis",
                        "features": ["Tech stack", "Traffic analysis", "Competitor insights"],
                        "cost": "Free/Paid"
                    }
                ]
            },
            "social_media_research": {
                "name": "Social Media Research Tools",
                "tools": [
                    {
                        "name": "BuzzSumo",
                        "description": "Content research and social media analysis",
                        "features": ["Content analysis", "Social engagement", "Trending topics"],
                        "cost": "Paid"
                    },
                    {
                        "name": "Social Mention",
                        "description": "Social media monitoring and analysis",
                        "features": ["Brand monitoring", "Sentiment analysis", "Trend tracking"],
                        "cost": "Free"
                    },
                    {
                        "name": "Hootsuite Insights",
                        "description": "Social media listening and analytics",
                        "features": ["Social listening", "Trend analysis", "Competitor monitoring"],
                        "cost": "Paid"
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": research_tools,
            "message": "Niche research tools retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve niche research tools: {str(e)}"
        )

@router.get("/niche-validation-criteria")
async def get_niche_validation_criteria(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get criteria for validating niche opportunities"""
    try:
        validation_criteria = {
            "market_viability": {
                "name": "Market Viability",
                "criteria": [
                    {
                        "name": "Market Size",
                        "description": "Is the market large enough to support your business?",
                        "questions": [
                            "What is the total addressable market (TAM)?",
                            "What is the serviceable addressable market (SAM)?",
                            "What is the serviceable obtainable market (SOM)?"
                        ],
                        "thresholds": {
                            "excellent": "> $1B TAM",
                            "good": "$100M - $1B TAM",
                            "fair": "$10M - $100M TAM",
                            "poor": "< $10M TAM"
                        }
                    },
                    {
                        "name": "Market Growth",
                        "description": "Is the market growing or declining?",
                        "questions": [
                            "What is the annual growth rate?",
                            "Are there any market trends driving growth?",
                            "Is the market mature or emerging?"
                        ],
                        "thresholds": {
                            "excellent": "> 20% annual growth",
                            "good": "10-20% annual growth",
                            "fair": "5-10% annual growth",
                            "poor": "< 5% or declining"
                        }
                    },
                    {
                        "name": "Customer Demand",
                        "description": "Is there sufficient customer demand?",
                        "questions": [
                            "Are customers actively searching for solutions?",
                            "Are there existing successful businesses?",
                            "What is the customer pain point intensity?"
                        ],
                        "thresholds": {
                            "excellent": "High search volume, strong pain points",
                            "good": "Medium search volume, clear pain points",
                            "fair": "Low search volume, mild pain points",
                            "poor": "No search volume, unclear pain points"
                        }
                    }
                ]
            },
            "competitive_analysis": {
                "name": "Competitive Analysis",
                "criteria": [
                    {
                        "name": "Competition Level",
                        "description": "What is the level of competition?",
                        "questions": [
                            "How many competitors are there?",
                            "How strong are the competitors?",
                            "Is there room for differentiation?"
                        ],
                        "thresholds": {
                            "excellent": "Low competition, high differentiation opportunity",
                            "good": "Medium competition, clear differentiation",
                            "fair": "High competition, limited differentiation",
                            "poor": "Very high competition, no differentiation"
                        }
                    },
                    {
                        "name": "Barrier to Entry",
                        "description": "What are the barriers to entering this niche?",
                        "questions": [
                            "What are the startup costs?",
                            "Are there regulatory requirements?",
                            "What skills and resources are needed?"
                        ],
                        "thresholds": {
                            "excellent": "Low barriers, accessible to you",
                            "good": "Moderate barriers, manageable",
                            "fair": "High barriers, challenging",
                            "poor": "Very high barriers, prohibitive"
                        }
                    },
                    {
                        "name": "Competitive Advantages",
                        "description": "What advantages do you have over competitors?",
                        "questions": [
                            "What unique skills or experience do you have?",
                            "What resources or connections do you have?",
                            "What can you do better than competitors?"
                        ],
                        "thresholds": {
                            "excellent": "Multiple strong competitive advantages",
                            "good": "Some competitive advantages",
                            "fair": "Limited competitive advantages",
                            "poor": "No competitive advantages"
                        }
                    }
                ]
            },
            "financial_feasibility": {
                "name": "Financial Feasibility",
                "criteria": [
                    {
                        "name": "Revenue Potential",
                        "description": "What is the revenue potential?",
                        "questions": [
                            "What is the average customer lifetime value?",
                            "What are the pricing models in this niche?",
                            "What is the revenue per customer?"
                        ],
                        "thresholds": {
                            "excellent": "High LTV, multiple revenue streams",
                            "good": "Good LTV, clear revenue model",
                            "fair": "Moderate LTV, basic revenue model",
                            "poor": "Low LTV, unclear revenue model"
                        }
                    },
                    {
                        "name": "Profitability",
                        "description": "What is the profit margin potential?",
                        "questions": [
                            "What are the typical profit margins?",
                            "What are the main cost drivers?",
                            "Can you achieve economies of scale?"
                        ],
                        "thresholds": {
                            "excellent": "High margins, scalable model",
                            "good": "Good margins, scalable model",
                            "fair": "Moderate margins, limited scalability",
                            "poor": "Low margins, not scalable"
                        }
                    },
                    {
                        "name": "Funding Requirements",
                        "description": "How much funding is required?",
                        "questions": [
                            "What are the startup costs?",
                            "How long until profitability?",
                            "What funding sources are available?"
                        ],
                        "thresholds": {
                            "excellent": "Low startup costs, quick profitability",
                            "good": "Moderate startup costs, reasonable timeline",
                            "fair": "High startup costs, longer timeline",
                            "poor": "Very high startup costs, uncertain timeline"
                        }
                    }
                ]
            }
        }
        return {
            "status": "success",
            "data": validation_criteria,
            "message": "Niche validation criteria retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve niche validation criteria: {str(e)}"
        )
