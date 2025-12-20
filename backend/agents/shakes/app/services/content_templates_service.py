import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, ContentTemplate

logger = logging.getLogger(__name__)

class ContentTemplatesService:
    """Service for content template creation and management"""
    
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
        """Initialize content templates service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content templates service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content templates service: {e}")
            raise
    
    async def create_template(
        self,
        user_id: int,
        template_name: str,
        template_type: str,
        template_category: str,
        template_description: str,
        template_structure: Dict[str, Any],
        target_audience: str,
        industry: str,
        use_cases: List[str]
    ) -> Dict[str, Any]:
        """Create new content template"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Generate template content
                template_prompt = self._create_template_generation_prompt(
                    template_name, template_type, template_category, template_description,
                    template_structure, target_audience, industry, use_cases
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates content templates."}, {"role": "user", "content": template_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                template_content = ai_response.text_content if ai_response.success else ""
                
                # Generate usage instructions
                instructions_prompt = self._create_usage_instructions_prompt(
                    template_name, template_type, template_content, use_cases
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates template usage instructions."}, {"role": "user", "content": instructions_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
                usage_instructions = ai_response.text_content if ai_response.success else ""
                
                # Create template record
                content_template = ContentTemplate(
                    user_id=user_id,
                    template_name=template_name,
                    template_type=template_type,
                    template_category=template_category,
                    template_description=template_description,
                    template_content=template_content,
                    template_structure=template_structure,
                    target_audience=target_audience,
                    industry=industry,
                    use_cases=use_cases,
                    usage_instructions=usage_instructions,
                    is_active=True
                )
                session.add(content_template)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.template_created", {
                    "template_id": content_template.id,
                    "user_id": user_id,
                    "template_name": template_name,
                    "template_type": template_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "template_id": content_template.id,
                    "template_name": template_name,
                    "template_type": template_type,
                    "template_category": template_category,
                    "template_content": template_content,
                    "template_structure": template_structure,
                    "usage_instructions": usage_instructions,
                    "target_audience": target_audience,
                    "industry": industry,
                    "use_cases": use_cases,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def use_template(
        self,
        template_id: int,
        user_id: int,
        template_variables: Dict[str, Any],
        customization_requests: List[str]
    ) -> Dict[str, Any]:
        """Use template to generate content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get template
                template_result = await session.execute(
                    select(ContentTemplate).where(ContentTemplate.id == template_id)
                )
                content_template = template_result.scalar_one_or_none()
                
                if not content_template:
                    return {"success": False, "error": "Template not found"}
                
                # Generate content from template
                content_prompt = self._create_template_content_prompt(
                    content_template, template_variables, customization_requests
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that generates content from templates."}, {"role": "user", "content": content_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                generated_content = ai_response.text_content if ai_response.success else ""
                
                # Create content project
                project = ContentProject(
                    user_id=user_id,
                    title=f"Generated from {content_template.template_name}",
                    description=f"Content generated using {content_template.template_name} template",
                    content_type=content_template.template_type,
                    target_audience=content_template.target_audience,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Create content piece
                content_piece = ContentPiece(
                    project_id=project.id,
                    title=f"{content_template.template_name} - Generated Content",
                    content=generated_content,
                    content_type=content_template.template_type,
                    word_count=len(generated_content.split()),
                    character_count=len(generated_content),
                    reading_time=self._calculate_reading_time(generated_content),
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "template_id": template_id,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "generated_content": generated_content,
                    "template_name": content_template.template_name,
                    "template_type": content_template.template_type,
                    "template_variables": template_variables,
                    "customization_requests": customization_requests,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Template usage failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def customize_template(
        self,
        template_id: int,
        customization_requests: List[str],
        new_template_name: str = None
    ) -> Dict[str, Any]:
        """Customize existing template"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get original template
                template_result = await session.execute(
                    select(ContentTemplate).where(ContentTemplate.id == template_id)
                )
                original_template = template_result.scalar_one_or_none()
                
                if not original_template:
                    return {"success": False, "error": "Template not found"}
                
                # Generate customized template
                customization_prompt = self._create_template_customization_prompt(
                    original_template, customization_requests
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that customizes content templates."}, {"role": "user", "content": customization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                customized_content = ai_response.text_content if ai_response.success else ""
                
                # Create new customized template
                customized_template = ContentTemplate(
                    user_id=original_template.user_id,
                    template_name=new_template_name or f"{original_template.template_name} - Customized",
                    template_type=original_template.template_type,
                    template_category=original_template.template_category,
                    template_description=f"Customized version of {original_template.template_name}",
                    template_content=customized_content,
                    template_structure=original_template.template_structure,
                    target_audience=original_template.target_audience,
                    industry=original_template.industry,
                    use_cases=original_template.use_cases,
                    usage_instructions=original_template.usage_instructions,
                    is_active=True,
                    parent_template_id=template_id
                )
                session.add(customized_template)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "original_template_id": template_id,
                    "customized_template_id": customized_template.id,
                    "customized_template_name": customized_template.template_name,
                    "customized_content": customized_content,
                    "customization_requests": customization_requests,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Template customization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_templates_by_category(
        self,
        category: str,
        template_type: str = None,
        industry: str = None
    ) -> Dict[str, Any]:
        """Get templates by category and filters"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Build query
                query = select(ContentTemplate).where(
                    ContentTemplate.template_category == category,
                    ContentTemplate.is_active == True
                )
                
                if template_type:
                    query = query.where(ContentTemplate.template_type == template_type)
                
                if industry:
                    query = query.where(ContentTemplate.industry == industry)
                
                # Execute query
                templates_result = await session.execute(query)
                templates = templates_result.scalars().all()
                
                # Format results
                template_list = []
                for template in templates:
                    template_list.append({
                        "template_id": template.id,
                        "template_name": template.template_name,
                        "template_type": template.template_type,
                        "template_category": template.template_category,
                        "template_description": template.template_description,
                        "target_audience": template.target_audience,
                        "industry": template.industry,
                        "use_cases": template.use_cases,
                        "created_at": template.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "category": category,
                    "template_type": template_type,
                    "industry": industry,
                    "templates": template_list,
                    "total_templates": len(template_list),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Template retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_template_generation_prompt(
        self, template_name: str, template_type: str, template_category: str,
        template_description: str, template_structure: Dict[str, Any],
        target_audience: str, industry: str, use_cases: List[str]
    ) -> str:
        """Create prompt for template generation"""
        return f"""
        Create a {template_type} template for {template_name}:
        
        Template Category: {template_category}
        Template Description: {template_description}
        Template Structure: {template_structure}
        Target Audience: {target_audience}
        Industry: {industry}
        Use Cases: {', '.join(use_cases)}
        
        Requirements:
        1. Create a comprehensive {template_type} template
        2. Include all necessary sections and elements
        3. Provide clear placeholders for customization
        4. Ensure template is industry-appropriate
        5. Make it suitable for target audience
        6. Include best practices and guidelines
        7. Make it easy to customize and use
        
        Generate the complete template with clear structure and placeholders.
        """
    
    def _create_usage_instructions_prompt(
        self, template_name: str, template_type: str, template_content: str, use_cases: List[str]
    ) -> str:
        """Create prompt for usage instructions"""
        return f"""
        Create usage instructions for the {template_name} {template_type} template:
        
        Template Content:
        {template_content}
        
        Use Cases: {', '.join(use_cases)}
        
        Include:
        1. Step-by-step usage guide
        2. Placeholder explanations
        3. Customization tips
        4. Best practices
        5. Common mistakes to avoid
        6. Examples of effective usage
        7. Troubleshooting guide
        
        Format as comprehensive usage instructions.
        """
    
    def _create_template_content_prompt(
        self, content_template: ContentTemplate, template_variables: Dict[str, Any], customization_requests: List[str]
    ) -> str:
        """Create prompt for template content generation"""
        return f"""
        Generate content using the {content_template.template_name} template:
        
        Template Content:
        {content_template.template_content}
        
        Template Variables: {template_variables}
        Customization Requests: {', '.join(customization_requests)}
        
        Template Type: {content_template.template_type}
        Target Audience: {content_template.target_audience}
        Industry: {content_template.industry}
        
        Requirements:
        1. Fill in all template placeholders with provided variables
        2. Apply customization requests
        3. Maintain template structure and format
        4. Ensure content is appropriate for target audience
        5. Keep industry context in mind
        6. Make content engaging and professional
        
        Generate the complete customized content.
        """
    
    def _create_template_customization_prompt(
        self, original_template: ContentTemplate, customization_requests: List[str]
    ) -> str:
        """Create prompt for template customization"""
        return f"""
        Customize the {original_template.template_name} template:
        
        Original Template:
        {original_template.template_content}
        
        Customization Requests: {', '.join(customization_requests)}
        
        Template Type: {original_template.template_type}
        Target Audience: {original_template.target_audience}
        Industry: {original_template.industry}
        
        Requirements:
        1. Apply all customization requests
        2. Maintain template structure and usability
        3. Preserve original template quality
        4. Ensure customization enhances the template
        5. Keep it appropriate for target audience
        6. Maintain industry relevance
        
        Generate the customized template.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
