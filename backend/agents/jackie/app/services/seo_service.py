import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import SEOProject

logger = logging.getLogger(__name__)

class SEOService:
    def __init__(self):
        self.db = None
        self.event_bus = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        self.db = await get_jackie_database()
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        self._initialized = True
    
    async def analyze_seo(
        self,
        user_id: int,
        website_url: str,
        target_keywords: List[str],
        competitor_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                seo_score = await self._calculate_seo_score(website_url, target_keywords)
                keyword_rankings = await self._analyze_keyword_rankings(target_keywords)
                competitor_analysis = await self._analyze_competitors(competitor_urls) if competitor_urls else {}
                
                seo_project = SEOProject(
                    user_id=user_id,
                    project_name=f"SEO Analysis - {website_url}",
                    website_url=website_url,
                    target_keywords=target_keywords,
                    current_rankings=keyword_rankings,
                    seo_score=seo_score,
                    organic_traffic=0,
                    backlinks_count=0,
                    page_speed_score=0.0,
                    mobile_friendly_score=0.0,
                    recommendations=await self._generate_seo_recommendations(seo_score, keyword_rankings)
                )
                
                session.add(seo_project)
                await session.commit()
                await session.refresh(seo_project)
                
                return {
                    "success": True,
                    "seo_analysis": {
                        "project_id": seo_project.id,
                        "website_url": seo_project.website_url,
                        "seo_score": seo_project.seo_score,
                        "keyword_rankings": seo_project.current_rankings,
                        "competitor_analysis": competitor_analysis,
                        "recommendations": seo_project.recommendations
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze SEO: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_seo(
        self,
        user_id: int,
        content: str,
        target_keywords: List[str],
        content_type: str
    ) -> Dict[str, Any]:
        try:
            optimized_content = await self._optimize_content_for_seo(content, target_keywords, content_type)
            keyword_density = await self._calculate_keyword_density(optimized_content, target_keywords)
            seo_suggestions = await self._generate_content_suggestions(optimized_content, target_keywords)
            
            return {
                "success": True,
                "seo_optimization": {
                    "optimized_content": optimized_content,
                    "keyword_density": keyword_density,
                    "seo_suggestions": seo_suggestions,
                    "content_type": content_type
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize SEO: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_keyword_rankings(self, project_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(SEOProject).where(SEOProject.id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if not project:
                    return {"success": False, "error": "SEO project not found"}
                
                return {
                    "success": True,
                    "keyword_rankings": {
                        "project_id": project.id,
                        "website_url": project.website_url,
                        "target_keywords": project.target_keywords,
                        "current_rankings": project.current_rankings,
                        "seo_score": project.seo_score
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get keyword rankings: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_backlinks(self, website_url: str) -> Dict[str, Any]:
        try:
            backlink_analysis = await self._analyze_backlinks(website_url)
            
            return {
                "success": True,
                "backlink_analysis": backlink_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze backlinks: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_seo_score(self, website_url: str, target_keywords: List[str]) -> float:
        base_score = 75.0
        
        if len(target_keywords) > 0:
            base_score += 10.0
        
        if "https" in website_url:
            base_score += 5.0
        
        return min(base_score, 100.0)
    
    async def _analyze_keyword_rankings(self, target_keywords: List[str]) -> Dict[str, Any]:
        rankings = {}
        for keyword in target_keywords:
            rankings[keyword] = {
                "position": 50,
                "search_volume": 1000,
                "difficulty": "medium"
            }
        return rankings
    
    async def _analyze_competitors(self, competitor_urls: List[str]) -> Dict[str, Any]:
        competitor_analysis = {}
        for url in competitor_urls:
            competitor_analysis[url] = {
                "domain_authority": 45,
                "backlinks": 1000,
                "organic_traffic": 5000
            }
        return competitor_analysis
    
    async def _generate_seo_recommendations(self, seo_score: float, keyword_rankings: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if seo_score < 80:
            recommendations.append("Improve on-page SEO optimization")
        
        if seo_score < 70:
            recommendations.append("Focus on technical SEO improvements")
        
        recommendations.append("Build high-quality backlinks")
        recommendations.append("Create more relevant content")
        
        return recommendations
    
    async def _optimize_content_for_seo(self, content: str, target_keywords: List[str], content_type: str) -> str:
        """Optimize content for SEO using AI Service Manager"""
        from core.ai import get_ai_service_manager
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that optimizes content for SEO."},
            {"role": "user", "content": f"Optimize this {content_type} content for SEO with target keywords: {', '.join(target_keywords)}\n\nContent: {content}"}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        return ai_response.text_content if ai_response.success else content
    
    async def _calculate_keyword_density(self, content: str, target_keywords: List[str]) -> Dict[str, float]:
        density = {}
        total_words = len(content.split())
        
        for keyword in target_keywords:
            keyword_count = content.lower().count(keyword.lower())
            density[keyword] = (keyword_count / total_words * 100) if total_words > 0 else 0
        
        return density
    
    async def _generate_content_suggestions(self, content: str, target_keywords: List[str]) -> List[str]:
        suggestions = []
        
        if len(content) < 300:
            suggestions.append("Increase content length for better SEO")
        
        if len(target_keywords) > 0:
            suggestions.append("Include more target keywords naturally")
        
        suggestions.append("Add relevant internal and external links")
        suggestions.append("Optimize meta descriptions and titles")
        
        return suggestions
    
    async def _analyze_backlinks(self, website_url: str) -> Dict[str, Any]:
        return {
            "total_backlinks": 1500,
            "domain_authority": 45,
            "spam_score": 2,
            "top_referring_domains": [
                {"domain": "example.com", "authority": 80},
                {"domain": "another-example.com", "authority": 65}
            ],
            "anchor_text_distribution": {
                "branded": 40,
                "generic": 30,
                "exact_match": 20,
                "partial_match": 10
            }
        }
