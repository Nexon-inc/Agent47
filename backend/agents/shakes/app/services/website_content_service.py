import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class WebsiteContentService:
    """Service for AI-powered website and landing page content creation"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize website landing service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Website content service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize website content service: {e}")
            raise
    
    async def create_landing_page(
        self,
        user_id: int,
        page_title: str,
        business_type: str,
        target_audience: str,
        primary_goal: str,
        key_benefits: List[str],
        call_to_action: str,
        tone: str,
        page_type: str = "conversion"
    ) -> Dict[str, Any]:
        """Create complete landing page content with all sections"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Landing Page: {page_title}",
                    description=f"AI-generated {page_type} landing page for {business_type}",
                    content_type="landing_page",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate landing page structure
                structure_prompt = self._create_landing_structure_prompt(
                    page_title, business_type, target_audience, primary_goal, page_type
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates website page structures."}, {"role": "user", "content": structure_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                page_structure = ai_response.text_content if ai_response.success else "{}"
                
                # Generate hero section
                hero_prompt = self._create_hero_prompt(
                    page_title, business_type, target_audience, primary_goal, key_benefits, call_to_action, tone
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates compelling hero sections."}, {"role": "user", "content": hero_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                hero_content = ai_response.text_content if ai_response.success else ""
                
                # Generate feature sections
                features_prompt = self._create_features_prompt(
                    business_type, key_benefits, target_audience, tone
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates feature sections."}, {"role": "user", "content": features_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                features_content = ai_response.text_content if ai_response.success else ""
                
                # Generate social proof section
                social_proof_prompt = self._create_social_proof_prompt(
                    business_type, target_audience, tone
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates social proof sections."}, {"role": "user", "content": social_proof_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
                social_proof_content = ai_response.text_content if ai_response.success else ""
                
                # Generate CTA section
                cta_prompt = self._create_cta_prompt(
                    call_to_action, primary_goal, target_audience, tone
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates call-to-action sections."}, {"role": "user", "content": cta_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
                cta_content = ai_response.text_content if ai_response.success else ""
                
                # Assemble complete page
                complete_page = self._assemble_landing_page(
                    page_title, hero_content, features_content, social_proof_content, cta_content
                )
                
                # Create content piece
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=page_title,
                    content=complete_page,
                    content_type="landing_page",
                    platform="website",
                    word_count=len(complete_page.split()),
                    character_count=len(complete_page),
                    reading_time=self._calculate_reading_time(complete_page),
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.landing_page_created", {
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "user_id": user_id,
                    "page_title": page_title,
                    "page_type": page_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "page_title": page_title,
                    "page_structure": page_structure,
                    "hero_content": hero_content,
                    "features_content": features_content,
                    "social_proof_content": social_proof_content,
                    "cta_content": cta_content,
                    "complete_page": complete_page,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Landing page creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_website_page(
        self,
        user_id: int,
        page_title: str,
        page_type: str,
        business_type: str,
        target_audience: str,
        page_purpose: str,
        content_sections: List[str],
        tone: str,
        seo_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Create website page content with specified sections"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Website Page: {page_title}",
                    description=f"AI-generated {page_type} page for {business_type}",
                    content_type="website_page",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate page structure
                structure_prompt = self._create_website_structure_prompt(
                    page_title, page_type, business_type, target_audience, page_purpose, content_sections
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates website page structures."}, {"role": "user", "content": structure_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                page_structure = ai_response.text_content if ai_response.success else "{}"
                
                # Generate content for each section
                page_content = {}
                for section in content_sections:
                    section_prompt = self._create_website_section_prompt(
                        section, page_title, page_type, business_type, target_audience, page_purpose, tone
                    )
                    messages = [{"role": "system", "content": "You are an AI assistant that creates website content sections."}, {"role": "user", "content": section_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                    section_content = ai_response.text_content if ai_response.success else ""
                    page_content[section] = section_content
                
                # Generate meta description and title
                meta_prompt = self._create_meta_prompt(
                    page_title, page_type, business_type, target_audience, page_purpose, seo_keywords
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates SEO metadata."}, {"role": "user", "content": meta_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
                meta_content = ai_response.text_content if ai_response.success else ""
                
                # Assemble complete page
                complete_page = self._assemble_website_page(
                    page_title, page_content, page_structure, meta_content
                )
                
                # Create content piece
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=page_title,
                    content=complete_page,
                    content_type="website_page",
                    platform="website",
                    word_count=len(complete_page.split()),
                    character_count=len(complete_page),
                    reading_time=self._calculate_reading_time(complete_page),
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "page_title": page_title,
                    "page_structure": page_structure,
                    "page_content": page_content,
                    "meta_content": meta_content,
                    "complete_page": complete_page,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Website page creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_website_structure(
        self,
        user_id: int,
        business_name: str,
        business_type: str,
        target_audience: str,
        business_goals: List[str],
        tone: str,
        industry: str
    ) -> Dict[str, Any]:
        """Create complete website structure and navigation"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Website Structure: {business_name}",
                    description=f"AI-generated website structure for {business_type}",
                    content_type="website_structure",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate website structure
                structure_prompt = self._create_full_website_structure_prompt(
                    business_name, business_type, target_audience, business_goals, tone, industry
                )
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates website structures."}, {"role": "user", "content": structure_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                website_structure = ai_response.text_content if ai_response.success else "{}"
                
                # Generate navigation structure
                navigation_prompt = self._create_navigation_prompt(
                    business_name, business_type, business_goals
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates website navigation structures."}, {"role": "user", "content": navigation_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                navigation_structure = ai_response.text_content if ai_response.success else ""
                
                # Generate content strategy
                strategy_prompt = self._create_content_strategy_prompt(
                    business_name, business_type, target_audience, business_goals, industry
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates content strategies."}, {"role": "user", "content": strategy_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                content_strategy = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=f"Website Structure - {business_name}",
                    content=website_structure,
                    content_type="website_structure",
                    platform="website",
                    word_count=len(website_structure.split()),
                    character_count=len(website_structure),
                    reading_time=self._calculate_reading_time(website_structure),
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "business_name": business_name,
                    "website_structure": website_structure,
                    "navigation_structure": navigation_structure,
                    "content_strategy": content_strategy,
                    "word_count": content_piece.word_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Website structure creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_landing_structure_prompt(
        self, page_title: str, business_type: str, target_audience: str, primary_goal: str, page_type: str
    ) -> str:
        """Create prompt for landing page structure"""
        return f"""
        Create a landing page structure for:
        
        Page Title: {page_title}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Primary Goal: {primary_goal}
        Page Type: {page_type}
        
        Include:
        1. Page layout and flow
        2. Section purposes and content types
        3. Content hierarchy and organization
        4. Visual elements and formatting
        5. Conversion optimization strategies
        6. Call-to-action placement
        
        Format as a comprehensive landing page structure guide.
        """
    
    def _create_hero_prompt(
        self, page_title: str, business_type: str, target_audience: str, primary_goal: str, key_benefits: List[str], call_to_action: str, tone: str
    ) -> str:
        """Create prompt for hero section content"""
        return f"""
        Create a compelling hero section for this landing page:
        
        Page Title: {page_title}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Primary Goal: {primary_goal}
        Key Benefits: {', '.join(key_benefits)}
        Call-to-Action: {call_to_action}
        Tone: {tone}
        
        Requirements:
        - Compelling headline (H1)
        - Clear value proposition
        - Engaging subheadline
        - Primary call-to-action button
        - Hero image description
        - Trust indicators
        
        Generate the complete hero section content.
        """
    
    def _create_features_prompt(
        self, business_type: str, key_benefits: List[str], target_audience: str, tone: str
    ) -> str:
        """Create prompt for features section content"""
        return f"""
        Create a features section for this landing page:
        
        Business Type: {business_type}
        Key Benefits: {', '.join(key_benefits)}
        Target Audience: {target_audience}
        Tone: {tone}
        
        Requirements:
        - Feature highlights with benefits
        - Engaging feature descriptions
        - Visual element suggestions
        - Benefit-focused language
        - Clear value communication
        
        Generate compelling features section content.
        """
    
    def _create_social_proof_prompt(
        self, business_type: str, target_audience: str, tone: str
    ) -> str:
        """Create prompt for social proof section content"""
        return f"""
        Create a social proof section for this landing page:
        
        Business Type: {business_type}
        Target Audience: {target_audience}
        Tone: {tone}
        
        Requirements:
        - Customer testimonials
        - Success metrics
        - Trust badges and certifications
        - Customer logos or case studies
        - Social proof elements
        
        Generate compelling social proof content.
        """
    
    def _create_cta_prompt(
        self, call_to_action: str, primary_goal: str, target_audience: str, tone: str
    ) -> str:
        """Create prompt for call-to-action section content"""
        return f"""
        Create a compelling call-to-action section:
        
        Call-to-Action: {call_to_action}
        Primary Goal: {primary_goal}
        Target Audience: {target_audience}
        Tone: {tone}
        
        Requirements:
        - Strong CTA button text
        - Urgency and scarcity elements
        - Risk reversal (guarantees)
        - Multiple CTA options
        - Form or contact information
        
        Generate a conversion-focused CTA section.
        """
    
    def _create_website_structure_prompt(
        self, page_title: str, page_type: str, business_type: str, target_audience: str, page_purpose: str, content_sections: List[str]
    ) -> str:
        """Create prompt for website page structure"""
        return f"""
        Create a website page structure for:
        
        Page Title: {page_title}
        Page Type: {page_type}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Page Purpose: {page_purpose}
        Content Sections: {', '.join(content_sections)}
        
        Include:
        1. Page layout and flow
        2. Section purposes and content types
        3. Content hierarchy and organization
        4. Navigation elements
        5. Internal linking strategy
        
        Format as a comprehensive page structure guide.
        """
    
    def _create_website_section_prompt(
        self, section: str, page_title: str, page_type: str, business_type: str, target_audience: str, page_purpose: str, tone: str
    ) -> str:
        """Create prompt for website section content"""
        return f"""
        Create content for the "{section}" section of this website page:
        
        Page Title: {page_title}
        Page Type: {page_type}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Page Purpose: {page_purpose}
        Tone: {tone}
        
        Section: {section}
        
        Requirements:
        - Engaging and informative content
        - Appropriate length for section
        - Consistent with page tone
        - Include relevant examples or insights
        - Encourage user engagement
        
        Generate compelling content for this section.
        """
    
    def _create_meta_prompt(
        self, page_title: str, page_type: str, business_type: str, target_audience: str, page_purpose: str, seo_keywords: List[str]
    ) -> str:
        """Create prompt for meta description and title"""
        keywords = ', '.join(seo_keywords) if seo_keywords else "relevant keywords"
        
        return f"""
        Create SEO meta content for this website page:
        
        Page Title: {page_title}
        Page Type: {page_type}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Page Purpose: {page_purpose}
        SEO Keywords: {keywords}
        
        Requirements:
        - Meta title (50-60 characters)
        - Meta description (150-160 characters)
        - Include primary keywords
        - Compelling and clickable
        - Clear value proposition
        
        Generate optimized meta title and description.
        """
    
    def _create_full_website_structure_prompt(
        self, business_name: str, business_type: str, target_audience: str, business_goals: List[str], tone: str, industry: str
    ) -> str:
        """Create prompt for full website structure"""
        return f"""
        Create a complete website structure for:
        
        Business Name: {business_name}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Business Goals: {', '.join(business_goals)}
        Tone: {tone}
        Industry: {industry}
        
        Include:
        1. Complete site map
        2. Page hierarchy and organization
        3. Navigation structure
        4. Content strategy for each page
        5. User journey mapping
        6. Conversion funnel design
        
        Format as a comprehensive website structure document.
        """
    
    def _create_navigation_prompt(
        self, business_name: str, business_type: str, business_goals: List[str]
    ) -> str:
        """Create prompt for navigation structure"""
        return f"""
        Create a navigation structure for this website:
        
        Business Name: {business_name}
        Business Type: {business_type}
        Business Goals: {', '.join(business_goals)}
        
        Include:
        1. Main navigation menu
        2. Footer navigation
        3. Breadcrumb structure
        4. Mobile navigation
        5. User experience flow
        
        Generate a user-friendly navigation structure.
        """
    
    def _create_content_strategy_prompt(
        self, business_name: str, business_type: str, target_audience: str, business_goals: List[str], industry: str
    ) -> str:
        """Create prompt for content strategy"""
        return f"""
        Create a content strategy for this website:
        
        Business Name: {business_name}
        Business Type: {business_type}
        Target Audience: {target_audience}
        Business Goals: {', '.join(business_goals)}
        Industry: {industry}
        
        Include:
        1. Content themes and topics
        2. Content calendar recommendations
        3. Content types and formats
        4. SEO content strategy
        5. Content distribution plan
        
        Generate a comprehensive content strategy.
        """
    
    def _assemble_landing_page(
        self, page_title: str, hero_content: str, features_content: str, social_proof_content: str, cta_content: str
    ) -> str:
        """Assemble complete landing page from sections"""
        page = f"# {page_title}\n\n"
        page += "## Hero Section\n\n"
        page += f"{hero_content}\n\n"
        page += "## Features & Benefits\n\n"
        page += f"{features_content}\n\n"
        page += "## Social Proof\n\n"
        page += f"{social_proof_content}\n\n"
        page += "## Call-to-Action\n\n"
        page += f"{cta_content}\n\n"
        page += "---\n\n*Landing page generated by Shakes AI Content Creation*\n"
        return page
    
    def _assemble_website_page(
        self, page_title: str, page_content: Dict[str, str], page_structure: str, meta_content: str
    ) -> str:
        """Assemble complete website page from sections"""
        page = f"# {page_title}\n\n"
        page += "## Meta Information\n\n"
        page += f"{meta_content}\n\n"
        page += "## Page Structure\n\n"
        page += f"{page_structure}\n\n"
        
        for section, content in page_content.items():
            page += f"## {section.title()}\n\n"
            page += f"{content}\n\n"
        
        page += "---\n\n*Website page generated by Shakes AI Content Creation*\n"
        return page
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
