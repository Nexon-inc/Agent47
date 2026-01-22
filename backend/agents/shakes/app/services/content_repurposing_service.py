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

class ContentRepurposingService:
    """Service for AI-powered content repurposing across different formats and platforms"""
    
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
        """Initialize content repurposing service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content repurposing service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content repurposing service: {e}")
            raise
    
    async def repurpose_content(
        self,
        user_id: int,
        source_content_id: int,
        target_format: str,
        target_platform: str,
        repurposing_goals: List[str],
        target_audience: str,
        tone_adjustment: str = "maintain"
    ) -> Dict[str, Any]:
        """Repurpose existing content into new format and platform"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                source_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == source_content_id)
                )
                source_content = source_result.scalar_one_or_none()
                
                if not source_content:
                    return {"success": False, "error": "Source content not found"}
                
                project_result = await session.execute(
                    select(ShakesContentProject).where(ShakesContentProject.id == source_content.project_id)
                )
                source_project = project_result.scalar_one_or_none()
                
                if not source_project:
                    return {"success": False, "error": "Source project not found"}
                
                repurpose_project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Repurposed: {source_content.title}",
                    description=f"Repurposed from {source_content.content_type} to {target_format} for {target_platform}",
                    content_type="repurposed_content",
                    target_audience=target_audience,
                    tone=source_project.tone,
                    status="draft"
                )
                session.add(repurpose_project)
                await session.flush()
                
                repurpose_prompt = self._create_repurpose_prompt(
                    source_content.content, source_content.content_type, target_format,
                    target_platform, repurposing_goals, target_audience, tone_adjustment
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that repurposes content for different platforms."}, {"role": "user", "content": repurpose_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                repurposed_content = ai_response.text_content if ai_response.success else ""
                
                optimization_prompt = self._create_optimization_prompt(
                    repurposed_content, target_format, target_platform, target_audience
                )
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes repurposed content."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                platform_optimizations = ai_response.text_content if ai_response.success else ""
                
                repurposed_piece = ShakesContentPiece(
                    project_id=repurpose_project.id,
                    title=f"{source_content.title} - {target_format}",
                    content=repurposed_content,
                    content_type=target_format,
                    platform=target_platform,
                    word_count=len(repurposed_content.split()),
                    character_count=len(repurposed_content),
                    reading_time=self._calculate_reading_time(repurposed_content),
                    status="draft",
                    ai_generated=True
                )
                session.add(repurposed_piece)
                await session.flush()
                
                await session.commit()
                
                await self.event_bus.publish("shakes.content_repurposed", {
                    "project_id": repurpose_project.id,
                    "content_piece_id": repurposed_piece.id,
                    "source_content_id": source_content_id,
                    "user_id": user_id,
                    "target_format": target_format,
                    "target_platform": target_platform,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": repurpose_project.id,
                    "content_piece_id": repurposed_piece.id,
                    "source_content_id": source_content_id,
                    "repurposed_content": repurposed_content,
                    "platform_optimizations": platform_optimizations,
                    "target_format": target_format,
                    "target_platform": target_platform,
                    "word_count": repurposed_piece.word_count,
                    "reading_time": repurposed_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content repurposing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_repurpose_prompt(
        self, source_content: str, source_type: str, target_format: str,
        target_platform: str, repurposing_goals: List[str], target_audience: str, tone_adjustment: str
    ) -> str:
        """Create prompt for content repurposing"""
        return f"""
        Repurpose this content from {source_type} to {target_format} for {target_platform}:
        
        Source Content:
        {source_content}
        
        Target Format: {target_format}
        Target Platform: {target_platform}
        Repurposing Goals: {', '.join(repurposing_goals)}
        Target Audience: {target_audience}
        Tone Adjustment: {tone_adjustment}
        
        Requirements:
        - Maintain core message and value
        - Adapt to {target_format} format requirements
        - Optimize for {target_platform} best practices
        - Adjust tone if needed for {tone_adjustment}
        - Ensure content fits target audience
        
        Generate the complete repurposed content.
        """
    
    def _create_optimization_prompt(
        self, content: str, target_format: str, target_platform: str, target_audience: str
    ) -> str:
        """Create prompt for platform-specific optimization"""
        return f"""
        Optimize this {target_format} content for {target_platform}:
        
        Content:
        {content}
        
        Target Platform: {target_platform}
        Target Audience: {target_audience}
        
        Provide:
        1. Platform-specific optimization tips
        2. Format adjustments needed
        3. Engagement strategies
        4. Best practices for {target_platform}
        5. Content enhancement recommendations
        
        Format as comprehensive optimization guide.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
