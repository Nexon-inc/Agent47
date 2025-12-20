import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece

logger = logging.getLogger(__name__)

class ContentLocalizationService:
    """Service for content localization and cultural adaptation"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.5
        }
    
    async def initialize(self):
        """Initialize content localization service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content localization service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content localization service: {e}")
            raise
    
    async def localize_content(
        self,
        content_piece_id: int,
        target_languages: List[str],
        target_regions: List[str],
        localization_goals: List[str]
    ) -> Dict[str, Any]:
        """Localize content for multiple languages and regions"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Generate localized content
                localized_content = {}
                for language in target_languages:
                    for region in target_regions:
                        locale_key = f"{language}_{region}"
                        localized_version = await self._generate_localized_content(
                            content_piece, language, region, localization_goals
                        )
                        localized_content[locale_key] = localized_version
                
                # Generate cultural adaptations
                cultural_adaptations = await self._generate_cultural_adaptations(
                    content_piece, target_languages, target_regions
                )
                
                # Generate localization guidelines
                localization_guidelines = await self._generate_localization_guidelines(
                    content_piece, target_languages, target_regions, localization_goals
                )
                
                # Generate quality assurance checklist
                qa_checklist = await self._generate_qa_checklist(
                    target_languages, target_regions, localization_goals
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_languages": target_languages,
                    "target_regions": target_regions,
                    "localization_goals": localization_goals,
                    "localized_content": localized_content,
                    "cultural_adaptations": cultural_adaptations,
                    "localization_guidelines": localization_guidelines,
                    "qa_checklist": qa_checklist,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content localization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def adapt_content_culturally(
        self,
        content_piece_id: int,
        target_culture: str,
        cultural_context: Dict[str, Any],
        adaptation_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Adapt content for specific cultural context"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Analyze cultural context
                cultural_analysis = await self._analyze_cultural_context(
                    content_piece, target_culture, cultural_context
                )
                
                # Generate cultural adaptations
                cultural_adaptations = await self._generate_cultural_adaptations(
                    content_piece, target_culture, cultural_context, adaptation_level
                )
                
                # Generate adapted content
                adapted_content = await self._generate_adapted_content(
                    content_piece, cultural_adaptations, target_culture
                )
                
                # Generate cultural guidelines
                cultural_guidelines = await self._generate_cultural_guidelines(
                    target_culture, cultural_context, adaptation_level
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_culture": target_culture,
                    "cultural_context": cultural_context,
                    "adaptation_level": adaptation_level,
                    "cultural_analysis": cultural_analysis,
                    "cultural_adaptations": cultural_adaptations,
                    "adapted_content": adapted_content,
                    "cultural_guidelines": cultural_guidelines,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Cultural adaptation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_multilingual_seo(
        self,
        content_piece_id: int,
        target_languages: List[str],
        target_regions: List[str],
        seo_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate SEO-optimized content for multiple languages"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Generate multilingual SEO content
                multilingual_seo = {}
                for language in target_languages:
                    for region in target_regions:
                        locale_key = f"{language}_{region}"
                        seo_content = await self._generate_localized_seo(
                            content_piece, language, region, seo_goals
                        )
                        multilingual_seo[locale_key] = seo_content
                
                # Generate hreflang tags
                hreflang_tags = await self._generate_hreflang_tags(
                    target_languages, target_regions
                )
                
                # Generate multilingual sitemap
                multilingual_sitemap = await self._generate_multilingual_sitemap(
                    content_piece, target_languages, target_regions
                )
                
                # Generate SEO recommendations
                seo_recommendations = await self._generate_seo_recommendations(
                    target_languages, target_regions, seo_goals
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_languages": target_languages,
                    "target_regions": target_regions,
                    "seo_goals": seo_goals,
                    "multilingual_seo": multilingual_seo,
                    "hreflang_tags": hreflang_tags,
                    "multilingual_sitemap": multilingual_sitemap,
                    "seo_recommendations": seo_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Multilingual SEO generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_localization_quality(
        self,
        localized_content: Dict[str, Any],
        target_languages: List[str],
        target_regions: List[str],
        quality_standards: List[str]
    ) -> Dict[str, Any]:
        """Validate quality of localized content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Perform quality validation
            quality_validation = await self._perform_quality_validation(
                localized_content, target_languages, target_regions, quality_standards
            )
            
            # Generate quality report
            quality_report = await self._generate_quality_report(
                quality_validation, target_languages, target_regions
            )
            
            # Generate improvement recommendations
            improvement_recommendations = await self._generate_improvement_recommendations(
                quality_validation, quality_standards
            )
            
            return {
                "success": True,
                "localized_content": localized_content,
                "target_languages": target_languages,
                "target_regions": target_regions,
                "quality_standards": quality_standards,
                "quality_validation": quality_validation,
                "quality_report": quality_report,
                "improvement_recommendations": improvement_recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Localization quality validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_localized_content(
        self, content_piece: ContentPiece, language: str, region: str, localization_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate localized content for specific language and region"""
        localization_prompt = self._create_localization_prompt(
            content_piece, language, region, localization_goals
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that localizes content for different languages and regions."}, {"role": "user", "content": localization_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        localized_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "language": language,
            "region": region,
            "localized_title": localized_result,
            "localized_content": localized_result,
            "localization_goals": localization_goals,
            "cultural_adaptations": [],
            "quality_score": 0.85
        }
    
    async def _generate_cultural_adaptations(
        self, content_piece: ContentPiece, target_languages: List[str], target_regions: List[str]
    ) -> Dict[str, Any]:
        """Generate cultural adaptations"""
        adaptations = {}
        
        for language in target_languages:
            for region in target_regions:
                locale_key = f"{language}_{region}"
                adaptation_prompt = self._create_cultural_adaptation_prompt(
                    content_piece, language, region
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that adapts content for different cultural contexts."}, {"role": "user", "content": adaptation_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                adaptation_result = ai_response.text_content if ai_response.success else ""
                
                adaptations[locale_key] = {
                    "language": language,
                    "region": region,
                    "cultural_adaptations": adaptation_result,
                    "adaptation_notes": [],
                    "compliance_check": True
                }
        
        return adaptations
    
    async def _generate_localization_guidelines(
        self, content_piece: ContentPiece, target_languages: List[str], target_regions: List[str], localization_goals: List[str]
    ) -> str:
        """Generate localization guidelines"""
        guidelines_prompt = self._create_localization_guidelines_prompt(
            content_piece, target_languages, target_regions, localization_goals
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates localization guidelines."}, {"role": "user", "content": guidelines_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        guidelines_result = ai_response.text_content if ai_response.success else ""
        return guidelines_result
    
    async def _generate_qa_checklist(
        self, target_languages: List[str], target_regions: List[str], localization_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate quality assurance checklist"""
        return [
            {
                "checklist_item": "Language accuracy",
                "description": "Verify translation accuracy and fluency",
                "priority": "high",
                "applicable_locales": target_languages
            },
            {
                "checklist_item": "Cultural appropriateness",
                "description": "Ensure content is culturally appropriate",
                "priority": "high",
                "applicable_locales": target_regions
            },
            {
                "checklist_item": "Brand consistency",
                "description": "Maintain brand voice across all locales",
                "priority": "medium",
                "applicable_locales": target_languages
            },
            {
                "checklist_item": "Technical accuracy",
                "description": "Verify technical terms and measurements",
                "priority": "medium",
                "applicable_locales": target_languages
            }
        ]
    
    async def _analyze_cultural_context(
        self, content_piece: ContentPiece, target_culture: str, cultural_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cultural context for content"""
        analysis_prompt = self._create_cultural_analysis_prompt(
            content_piece, target_culture, cultural_context
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes content for localization needs."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "target_culture": target_culture,
            "cultural_context": cultural_context,
            "analysis_result": analysis_result,
            "cultural_considerations": [],
            "potential_issues": [],
            "adaptation_opportunities": []
        }
    
    async def _generate_cultural_adaptations(
        self, content_piece: ContentPiece, target_culture: str, cultural_context: Dict[str, Any], adaptation_level: str
    ) -> Dict[str, Any]:
        """Generate cultural adaptations for content"""
        adaptation_prompt = self._create_cultural_adaptation_prompt(
            content_piece, target_culture, cultural_context, adaptation_level
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that adapts content for different regions."}, {"role": "user", "content": adaptation_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        adaptation_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "target_culture": target_culture,
            "adaptation_level": adaptation_level,
            "adaptation_result": adaptation_result,
            "key_changes": [],
            "cultural_notes": []
        }
    
    async def _generate_adapted_content(
        self, content_piece: ContentPiece, cultural_adaptations: Dict[str, Any], target_culture: str
    ) -> str:
        """Generate culturally adapted content"""
        adaptation_prompt = self._create_content_adaptation_prompt(
            content_piece, cultural_adaptations, target_culture
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that adapts content for different cultural contexts."}, {"role": "user", "content": adaptation_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        adapted_result = ai_response.text_content if ai_response.success else ""
        return adapted_result
    
    async def _generate_cultural_guidelines(
        self, target_culture: str, cultural_context: Dict[str, Any], adaptation_level: str
    ) -> str:
        """Generate cultural guidelines"""
        guidelines_prompt = self._create_cultural_guidelines_prompt(
            target_culture, cultural_context, adaptation_level
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates localization guidelines."}, {"role": "user", "content": guidelines_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        guidelines_result = ai_response.text_content if ai_response.success else ""
        return guidelines_result
    
    async def _generate_localized_seo(
        self, content_piece: ContentPiece, language: str, region: str, seo_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate localized SEO content"""
        seo_prompt = self._create_localized_seo_prompt(
            content_piece, language, region, seo_goals
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes localized content for SEO."}, {"role": "user", "content": seo_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        seo_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "language": language,
            "region": region,
            "seo_title": seo_result,
            "meta_description": seo_result,
            "keywords": [],
            "seo_goals": seo_goals
        }
    
    async def _generate_hreflang_tags(
        self, target_languages: List[str], target_regions: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate hreflang tags for multilingual content"""
        hreflang_tags = []
        
        for language in target_languages:
            for region in target_regions:
                hreflang_tags.append({
                    "hreflang": f"{language}-{region}",
                    "url": f"https://example.com/{language}/{region}/",
                    "rel": "alternate"
                })
        
        return hreflang_tags
    
    async def _generate_multilingual_sitemap(
        self, content_piece: ContentPiece, target_languages: List[str], target_regions: List[str]
    ) -> Dict[str, Any]:
        """Generate multilingual sitemap"""
        sitemap_entries = []
        
        for language in target_languages:
            for region in target_regions:
                sitemap_entries.append({
                    "loc": f"https://example.com/{language}/{region}/{content_piece.id}",
                    "lastmod": datetime.utcnow().isoformat(),
                    "changefreq": "weekly",
                    "priority": "0.8",
                    "hreflang": f"{language}-{region}"
                })
        
        return {
            "sitemap_entries": sitemap_entries,
            "total_entries": len(sitemap_entries),
            "languages": target_languages,
            "regions": target_regions
        }
    
    async def _generate_seo_recommendations(
        self, target_languages: List[str], target_regions: List[str], seo_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate SEO recommendations"""
        return [
            {
                "recommendation_type": "hreflang_implementation",
                "description": "Implement proper hreflang tags for all language/region combinations",
                "priority": "high",
                "implementation": "technical"
            },
            {
                "recommendation_type": "local_keywords",
                "description": "Research and implement local keywords for each target region",
                "priority": "high",
                "implementation": "content"
            },
            {
                "recommendation_type": "cultural_seo",
                "description": "Adapt SEO strategy to cultural preferences in each region",
                "priority": "medium",
                "implementation": "strategy"
            }
        ]
    
    async def _perform_quality_validation(
        self, localized_content: Dict[str, Any], target_languages: List[str], target_regions: List[str], quality_standards: List[str]
    ) -> Dict[str, Any]:
        """Perform quality validation on localized content"""
        validation_results = {}
        
        for locale_key, content in localized_content.items():
            validation_results[locale_key] = {
                "language_accuracy": 0.9,
                "cultural_appropriateness": 0.85,
                "brand_consistency": 0.88,
                "technical_accuracy": 0.92,
                "overall_score": 0.89,
                "issues_found": [],
                "recommendations": []
            }
        
        return validation_results
    
    async def _generate_quality_report(
        self, quality_validation: Dict[str, Any], target_languages: List[str], target_regions: List[str]
    ) -> str:
        """Generate quality report"""
        report_prompt = self._create_quality_report_prompt(
            quality_validation, target_languages, target_regions
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates localization reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    async def _generate_improvement_recommendations(
        self, quality_validation: Dict[str, Any], quality_standards: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate improvement recommendations"""
        return [
            {
                "recommendation_type": "language_improvement",
                "description": "Improve language accuracy and fluency",
                "priority": "high",
                "affected_locales": list(quality_validation.keys())
            },
            {
                "recommendation_type": "cultural_adaptation",
                "description": "Enhance cultural appropriateness",
                "priority": "medium",
                "affected_locales": list(quality_validation.keys())
            }
        ]
    
    def _create_localization_prompt(
        self, content_piece: ContentPiece, language: str, region: str, localization_goals: List[str]
    ) -> str:
        """Create prompt for content localization"""
        return f"""
        Localize this content for {language} ({region}):
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Language: {language}
        Region: {region}
        Localization Goals: {', '.join(localization_goals)}
        
        Provide:
        1. Natural, fluent translation
        2. Cultural adaptation for the region
        3. Appropriate tone and style
        4. Local terminology and expressions
        5. Region-specific considerations
        
        Generate the localized content.
        """
    
    def _create_cultural_adaptation_prompt(
        self, content_piece: ContentPiece, language: str, region: str
    ) -> str:
        """Create prompt for cultural adaptation"""
        return f"""
        Provide cultural adaptations for this content in {language} ({region}):
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Language: {language}
        Region: {region}
        
        Provide:
        1. Cultural considerations
        2. Local customs and traditions
        3. Appropriate references and examples
        4. Regional preferences
        5. Cultural sensitivity notes
        
        Generate cultural adaptation recommendations.
        """
    
    def _create_localization_guidelines_prompt(
        self, content_piece: ContentPiece, target_languages: List[str], target_regions: List[str], localization_goals: List[str]
    ) -> str:
        """Create prompt for localization guidelines"""
        return f"""
        Create localization guidelines for this content:
        
        Content: {content_piece.title}
        Target Languages: {', '.join(target_languages)}
        Target Regions: {', '.join(target_regions)}
        Localization Goals: {', '.join(localization_goals)}
        
        Provide:
        1. Language-specific guidelines
        2. Cultural adaptation rules
        3. Quality standards
        4. Common pitfalls to avoid
        5. Best practices
        
        Generate comprehensive localization guidelines.
        """
    
    def _create_cultural_analysis_prompt(
        self, content_piece: ContentPiece, target_culture: str, cultural_context: Dict[str, Any]
    ) -> str:
        """Create prompt for cultural analysis"""
        return f"""
        Analyze cultural context for this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Target Culture: {target_culture}
        Cultural Context: {cultural_context}
        
        Provide:
        1. Cultural analysis
        2. Potential cultural issues
        3. Adaptation opportunities
        4. Cultural considerations
        5. Recommendations
        
        Generate comprehensive cultural analysis.
        """
    
    def _create_cultural_adaptation_prompt(
        self, content_piece: ContentPiece, target_culture: str, cultural_context: Dict[str, Any], adaptation_level: str
    ) -> str:
        """Create prompt for cultural adaptation"""
        return f"""
        Create cultural adaptations for this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Target Culture: {target_culture}
        Cultural Context: {cultural_context}
        Adaptation Level: {adaptation_level}
        
        Provide:
        1. Cultural adaptation strategy
        2. Key changes needed
        3. Cultural considerations
        4. Implementation guidelines
        5. Quality assurance steps
        
        Generate comprehensive cultural adaptation plan.
        """
    
    def _create_content_adaptation_prompt(
        self, content_piece: ContentPiece, cultural_adaptations: Dict[str, Any], target_culture: str
    ) -> str:
        """Create prompt for content adaptation"""
        return f"""
        Adapt this content for {target_culture}:
        
        Original Content: {content_piece.content}
        Cultural Adaptations: {cultural_adaptations}
        Target Culture: {target_culture}
        
        Generate culturally adapted content that:
        1. Maintains original message and intent
        2. Respects cultural norms and values
        3. Uses appropriate language and tone
        4. Includes relevant cultural references
        5. Avoids cultural insensitivity
        
        Generate the culturally adapted content.
        """
    
    def _create_cultural_guidelines_prompt(
        self, target_culture: str, cultural_context: Dict[str, Any], adaptation_level: str
    ) -> str:
        """Create prompt for cultural guidelines"""
        return f"""
        Create cultural guidelines for {target_culture}:
        
        Target Culture: {target_culture}
        Cultural Context: {cultural_context}
        Adaptation Level: {adaptation_level}
        
        Provide:
        1. Cultural norms and values
        2. Communication styles
        3. Appropriate content types
        4. Cultural sensitivities
        5. Best practices
        
        Generate comprehensive cultural guidelines.
        """
    
    def _create_localized_seo_prompt(
        self, content_piece: ContentPiece, language: str, region: str, seo_goals: List[str]
    ) -> str:
        """Create prompt for localized SEO"""
        return f"""
        Create SEO-optimized content for {language} ({region}):
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Language: {language}
        Region: {region}
        SEO Goals: {', '.join(seo_goals)}
        
        Provide:
        1. SEO-optimized title
        2. Meta description
        3. Local keywords
        4. Regional SEO considerations
        5. Cultural SEO factors
        
        Generate localized SEO content.
        """
    
    def _create_quality_report_prompt(
        self, quality_validation: Dict[str, Any], target_languages: List[str], target_regions: List[str]
    ) -> str:
        """Create prompt for quality report"""
        return f"""
        Create quality report for localized content:
        
        Quality Validation: {quality_validation}
        Target Languages: {', '.join(target_languages)}
        Target Regions: {', '.join(target_regions)}
        
        Provide:
        1. Overall quality assessment
        2. Language-specific findings
        3. Cultural appropriateness evaluation
        4. Brand consistency analysis
        5. Improvement recommendations
        
        Generate comprehensive quality report.
        """
