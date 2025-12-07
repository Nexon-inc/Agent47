import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece

logger = logging.getLogger(__name__)

class GrammarRefinementService:
    """Service for AI-powered grammar and tone refinement"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.3
        }
    
    async def initialize(self):
        """Initialize grammar refinement service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Grammar refinement service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize grammar refinement service: {e}")
            raise
    
    async def refine_content(
        self,
        content_piece_id: int,
        refinement_type: str,
        target_tone: str,
        refinement_goals: List[str],
        preserve_style: bool = True
    ) -> Dict[str, Any]:
        """Refine content for grammar, tone, and style"""
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
                
                # Generate refinement
                refinement_prompt = self._create_refinement_prompt(
                    content_piece.content, content_piece.content_type, refinement_type,
                    target_tone, refinement_goals, preserve_style
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that refines grammar and writing style."}, {"role": "user", "content": refinement_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
                refined_content = ai_response.text_content if ai_response.success else ""
                
                # Generate improvement analysis
                analysis_prompt = self._create_improvement_analysis_prompt(
                    content_piece.content, refined_content, refinement_type, target_tone
                )
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes writing improvements."}, {"role": "user", "content": analysis_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                improvement_analysis = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                original_content = content_piece.content
                content_piece.content = refined_content
                content_piece.word_count = len(refined_content.split())
                content_piece.character_count = len(refined_content)
                content_piece.reading_time = self._calculate_reading_time(refined_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.content_refined", {
                    "content_piece_id": content_piece_id,
                    "refinement_type": refinement_type,
                    "target_tone": target_tone,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "original_content": original_content,
                    "refined_content": refined_content,
                    "refinement_type": refinement_type,
                    "target_tone": target_tone,
                    "improvement_analysis": improvement_analysis,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content refinement failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_refine_content(
        self,
        content_piece_ids: List[int],
        refinement_type: str,
        target_tone: str,
        refinement_goals: List[str]
    ) -> Dict[str, Any]:
        """Refine multiple content pieces in batch"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                refined_pieces = []
                
                for content_piece_id in content_piece_ids:
                    # Get content piece
                    content_result = await session.execute(
                        select(ContentPiece).where(ContentPiece.id == content_piece_id)
                    )
                    content_piece = content_result.scalar_one_or_none()
                    
                    if not content_piece:
                        continue
                    
                    # Generate refinement
                    refinement_prompt = self._create_refinement_prompt(
                        content_piece.content, content_piece.content_type, refinement_type,
                        target_tone, refinement_goals, True
                    )
                    # Use AI Service Manager instead of NLPUtils
                    ai_manager = await get_ai_service_manager()
                    messages = [{"role": "system", "content": "You are an AI assistant that refines grammar and writing quality."}, {"role": "user", "content": refinement_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
                    refined_content = ai_response.text_content if ai_response.success else ""
                    
                    # Update content piece
                    content_piece.content = refined_content
                    content_piece.word_count = len(refined_content.split())
                    content_piece.character_count = len(refined_content)
                    content_piece.reading_time = self._calculate_reading_time(refined_content)
                    content_piece.updated_at = datetime.utcnow()
                    
                    refined_pieces.append({
                        "content_piece_id": content_piece_id,
                        "refined_content": refined_content,
                        "word_count": content_piece.word_count,
                        "reading_time": content_piece.reading_time
                    })
                
                await session.commit()
                
                return {
                    "success": True,
                    "refined_pieces": refined_pieces,
                    "total_refined": len(refined_pieces),
                    "refinement_type": refinement_type,
                    "target_tone": target_tone,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Batch content refinement failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_content_quality(
        self,
        content_piece_id: int,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze content quality and provide improvement suggestions"""
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
                
                # Generate quality analysis
                analysis_prompt = self._create_quality_analysis_prompt(
                    content_piece.content, content_piece.content_type, analysis_type
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes writing quality."}, {"role": "user", "content": analysis_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
                quality_analysis = ai_response.text_content if ai_response.success else ""
                
                # Generate improvement suggestions
                suggestions_prompt = self._create_improvement_suggestions_prompt(
                    content_piece.content, content_piece.content_type, quality_analysis
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides writing improvement suggestions."}, {"role": "user", "content": suggestions_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                improvement_suggestions = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "analysis_type": analysis_type,
                    "quality_analysis": quality_analysis,
                    "improvement_suggestions": improvement_suggestions,
                    "content_metrics": {
                        "word_count": content_piece.word_count,
                        "character_count": content_piece.character_count,
                        "reading_time": content_piece.reading_time,
                        "content_type": content_piece.content_type,
                        "platform": content_piece.platform
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content quality analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def adjust_tone(
        self,
        content_piece_id: int,
        current_tone: str,
        target_tone: str,
        tone_intensity: str = "moderate"
    ) -> Dict[str, Any]:
        """Adjust content tone while maintaining message"""
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
                
                # Generate tone adjustment
                tone_prompt = self._create_tone_adjustment_prompt(
                    content_piece.content, content_piece.content_type, current_tone, target_tone, tone_intensity
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that adjusts writing tone and style."}, {"role": "user", "content": tone_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
                adjusted_content = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                content_piece.content = adjusted_content
                content_piece.word_count = len(adjusted_content.split())
                content_piece.character_count = len(adjusted_content)
                content_piece.reading_time = self._calculate_reading_time(adjusted_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "adjusted_content": adjusted_content,
                    "current_tone": current_tone,
                    "target_tone": target_tone,
                    "tone_intensity": tone_intensity,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Tone adjustment failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_refinement_prompt(
        self, content: str, content_type: str, refinement_type: str,
        target_tone: str, refinement_goals: List[str], preserve_style: bool
    ) -> str:
        """Create prompt for content refinement"""
        return f"""
        Refine this {content_type} content with {refinement_type} improvements:
        
        Original Content:
        {content}
        
        Refinement Type: {refinement_type}
        Target Tone: {target_tone}
        Refinement Goals: {', '.join(refinement_goals)}
        Preserve Style: {preserve_style}
        
        Requirements:
        - Apply {refinement_type} improvements
        - Adjust tone to {target_tone}
        - Achieve specified refinement goals
        - Maintain original message and intent
        - Preserve writing style if requested
        - Improve readability and flow
        - Fix grammar and syntax issues
        
        Generate the refined content.
        """
    
    def _create_improvement_analysis_prompt(
        self, original_content: str, refined_content: str, refinement_type: str, target_tone: str
    ) -> str:
        """Create prompt for improvement analysis"""
        return f"""
        Analyze the improvements made to this content:
        
        Original Content:
        {original_content}
        
        Refined Content:
        {refined_content}
        
        Refinement Type: {refinement_type}
        Target Tone: {target_tone}
        
        Provide:
        1. Key improvements made
        2. Grammar and syntax fixes
        3. Tone adjustments
        4. Readability enhancements
        5. Style preservation
        6. Overall quality assessment
        
        Format as comprehensive improvement analysis.
        """
    
    def _create_quality_analysis_prompt(
        self, content: str, content_type: str, analysis_type: str
    ) -> str:
        """Create prompt for content quality analysis"""
        return f"""
        Perform {analysis_type} quality analysis on this {content_type} content:
        
        Content:
        {content}
        
        Analysis Type: {analysis_type}
        
        Evaluate:
        1. Grammar and syntax quality
        2. Clarity and readability
        3. Tone consistency
        4. Structure and flow
        5. Engagement factors
        6. Platform optimization
        7. Target audience alignment
        8. Call-to-action effectiveness
        
        Format as comprehensive quality analysis.
        """
    
    def _create_improvement_suggestions_prompt(
        self, content: str, content_type: str, quality_analysis: str
    ) -> str:
        """Create prompt for improvement suggestions"""
        return f"""
        Provide improvement suggestions based on this quality analysis:
        
        Content:
        {content}
        
        Content Type: {content_type}
        
        Quality Analysis:
        {quality_analysis}
        
        Provide:
        1. Specific improvement recommendations
        2. Grammar and syntax fixes
        3. Tone and style adjustments
        4. Structure improvements
        5. Engagement enhancements
        6. Platform-specific optimizations
        7. Priority ranking of suggestions
        
        Format as actionable improvement suggestions.
        """
    
    def _create_tone_adjustment_prompt(
        self, content: str, content_type: str, current_tone: str, target_tone: str, tone_intensity: str
    ) -> str:
        """Create prompt for tone adjustment"""
        return f"""
        Adjust the tone of this {content_type} content:
        
        Content:
        {content}
        
        Current Tone: {current_tone}
        Target Tone: {target_tone}
        Tone Intensity: {tone_intensity}
        
        Requirements:
        - Change tone from {current_tone} to {target_tone}
        - Apply {tone_intensity} intensity adjustment
        - Maintain original message and intent
        - Preserve content structure
        - Ensure natural flow and readability
        - Keep content authentic and engaging
        
        Generate the tone-adjusted content.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
