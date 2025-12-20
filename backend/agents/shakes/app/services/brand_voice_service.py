import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, BrandVoice

logger = logging.getLogger(__name__)

class BrandVoiceService:
    """Service for brand voice customization and consistency"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.6
        }
    
    async def initialize(self):
        """Initialize brand voice service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Brand voice service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize brand voice service: {e}")
            raise
    
    async def create_brand_voice(
        self,
        user_id: int,
        brand_name: str,
        brand_description: str,
        target_audience: str,
        brand_values: List[str],
        tone_characteristics: List[str],
        sample_content: List[str],
        industry: str
    ) -> Dict[str, Any]:
        """Create and define brand voice profile"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Generate brand voice analysis
                voice_analysis_prompt = self._create_brand_voice_analysis_prompt(
                    brand_name, brand_description, target_audience, brand_values,
                    tone_characteristics, sample_content, industry
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes brand voice."}, {"role": "user", "content": voice_analysis_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
                voice_analysis = ai_response.text_content if ai_response.success else ""
                
                # Generate voice guidelines
                guidelines_prompt = self._create_voice_guidelines_prompt(
                    brand_name, voice_analysis, target_audience, brand_values, tone_characteristics
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates brand voice guidelines."}, {"role": "user", "content": guidelines_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
                voice_guidelines = ai_response.text_content if ai_response.success else ""
                
                # Create brand voice record
                brand_voice = BrandVoice(
                    user_id=user_id,
                    brand_name=brand_name,
                    brand_description=brand_description,
                    target_audience=target_audience,
                    brand_values=brand_values,
                    tone_characteristics=tone_characteristics,
                    voice_analysis=voice_analysis,
                    voice_guidelines=voice_guidelines,
                    industry=industry,
                    is_active=True
                )
                session.add(brand_voice)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.brand_voice_created", {
                    "brand_voice_id": brand_voice.id,
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "brand_voice_id": brand_voice.id,
                    "brand_name": brand_name,
                    "voice_analysis": voice_analysis,
                    "voice_guidelines": voice_guidelines,
                    "brand_values": brand_values,
                    "tone_characteristics": tone_characteristics,
                    "target_audience": target_audience,
                    "industry": industry,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Brand voice creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def apply_brand_voice(
        self,
        content_piece_id: int,
        brand_voice_id: int,
        application_intensity: str = "moderate"
    ) -> Dict[str, Any]:
        """Apply brand voice to existing content"""
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
                
                # Get brand voice
                brand_voice_result = await session.execute(
                    select(BrandVoice).where(BrandVoice.id == brand_voice_id)
                )
                brand_voice = brand_voice_result.scalar_one_or_none()
                
                if not brand_voice:
                    return {"success": False, "error": "Brand voice not found"}
                
                # Apply brand voice
                application_prompt = self._create_brand_voice_application_prompt(
                    content_piece.content, content_piece.content_type, brand_voice,
                    application_intensity
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that applies brand voice to content."}, {"role": "user", "content": application_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.6)
                branded_content = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                original_content = content_piece.content
                content_piece.content = branded_content
                content_piece.word_count = len(branded_content.split())
                content_piece.character_count = len(branded_content)
                content_piece.reading_time = self._calculate_reading_time(branded_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "brand_voice_id": brand_voice_id,
                    "original_content": original_content,
                    "branded_content": branded_content,
                    "application_intensity": application_intensity,
                    "brand_name": brand_voice.brand_name,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Brand voice application failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_brand_consistency(
        self,
        content_piece_id: int,
        brand_voice_id: int
    ) -> Dict[str, Any]:
        """Analyze content for brand voice consistency"""
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
                
                # Get brand voice
                brand_voice_result = await session.execute(
                    select(BrandVoice).where(BrandVoice.id == brand_voice_id)
                )
                brand_voice = brand_voice_result.scalar_one_or_none()
                
                if not brand_voice:
                    return {"success": False, "error": "Brand voice not found"}
                
                # Analyze consistency
                consistency_prompt = self._create_consistency_analysis_prompt(
                    content_piece.content, content_piece.content_type, brand_voice
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes brand voice consistency."}, {"role": "user", "content": consistency_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
                consistency_analysis = ai_response.text_content if ai_response.success else ""
                
                # Calculate consistency score
                consistency_score = self._calculate_consistency_score(consistency_analysis)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "brand_voice_id": brand_voice_id,
                    "consistency_score": consistency_score,
                    "consistency_analysis": consistency_analysis,
                    "brand_name": brand_voice.brand_name,
                    "content_type": content_piece.content_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Brand consistency analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_brand_voice(
        self,
        brand_voice_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing brand voice profile"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get brand voice
                brand_voice_result = await session.execute(
                    select(BrandVoice).where(BrandVoice.id == brand_voice_id)
                )
                brand_voice = brand_voice_result.scalar_one_or_none()
                
                if not brand_voice:
                    return {"success": False, "error": "Brand voice not found"}
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(brand_voice, field):
                        setattr(brand_voice, field, value)
                
                # Regenerate analysis if key fields changed
                if any(field in updates for field in ['brand_description', 'target_audience', 'brand_values', 'tone_characteristics']):
                    voice_analysis_prompt = self._create_brand_voice_analysis_prompt(
                        brand_voice.brand_name, brand_voice.brand_description, brand_voice.target_audience,
                        brand_voice.brand_values, brand_voice.tone_characteristics, [], brand_voice.industry
                    )
                    # Use AI Service Manager instead of NLPUtils
                    ai_manager = await get_ai_service_manager()
                    messages = [{"role": "system", "content": "You are an AI assistant that analyzes brand voice."}, {"role": "user", "content": voice_analysis_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
                    brand_voice.voice_analysis = ai_response.text_content if ai_response.success else ""
                    
                    guidelines_prompt = self._create_voice_guidelines_prompt(
                        brand_voice.brand_name, brand_voice.voice_analysis, brand_voice.target_audience,
                        brand_voice.brand_values, brand_voice.tone_characteristics
                    )
                    messages = [{"role": "system", "content": "You are an AI assistant that creates brand voice guidelines."}, {"role": "user", "content": guidelines_prompt}]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
                    brand_voice.voice_guidelines = ai_response.text_content if ai_response.success else ""
                
                brand_voice.updated_at = datetime.utcnow()
                await session.commit()
                
                return {
                    "success": True,
                    "brand_voice_id": brand_voice_id,
                    "updated_fields": list(updates.keys()),
                    "brand_name": brand_voice.brand_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Brand voice update failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_brand_voice_analysis_prompt(
        self, brand_name: str, brand_description: str, target_audience: str,
        brand_values: List[str], tone_characteristics: List[str], sample_content: List[str], industry: str
    ) -> str:
        """Create prompt for brand voice analysis"""
        return f"""
        Analyze and define the brand voice for {brand_name}:
        
        Brand Name: {brand_name}
        Brand Description: {brand_description}
        Target Audience: {target_audience}
        Brand Values: {', '.join(brand_values)}
        Tone Characteristics: {', '.join(tone_characteristics)}
        Industry: {industry}
        Sample Content: {sample_content}
        
        Provide:
        1. Brand personality assessment
        2. Voice characteristics analysis
        3. Tone recommendations
        4. Language style guidelines
        5. Communication preferences
        6. Audience alignment strategies
        7. Industry-specific considerations
        
        Format as comprehensive brand voice analysis.
        """
    
    def _create_voice_guidelines_prompt(
        self, brand_name: str, voice_analysis: str, target_audience: str,
        brand_values: List[str], tone_characteristics: List[str]
    ) -> str:
        """Create prompt for voice guidelines"""
        return f"""
        Create detailed brand voice guidelines for {brand_name}:
        
        Brand Name: {brand_name}
        Voice Analysis: {voice_analysis}
        Target Audience: {target_audience}
        Brand Values: {', '.join(brand_values)}
        Tone Characteristics: {', '.join(tone_characteristics)}
        
        Include:
        1. Voice and tone rules
        2. Language preferences
        3. Communication style guidelines
        4. Do's and don'ts
        5. Audience-specific adaptations
        6. Platform-specific considerations
        7. Content type guidelines
        8. Quality standards
        
        Format as actionable brand voice guidelines.
        """
    
    def _create_brand_voice_application_prompt(
        self, content: str, content_type: str, brand_voice: BrandVoice, application_intensity: str
    ) -> str:
        """Create prompt for brand voice application"""
        return f"""
        Apply {brand_voice.brand_name} brand voice to this {content_type} content:
        
        Content:
        {content}
        
        Brand Voice Guidelines:
        {brand_voice.voice_guidelines}
        
        Brand Values: {', '.join(brand_voice.brand_values)}
        Tone Characteristics: {', '.join(brand_voice.tone_characteristics)}
        Target Audience: {brand_voice.target_audience}
        Application Intensity: {application_intensity}
        
        Requirements:
        - Apply brand voice consistently
        - Maintain {application_intensity} intensity
        - Align with brand values and tone
        - Consider target audience preferences
        - Preserve content structure and message
        - Ensure natural, authentic voice
        
        Generate the brand-consistent content.
        """
    
    def _create_consistency_analysis_prompt(
        self, content: str, content_type: str, brand_voice: BrandVoice
    ) -> str:
        """Create prompt for consistency analysis"""
        return f"""
        Analyze brand voice consistency for {brand_voice.brand_name}:
        
        Content:
        {content}
        
        Content Type: {content_type}
        
        Brand Voice Guidelines:
        {brand_voice.voice_guidelines}
        
        Brand Values: {', '.join(brand_voice.brand_values)}
        Tone Characteristics: {', '.join(brand_voice.tone_characteristics)}
        Target Audience: {brand_voice.target_audience}
        
        Evaluate:
        1. Voice consistency with brand guidelines
        2. Tone alignment with characteristics
        3. Value representation
        4. Audience appropriateness
        5. Language style consistency
        6. Overall brand alignment
        
        Format as comprehensive consistency analysis.
        """
    
    def _calculate_consistency_score(self, consistency_analysis: str) -> float:
        """Calculate brand consistency score"""
        # Simple scoring based on analysis keywords
        positive_indicators = ["consistent", "aligned", "appropriate", "matches", "follows"]
        negative_indicators = ["inconsistent", "misaligned", "inappropriate", "conflicts", "violates"]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in consistency_analysis.lower())
        negative_count = sum(1 for indicator in negative_indicators if indicator in consistency_analysis.lower())
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral score
        
        score = positive_count / (positive_count + negative_count)
        return round(score, 3)
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
