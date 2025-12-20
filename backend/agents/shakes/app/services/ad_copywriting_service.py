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

class AdCopywritingService:
    """Service for AI-powered ad copy creation and optimization across multiple platforms"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize ad copywriting service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Ad copywriting service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ad copywriting service: {e}")
            raise
    
    async def create_ad_copy(
        self,
        user_id: int,
        platform: str,
        ad_type: str,
        product_service: str,
        target_audience: str,
        ad_objective: str,
        budget_range: str,
        call_to_action: str,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Create platform-optimized ad copy with AI-powered persuasion"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ContentProject(
                    user_id=user_id,
                    title=f"Ad Copy: {product_service}",
                    description=f"AI-generated {platform} {ad_type} ad for {product_service}",
                    content_type="ad_copy",
                    platform=platform,
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate ad copy
                ad_prompt = self._create_ad_copy_prompt(
                    platform, ad_type, product_service, target_audience,
                    ad_objective, budget_range, call_to_action, tone
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates compelling ad copy."}, {"role": "user", "content": ad_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.8)
                ad_copy = ai_response.text_content if ai_response.success else ""
                
                # Generate multiple variations
                variations_prompt = self._create_variations_prompt(
                    ad_copy, platform, ad_type, 3
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates ad copy variations."}, {"role": "user", "content": variations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.8)
                variations = ai_response.text_content if ai_response.success else ""
                
                # Generate performance predictions
                performance_prompt = self._create_performance_prompt(
                    ad_copy, platform, ad_type, target_audience
                )
                messages = [{"role": "system", "content": "You are an AI assistant that predicts ad performance."}, {"role": "user", "content": performance_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                performance_prediction = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ContentPiece(
                    project_id=project.id,
                    title=product_service,
                    content=ad_copy,
                    content_type="ad_copy",
                    platform=platform,
                    word_count=len(ad_copy.split()),
                    character_count=len(ad_copy),
                    reading_time=1,
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.ad_copy_created", {
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "user_id": user_id,
                    "platform": platform,
                    "ad_type": ad_type,
                    "product_service": product_service,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "ad_copy": ad_copy,
                    "variations": self._parse_variations(variations),
                    "performance_prediction": performance_prediction,
                    "platform_optimizations": self._get_platform_optimizations(platform),
                    "copywriting_tips": self._get_copywriting_tips(platform, ad_type),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Ad copy creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_ad_campaign(
        self,
        user_id: int,
        platform: str,
        campaign_name: str,
        product_service: str,
        target_audience: str,
        ad_objective: str,
        budget_range: str,
        campaign_duration: int,
        ad_types: List[str]
    ) -> Dict[str, Any]:
        """Create comprehensive ad campaign with multiple ad types"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project for campaign
                project = ContentProject(
                    user_id=user_id,
                    title=f"Ad Campaign: {campaign_name}",
                    description=f"AI-generated {platform} campaign for {product_service}",
                    content_type="ad_copy",
                    platform=platform,
                    target_audience=target_audience,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate campaign strategy
                strategy_prompt = self._create_campaign_strategy_prompt(
                    campaign_name, platform, product_service, target_audience,
                    ad_objective, budget_range, campaign_duration, ad_types
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates ad campaign strategies."}, {"role": "user", "content": strategy_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                campaign_strategy = ai_response.text_content if ai_response.success else ""
                
                # Generate ads for each type
                campaign_ads = []
                for ad_type in ad_types:
                    ad_prompt = self._create_campaign_ad_prompt(
                        platform, ad_type, product_service, target_audience,
                        ad_objective, budget_range, campaign_strategy
                    )
                    # Use AI Service Manager instead of NLPUtils
                    ai_manager = await get_ai_service_manager()
                    messages = [{"role": "system", "content": "You are an AI assistant that creates compelling ad copy."}, {"role": "user", "content": ad_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.8)
                    ad_copy = ai_response.text_content if ai_response.success else ""
                    
                    # Create content piece for each ad
                    content_piece = ContentPiece(
                        project_id=project.id,
                        title=f"{campaign_name} - {ad_type}",
                        content=ad_copy,
                        content_type="ad_copy",
                        platform=platform,
                        word_count=len(ad_copy.split()),
                        character_count=len(ad_copy),
                        reading_time=1,
                        status="draft",
                        ai_generated=True
                    )
                    session.add(content_piece)
                    await session.flush()
                    
                    campaign_ads.append({
                        "ad_type": ad_type,
                        "content_piece_id": content_piece.id,
                        "ad_copy": ad_copy,
                        "word_count": content_piece.word_count
                    })
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "campaign_strategy": campaign_strategy,
                    "campaign_ads": campaign_ads,
                    "platform": platform,
                    "ad_types": ad_types,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Ad campaign creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_ad_copy(
        self,
        content_piece_id: int,
        optimization_type: str,
        optimization_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize existing ad copy for better performance"""
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
                
                optimized_copy = content_piece.content
                
                if optimization_type == "improve_headlines":
                    optimized_copy = await self._improve_headlines(optimized_copy, optimization_params)
                elif optimization_type == "enhance_persuasion":
                    optimized_copy = await self._enhance_persuasion(optimized_copy, optimization_params)
                elif optimization_type == "optimize_cta":
                    optimized_copy = await self._optimize_cta(optimized_copy, optimization_params)
                elif optimization_type == "a_b_testing":
                    optimized_copy = await self._create_ab_testing_variants(optimized_copy, optimization_params)
                
                # Update content piece
                content_piece.content = optimized_copy
                content_piece.word_count = len(optimized_copy.split())
                content_piece.character_count = len(optimized_copy)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "optimized_copy": optimized_copy,
                    "word_count": content_piece.word_count,
                    "optimization_type": optimization_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Ad copy optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_ad_copy_prompt(
        self, platform: str, ad_type: str, product_service: str, target_audience: str,
        ad_objective: str, budget_range: str, call_to_action: str, tone: str
    ) -> str:
        """Create prompt for ad copy generation"""
        platform_guidelines = self._get_platform_guidelines(platform)
        
        return f"""
        Create compelling {ad_type} ad copy for {platform}:
        
        Product/Service: {product_service}
        Target Audience: {target_audience}
        Ad Objective: {ad_objective}
        Budget Range: {budget_range}
        Call-to-Action: {call_to_action}
        Tone: {tone}
        
        Platform Guidelines:
        {platform_guidelines}
        
        Requirements:
        - Create persuasive, conversion-focused copy
        - Include compelling headline and description
        - Use emotional triggers and benefits
        - Optimize for {platform} best practices
        - Include clear call-to-action
        - Match {tone} tone throughout
        
        Generate the complete ad copy with headline, description, and call-to-action.
        """
    
    def _create_variations_prompt(
        self, original_copy: str, platform: str, ad_type: str, variation_count: int
    ) -> str:
        """Create prompt for ad copy variations"""
        return f"""
        Create {variation_count} variations of this {platform} {ad_type} ad:
        
        Original Ad Copy:
        {original_copy}
        
        Requirements:
        - Maintain the same message and objective
        - Use different emotional appeals and language
        - Test different headline approaches
        - Vary the call-to-action style
        - Keep platform optimization in mind
        
        Generate {variation_count} distinct variations that can be A/B tested.
        """
    
    def _create_performance_prompt(
        self, ad_copy: str, platform: str, ad_type: str, target_audience: str
    ) -> str:
        """Create prompt for performance prediction"""
        return f"""
        Predict the performance of this {platform} {ad_type} ad:
        
        Ad Copy:
        {ad_copy}
        
        Platform: {platform}
        Ad Type: {ad_type}
        Target Audience: {target_audience}
        
        Provide:
        1. Expected click-through rate (CTR)
        2. Conversion rate predictions
        3. Cost-per-click estimates
        4. Performance factors and risks
        5. Optimization recommendations
        
        Format as a comprehensive performance analysis.
        """
    
    def _create_campaign_strategy_prompt(
        self, campaign_name: str, platform: str, product_service: str, target_audience: str,
        ad_objective: str, budget_range: str, campaign_duration: int, ad_types: List[str]
    ) -> str:
        """Create prompt for campaign strategy generation"""
        return f"""
        Create a comprehensive ad campaign strategy:
        
        Campaign Name: {campaign_name}
        Platform: {platform}
        Product/Service: {product_service}
        Target Audience: {target_audience}
        Ad Objective: {ad_objective}
        Budget Range: {budget_range}
        Campaign Duration: {campaign_duration} days
        Ad Types: {', '.join(ad_types)}
        
        Include:
        1. Campaign overview and goals
        2. Target audience segmentation
        3. Ad type strategy for each type
        4. Budget allocation recommendations
        5. Timeline and scheduling
        6. Performance metrics and KPIs
        7. Testing and optimization plan
        
        Format as a comprehensive campaign strategy document.
        """
    
    def _create_campaign_ad_prompt(
        self, platform: str, ad_type: str, product_service: str, target_audience: str,
        ad_objective: str, budget_range: str, campaign_strategy: str
    ) -> str:
        """Create prompt for campaign ad generation"""
        return f"""
        Create {ad_type} ad copy for this campaign:
        
        Platform: {platform}
        Ad Type: {ad_type}
        Product/Service: {product_service}
        Target Audience: {target_audience}
        Ad Objective: {ad_objective}
        Budget Range: {budget_range}
        
        Campaign Strategy:
        {campaign_strategy}
        
        Requirements:
        - Align with overall campaign strategy
        - Optimize for {ad_type} format
        - Maintain campaign consistency
        - Include compelling call-to-action
        - Follow {platform} best practices
        
        Generate the complete {ad_type} ad copy.
        """
    
    async def _improve_headlines(self, ad_copy: str, params: Dict[str, Any]) -> str:
        """Improve ad headlines for better performance"""
        headline_prompt = f"""
        Improve the headlines in this ad copy:
        
        {ad_copy}
        
        Improvement focus: {params.get('focus', 'engagement')}
        Headline style: {params.get('style', 'benefit-focused')}
        
        Create more compelling, click-worthy headlines that drive action.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that improves ad headlines."}, {"role": "user", "content": headline_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.8)
        improved_copy = ai_response.text_content if ai_response.success else copy
        return improved_copy
    
    async def _enhance_persuasion(self, ad_copy: str, params: Dict[str, Any]) -> str:
        """Enhance persuasive elements in ad copy"""
        persuasion_prompt = f"""
        Enhance the persuasive elements in this ad copy:
        
        {ad_copy}
        
        Persuasion technique: {params.get('technique', 'benefit-focused')}
        Emotional appeal: {params.get('emotion', 'desire')}
        
        Strengthen the persuasive elements and emotional triggers.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that enhances persuasive elements in ad copy."}, {"role": "user", "content": persuasion_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.8)
        enhanced_copy = ai_response.text_content if ai_response.success else copy
        return enhanced_copy
    
    async def _optimize_cta(self, ad_copy: str, params: Dict[str, Any]) -> str:
        """Optimize call-to-action in ad copy"""
        cta_prompt = f"""
        Optimize the call-to-action in this ad copy:
        
        {ad_copy}
        
        CTA style: {params.get('cta_style', 'action-oriented')}
        Urgency level: {params.get('urgency', 'moderate')}
        
        Create a more compelling and action-driving call-to-action.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes call-to-action elements."}, {"role": "user", "content": cta_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.8)
        optimized_copy = ai_response.text_content if ai_response.success else copy
        return optimized_copy
    
    async def _create_ab_testing_variants(self, ad_copy: str, params: Dict[str, Any]) -> str:
        """Create A/B testing variants for ad copy"""
        ab_prompt = f"""
        Create A/B testing variants for this ad copy:
        
        {ad_copy}
        
        Number of variants: {params.get('variant_count', 3)}
        Testing focus: {params.get('testing_focus', 'headlines')}
        
        Generate distinct variants that can be tested for performance.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates A/B test variants for ad copy."}, {"role": "user", "content": ab_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.8)
        ab_variants = ai_response.text_content if ai_response.success else ""
        return ab_variants
    
    def _get_platform_guidelines(self, platform: str) -> str:
        """Get platform-specific ad copy guidelines"""
        guidelines = {
            "google_ads": """
            - Headlines: 30 characters max, include keywords
            - Descriptions: 90 characters max, compelling benefits
            - Use ad extensions for additional information
            - Include relevant keywords naturally
            - Clear call-to-action in description
            """,
            "facebook_ads": """
            - Primary text: 125 characters for optimal display
            - Headlines: 40 characters max, engaging
            - Use emotional language and storytelling
            - Include social proof and urgency
            - Clear value proposition
            """,
            "instagram_ads": """
            - Caption: 125 characters for preview
            - Use hashtags strategically (5-15)
            - Visual-first approach
            - Include call-to-action
            - Use Instagram-specific language
            """,
            "linkedin_ads": """
            - Professional tone and language
            - Focus on business benefits
            - Include industry-specific terms
            - Clear professional call-to-action
            - Use LinkedIn ad formats effectively
            """,
            "twitter_ads": """
            - Character limit: 280 characters
            - Use trending hashtags strategically
            - Include call-to-action
            - Use Twitter-specific features
            - Keep it concise and engaging
            """
        }
        
        return guidelines.get(platform.lower(), "Follow general ad copy best practices.")
    
    def _get_platform_optimizations(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific optimization tips"""
        optimizations = {
            "google_ads": {
                "headline_optimization": "Include primary keyword in first headline",
                "description_tips": "Use benefits and features in descriptions",
                "ad_extensions": "Utilize sitelink, callout, and structured snippets",
                "keyword_optimization": "Match ad copy with keyword themes"
            },
            "facebook_ads": {
                "text_optimization": "Keep primary text under 125 characters",
                "headline_tips": "Use emotional triggers and questions",
                "visual_optimization": "Ensure text overlay is minimal",
                "audience_targeting": "Align copy with audience interests"
            },
            "instagram_ads": {
                "caption_optimization": "Hook in first line, CTA in last",
                "hashtag_strategy": "Use 5-15 relevant hashtags",
                "visual_copy": "Ensure copy complements visual content",
                "engagement_focus": "Encourage comments and shares"
            },
            "linkedin_ads": {
                "professional_tone": "Use industry-specific terminology",
                "business_focus": "Emphasize ROI and business outcomes",
                "credibility": "Include social proof and statistics",
                "networking": "Encourage professional connections"
            },
            "twitter_ads": {
                "character_optimization": "Use all available characters effectively",
                "hashtag_usage": "Include 1-3 relevant hashtags",
                "engagement": "Encourage retweets and replies",
                "trending": "Leverage trending topics when relevant"
            }
        }
        
        return optimizations.get(platform.lower(), {})
    
    def _get_copywriting_tips(self, platform: str, ad_type: str) -> List[str]:
        """Get platform and ad type specific copywriting tips"""
        tips = {
            "google_ads": [
                "Use exact match keywords in headlines",
                "Include benefits in descriptions",
                "Use ad extensions for additional information",
                "Test different headline combinations"
            ],
            "facebook_ads": [
                "Tell a story in primary text",
                "Use emotional language",
                "Include social proof",
                "Test different image-text combinations"
            ],
            "instagram_ads": [
                "Use visual-first approach",
                "Include relevant hashtags",
                "Keep captions engaging",
                "Use Instagram-specific language"
            ],
            "linkedin_ads": [
                "Use professional tone",
                "Focus on business outcomes",
                "Include industry terminology",
                "Emphasize credibility and expertise"
            ],
            "twitter_ads": [
                "Keep it concise and engaging",
                "Use trending hashtags strategically",
                "Include clear call-to-action",
                "Encourage engagement and sharing"
            ]
        }
        
        platform_tips = tips.get(platform.lower(), [])
        
        # Add ad type specific tips
        ad_type_tips = {
            "search": ["Focus on user intent", "Include relevant keywords", "Clear value proposition"],
            "display": ["Visual appeal", "Brand awareness", "Engaging storytelling"],
            "social": ["Community building", "Emotional connection", "Shareable content"],
            "video": ["Hook in first 3 seconds", "Clear message", "Strong call-to-action"]
        }
        
        ad_type_specific = ad_type_tips.get(ad_type.lower(), [])
        
        return platform_tips + ad_type_specific
    
    def _parse_variations(self, variations_content: str) -> List[str]:
        """Parse ad copy variations from generated content"""
        lines = variations_content.split('\n')
        variations = []
        current_variation = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Variation') or line.startswith('Version'):
                if current_variation:
                    variations.append(current_variation.strip())
                current_variation = line + "\n"
            elif line:
                current_variation += line + "\n"
        
        if current_variation:
            variations.append(current_variation.strip())
        
        return variations[:5]  # Limit to 5 variations
