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

class EmailWritingService:
    """Service for AI-powered email and newsletter content creation"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 4000,
            "temperature": 0.7
        }
    
    async def initialize(self):
        """Initialize email newsletter service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Email writing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize email writing service: {e}")
            raise
    
    async def create_email_sequence(
        self,
        user_id: int,
        sequence_name: str,
        email_type: str,
        target_audience: str,
        business_goal: str,
        sequence_length: int,
        tone: str,
        industry: str,
        call_to_action: str
    ) -> Dict[str, Any]:
        """Create complete email sequence with multiple emails"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Email Sequence: {sequence_name}",
                    description=f"AI-generated {email_type} email sequence for {business_goal}",
                    content_type="email_sequence",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                strategy_prompt = self._create_sequence_strategy_prompt(
                    sequence_name, email_type, target_audience, business_goal,
                    sequence_length, tone, industry, call_to_action
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates email sequence strategies."}, {"role": "user", "content": strategy_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                sequence_strategy = ai_response.text_content if ai_response.success else ""
                
                email_sequence = []
                for email_number in range(1, sequence_length + 1):
                    email_prompt = self._create_email_prompt(
                        email_number, sequence_length, email_type, target_audience,
                        business_goal, tone, industry, call_to_action, sequence_strategy
                    )
                    messages = [{"role": "system", "content": "You are an AI assistant that writes professional emails."}, {"role": "user", "content": email_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                    email_content = ai_response.text_content if ai_response.success else ""
                    
                    content_piece = ShakesContentPiece(
                        project_id=project.id,
                        title=f"{sequence_name} - Email {email_number}",
                        content=email_content,
                        content_type="email",
                        platform="email",
                        word_count=len(email_content.split()),
                        character_count=len(email_content),
                        reading_time=self._calculate_reading_time(email_content),
                        status="draft",
                        ai_generated=True
                    )
                    session.add(content_piece)
                    await session.flush()
                    
                    email_sequence.append({
                        "email_number": email_number,
                        "content_piece_id": content_piece.id,
                        "subject_line": self._extract_subject_line(email_content),
                        "email_content": email_content,
                        "word_count": content_piece.word_count,
                        "reading_time": content_piece.reading_time
                    })
                
                await session.commit()
                
                await self.event_bus.publish("shakes.email_sequence_created", {
                    "project_id": project.id,
                    "user_id": user_id,
                    "sequence_name": sequence_name,
                    "email_type": email_type,
                    "sequence_length": sequence_length,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "sequence_strategy": sequence_strategy,
                    "email_sequence": email_sequence,
                    "email_type": email_type,
                    "target_audience": target_audience,
                    "business_goal": business_goal,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Email sequence creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_newsletter(
        self,
        user_id: int,
        newsletter_title: str,
        newsletter_type: str,
        target_audience: str,
        industry: str,
        content_sections: List[str],
        tone: str,
        include_analytics: bool = True
    ) -> Dict[str, Any]:
        """Create comprehensive newsletter with multiple sections"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Newsletter: {newsletter_title}",
                    description=f"AI-generated {newsletter_type} newsletter for {industry}",
                    content_type="newsletter",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                structure_prompt = self._create_newsletter_structure_prompt(
                    newsletter_title, newsletter_type, target_audience, industry, content_sections
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates newsletter structures."}, {"role": "user", "content": structure_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                newsletter_structure = ai_response.text_content if ai_response.success else ""
                
                newsletter_content = {}
                for section in content_sections:
                    section_prompt = self._create_section_prompt(
                        section, newsletter_title, newsletter_type, target_audience, industry, tone
                    )
                    messages = [{"role": "system", "content": "You are an AI assistant that writes newsletter sections."}, {"role": "user", "content": section_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.7)
                    section_content = ai_response.text_content if ai_response.success else ""
                    newsletter_content[section] = section_content
                
                complete_newsletter = self._assemble_newsletter(newsletter_title, newsletter_content, newsletter_structure)
                
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=newsletter_title,
                    content=complete_newsletter,
                    content_type="newsletter",
                    platform="email",
                    word_count=len(complete_newsletter.split()),
                    character_count=len(complete_newsletter),
                    reading_time=self._calculate_reading_time(complete_newsletter),
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
                    "newsletter_title": newsletter_title,
                    "newsletter_structure": newsletter_structure,
                    "newsletter_content": newsletter_content,
                    "complete_newsletter": complete_newsletter,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Newsletter creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_sequence_strategy_prompt(
        self, sequence_name: str, email_type: str, target_audience: str, business_goal: str,
        sequence_length: int, tone: str, industry: str, call_to_action: str
    ) -> str:
        """Create prompt for email sequence strategy"""
        return f"""
        Create a comprehensive email sequence strategy:
        
        Sequence Name: {sequence_name}
        Email Type: {email_type}
        Target Audience: {target_audience}
        Business Goal: {business_goal}
        Sequence Length: {sequence_length} emails
        Tone: {tone}
        Industry: {industry}
        Call-to-Action: {call_to_action}
        
        Include:
        1. Overall sequence objective and flow
        2. Email purpose for each step
        3. Content themes and progression
        4. Timing and frequency recommendations
        5. Personalization strategies
        6. Success metrics and KPIs
        7. A/B testing opportunities
        
        Format as a comprehensive email sequence strategy document.
        """
    
    def _create_email_prompt(
        self, email_number: int, sequence_length: int, email_type: str, target_audience: str,
        business_goal: str, tone: str, industry: str, call_to_action: str, sequence_strategy: str
    ) -> str:
        """Create prompt for individual email generation"""
        return f"""
        Create email {email_number} of {sequence_length} for this sequence:
        
        Email Type: {email_type}
        Target Audience: {target_audience}
        Business Goal: {business_goal}
        Tone: {tone}
        Industry: {industry}
        Call-to-Action: {call_to_action}
        
        Sequence Strategy:
        {sequence_strategy}
        
        Requirements:
        - Align with overall sequence strategy
        - Progress the relationship appropriately
        - Maintain consistent tone and branding
        - Include compelling subject line
        - Clear and actionable content
        - Strong call-to-action
        
        Generate the complete email with subject line and body content.
        """
    
    def _create_newsletter_structure_prompt(
        self, newsletter_title: str, newsletter_type: str, target_audience: str, industry: str, content_sections: List[str]
    ) -> str:
        """Create prompt for newsletter structure"""
        return f"""
        Create a newsletter structure for:
        
        Newsletter Title: {newsletter_title}
        Newsletter Type: {newsletter_type}
        Target Audience: {target_audience}
        Industry: {industry}
        Content Sections: {', '.join(content_sections)}
        
        Include:
        1. Newsletter layout and flow
        2. Section purposes and content types
        3. Content hierarchy and organization
        4. Visual elements and formatting
        5. Engagement strategies
        6. Call-to-action placement
        
        Format as a comprehensive newsletter structure guide.
        """
    
    def _create_section_prompt(
        self, section: str, newsletter_title: str, newsletter_type: str, target_audience: str, industry: str, tone: str
    ) -> str:
        """Create prompt for newsletter section content"""
        return f"""
        Create content for the "{section}" section of this newsletter:
        
        Newsletter Title: {newsletter_title}
        Newsletter Type: {newsletter_type}
        Target Audience: {target_audience}
        Industry: {industry}
        Tone: {tone}
        
        Section: {section}
        
        Requirements:
        - Engaging and informative content
        - Appropriate length for section
        - Consistent with newsletter tone
        - Include relevant examples or insights
        - Encourage reader engagement
        
        Generate compelling content for this section.
        """
    
    def _assemble_newsletter(self, title: str, content: Dict[str, str], structure: str) -> str:
        """Assemble complete newsletter from sections"""
        newsletter = f"# {title}\n\n"
        
        for section, section_content in content.items():
            newsletter += f"## {section.title()}\n\n"
            newsletter += f"{section_content}\n\n"
        
        newsletter += f"---\n\n*Newsletter generated by Shakes AI Content Creation*\n"
        return newsletter
    
    def _extract_subject_line(self, email_content: str) -> str:
        """Extract subject line from email content"""
        lines = email_content.split('\n')
        for line in lines:
            if line.strip().startswith('Subject:') or line.strip().startswith('Subject Line:'):
                return line.split(':', 1)[1].strip()
        return "No subject line found"
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
