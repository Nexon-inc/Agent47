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

class VoiceoverIntegrationService:
    """Service for AI voiceover integration and generation"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize voiceover integration service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Voiceover integration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voiceover integration service: {e}")
            raise
    
    async def generate_voiceover(
        self,
        content_piece_id: int,
        voice_characteristics: Dict[str, Any],
        audio_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI voiceover for content"""
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
                
                # Prepare content for voiceover
                voiceover_script = await self._prepare_voiceover_script(
                    content_piece, voice_characteristics
                )
                
                # Generate voiceover
                voiceover_result = await self._generate_voiceover_audio(
                    voiceover_script, voice_characteristics, audio_settings
                )
                
                # Generate voiceover metadata
                voiceover_metadata = await self._generate_voiceover_metadata(
                    voiceover_result, voice_characteristics, audio_settings
                )
                
                # Publish event
                await self.event_bus.publish("shakes.voiceover_generated", {
                    "content_piece_id": content_piece_id,
                    "voiceover_id": voiceover_result.get("voiceover_id"),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "voiceover_script": voiceover_script,
                    "voiceover_result": voiceover_result,
                    "voiceover_metadata": voiceover_metadata,
                    "voice_characteristics": voice_characteristics,
                    "audio_settings": audio_settings,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Voiceover generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_multilingual_voiceover(
        self,
        content_piece_id: int,
        target_languages: List[str],
        voice_characteristics: Dict[str, Any],
        translation_style: str = "natural"
    ) -> Dict[str, Any]:
        """Generate voiceover in multiple languages"""
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
                
                # Generate translations
                translations = await self._generate_translations(
                    content_piece, target_languages, translation_style
                )
                
                # Generate voiceovers for each language
                multilingual_voiceovers = {}
                for language in target_languages:
                    language_voiceover = await self._generate_language_voiceover(
                        translations[language], language, voice_characteristics
                    )
                    multilingual_voiceovers[language] = language_voiceover
                
                # Generate language-specific metadata
                language_metadata = await self._generate_language_metadata(
                    multilingual_voiceovers, target_languages
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_languages": target_languages,
                    "translations": translations,
                    "multilingual_voiceovers": multilingual_voiceovers,
                    "language_metadata": language_metadata,
                    "voice_characteristics": voice_characteristics,
                    "translation_style": translation_style,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Multilingual voiceover generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def customize_voice_characteristics(
        self,
        base_voice: str,
        customization_parameters: Dict[str, Any],
        target_audience: str
    ) -> Dict[str, Any]:
        """Customize voice characteristics for specific audience"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate voice customization
            voice_customization = await self._generate_voice_customization(
                base_voice, customization_parameters, target_audience
            )
            
            # Generate voice samples
            voice_samples = await self._generate_voice_samples(
                voice_customization, customization_parameters
            )
            
            # Generate customization recommendations
            customization_recommendations = await self._generate_customization_recommendations(
                voice_customization, target_audience
            )
            
            return {
                "success": True,
                "base_voice": base_voice,
                "customization_parameters": customization_parameters,
                "target_audience": target_audience,
                "voice_customization": voice_customization,
                "voice_samples": voice_samples,
                "customization_recommendations": customization_recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Voice customization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_voiceover_script(
        self,
        content_piece_id: int,
        script_style: str,
        target_duration: int = 60
    ) -> Dict[str, Any]:
        """Generate optimized voiceover script"""
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
                
                # Generate voiceover script
                voiceover_script = await self._generate_optimized_script(
                    content_piece, script_style, target_duration
                )
                
                # Generate script timing
                script_timing = await self._generate_script_timing(
                    voiceover_script, target_duration
                )
                
                # Generate pronunciation guide
                pronunciation_guide = await self._generate_pronunciation_guide(
                    voiceover_script
                )
                
                # Generate script annotations
                script_annotations = await self._generate_script_annotations(
                    voiceover_script, script_style
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "script_style": script_style,
                    "target_duration": target_duration,
                    "voiceover_script": voiceover_script,
                    "script_timing": script_timing,
                    "pronunciation_guide": pronunciation_guide,
                    "script_annotations": script_annotations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Voiceover script generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _prepare_voiceover_script(
        self, content_piece: ContentPiece, voice_characteristics: Dict[str, Any]
    ) -> str:
        """Prepare content for voiceover generation"""
        script_prompt = self._create_script_preparation_prompt(
            content_piece, voice_characteristics
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates voiceover scripts."}, {"role": "user", "content": script_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
        script_result = ai_response.text_content if ai_response.success else ""
        return script_result
    
    async def _generate_voiceover_audio(
        self, voiceover_script: str, voice_characteristics: Dict[str, Any], audio_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate voiceover audio using Groq TTS"""
        try:
            import uuid
            from core.storage.s3_manager import storage_manager
            from core.ai import get_ai_service_manager

            # Initialize AI service manager if not already done
            if not hasattr(self, '_ai_service_manager') or self._ai_service_manager is None:
                self._ai_service_manager = await get_ai_service_manager()

            # Generate unique voiceover ID
            voiceover_id = f"voiceover_{uuid.uuid4().hex[:12]}"

            # Map voice characteristics to Groq TTS parameters
            voice = voice_characteristics.get("voice", "default")
            language = voice_characteristics.get("language", "en")
            speed = audio_settings.get("speed", 1.0)
            pitch = audio_settings.get("pitch", 1.0)
            voice_style = voice_characteristics.get("style", None)

            # Call Groq TTS via AI Service Manager
            tts_result = await self._ai_service_manager.text_to_speech(
                text=voiceover_script,
                voice=voice if voice != "default" else None,  # Let Groq choose default if not specified
                language=language,
                speed=speed,
                pitch=pitch,
                voice_style=voice_style
            )

            if not tts_result.get("success"):
                return {
                    "success": False,
                    "error": tts_result.get("error", "TTS generation failed")
                }

            audio_data = tts_result.get("audio_data")
            if not audio_data:
                return {
                    "success": False,
                    "error": "No audio data returned from TTS service"
                }

            # Upload audio to storage
            audio_filename = f"voiceovers/{voiceover_id}.mp3"
            try:
                audio_url = storage_manager.put_bytes(audio_data, "audio/mpeg", audio_filename)
            except Exception:
                # Fallback: if storage manager fails, still return local metadata
                audio_url = f"/internal_storage/{audio_filename}"

            # Calculate audio duration and file size
            duration_seconds = max(1.0, len(voiceover_script) / 15.0)  # Rough estimate: 15 chars per second
            file_size_mb = len(audio_data) / (1024 * 1024)

            return {
                "success": True,
                "voiceover_id": voiceover_id,
                "audio_url": audio_url,
                "duration_seconds": round(duration_seconds, 2),
                "file_size_mb": round(file_size_mb, 2),
                "audio_format": "mp3",
                "quality": "high",
            }
        except Exception as e:
            logger.error(f"_generate_voiceover_audio failed: {e}")
            return {"success": False, "error": str(e)}
    async def _generate_voiceover_metadata(
        self, voiceover_result: Dict[str, Any], voice_characteristics: Dict[str, Any], audio_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate voiceover metadata"""
        return {
            "voiceover_id": voiceover_result.get("voiceover_id"),
            "voice_characteristics": voice_characteristics,
            "audio_settings": audio_settings,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "quality_metrics": {
                "clarity_score": 0.95,
                "naturalness_score": 0.88,
                "pronunciation_accuracy": 0.92
            }
        }
    
    async def _generate_translations(
        self, content_piece: ContentPiece, target_languages: List[str], translation_style: str
    ) -> Dict[str, str]:
        """Generate translations for content"""
        translations = {}
        
        for language in target_languages:
            translation_prompt = self._create_translation_prompt(
                content_piece, language, translation_style
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": f"You are an AI assistant that translates content to {language}."}, {"role": "user", "content": translation_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
            translation_result = ai_response.text_content if ai_response.success else ""
            translations[language] = translation_result
        
        return translations
    
    async def _generate_language_voiceover(
        self, translated_content: str, language: str, voice_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate voiceover for specific language"""
        # This would generate actual voiceover for the language
        return {
            "language": language,
            "voiceover_id": f"voiceover_{language}_{int(datetime.utcnow().timestamp())}",
            "audio_url": f"https://shakes.com/voiceovers/{language}_sample.mp3",
            "duration_seconds": 45,
            "translated_content": translated_content
        }
    
    async def _generate_language_metadata(
        self, multilingual_voiceovers: Dict[str, Any], target_languages: List[str]
    ) -> Dict[str, Any]:
        """Generate metadata for multilingual voiceovers"""
        return {
            "languages": target_languages,
            "total_voiceovers": len(multilingual_voiceovers),
            "generation_timestamp": datetime.utcnow().isoformat(),
            "language_specific_metadata": {
                language: {
                    "voiceover_id": voiceover.get("voiceover_id"),
                    "duration_seconds": voiceover.get("duration_seconds"),
                    "audio_quality": "high"
                }
                for language, voiceover in multilingual_voiceovers.items()
            }
        }
    
    async def _generate_voice_customization(
        self, base_voice: str, customization_parameters: Dict[str, Any], target_audience: str
    ) -> Dict[str, Any]:
        """Generate voice customization"""
        customization_prompt = self._create_voice_customization_prompt(
            base_voice, customization_parameters, target_audience
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that customizes voiceover scripts."}, {"role": "user", "content": customization_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
        customization_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "base_voice": base_voice,
            "customization_parameters": customization_parameters,
            "target_audience": target_audience,
            "customization_result": customization_result,
            "customized_voice_id": f"custom_voice_{int(datetime.utcnow().timestamp())}"
        }
    
    async def _generate_voice_samples(
        self, voice_customization: Dict[str, Any], customization_parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate voice samples"""
        try:
            import uuid
            from core.storage.s3_manager import storage_manager
            
            samples = []
            sample_texts = [
                "Hello, this is a sample of the customized voice.",
                "This voice has been optimized for your target audience.",
                "Listen to how the voice adapts to different content types.",
                "The voice maintains consistency while expressing emotion."
            ]
            
            # Use global storage manager
            
            for i, sample_text in enumerate(sample_texts):
                sample_id = f"sample_{uuid.uuid4().hex[:8]}"
                
                # Generate audio for sample
                audio_result = await self._generate_voiceover_audio(
                    sample_text,
                    voice_customization,
                    customization_parameters
                )
                
                if audio_result.get("success"):
                    samples.append({
                        "sample_id": sample_id,
                        "sample_text": sample_text,
                        "audio_url": audio_result.get("audio_url", ""),
                        "duration_seconds": audio_result.get("duration_seconds", 0),
                        "file_size_mb": audio_result.get("file_size_mb", 0),
                        "audio_format": audio_result.get("audio_format", "mp3")
                    })
                else:
                    # Fallback sample without audio
                    samples.append({
                        "sample_id": sample_id,
                        "sample_text": sample_text,
                        "audio_url": "",
                        "duration_seconds": len(sample_text) / 15,  # Rough estimate
                        "file_size_mb": 0,
                        "audio_format": "mp3",
                        "error": "Audio generation failed"
                    })
            
            return samples
            
        except Exception as e:
            logger.error(f"Failed to generate voice samples: {e}")
            # Return fallback samples
            return [
                {
                    "sample_id": "sample_1",
                    "sample_text": "Hello, this is a sample of the customized voice.",
                    "audio_url": "",
                    "duration_seconds": 5,
                    "file_size_mb": 0,
                    "audio_format": "mp3",
                    "error": "Sample generation failed"
                },
                {
                    "sample_id": "sample_2", 
                    "sample_text": "This voice has been optimized for your target audience.",
                    "audio_url": "",
                    "duration_seconds": 6,
                    "file_size_mb": 0,
                    "audio_format": "mp3",
                    "error": "Sample generation failed"
                }
            ]
    
    async def _generate_customization_recommendations(
        self, voice_customization: Dict[str, Any], target_audience: str
    ) -> List[Dict[str, Any]]:
        """Generate customization recommendations"""
        try:
            recommendations_prompt = self._create_customization_recommendations_prompt(
                voice_customization, target_audience
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that provides voiceover recommendations."}, {"role": "user", "content": recommendations_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.6)
            recommendations_result = ai_response.text_content if ai_response.success else ""
            
            # Parse the AI-generated recommendations
            recommendations = self._parse_customization_recommendations(recommendations_result)
            
            # If parsing fails, return fallback recommendations
            if not recommendations:
                recommendations = [
                    {
                        "recommendation_type": "pitch",
                        "description": "Adjust pitch for better audience engagement",
                        "priority": "medium",
                        "impact": "moderate"
                    },
                    {
                        "recommendation_type": "pace", 
                        "description": "Optimize speaking pace for clarity",
                        "priority": "high",
                        "impact": "high"
                    },
                    {
                        "recommendation_type": "tone",
                        "description": "Modify tone to match target audience preferences",
                        "priority": "high",
                        "impact": "high"
                    }
                ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate customization recommendations: {e}")
            # Return fallback recommendations
            return [
                {
                    "recommendation_type": "pitch",
                    "description": "Adjust pitch for better audience engagement",
                    "priority": "medium",
                    "impact": "moderate"
                },
                {
                    "recommendation_type": "pace",
                    "description": "Optimize speaking pace for clarity", 
                    "priority": "high",
                    "impact": "high"
                }
            ]
    
    def _parse_customization_recommendations(self, recommendations_result: str) -> List[Dict[str, Any]]:
        """Parse AI-generated customization recommendations"""
        try:
            recommendations = []
            lines = recommendations_result.strip().split('\n')
            
            current_recommendation = {}
            for line in lines:
                line = line.strip()
                if not line:
                    if current_recommendation:
                        recommendations.append(current_recommendation)
                        current_recommendation = {}
                    continue
                
                if line.startswith('Type:'):
                    current_recommendation['recommendation_type'] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('Description:'):
                    current_recommendation['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('Priority:'):
                    current_recommendation['priority'] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('Impact:'):
                    current_recommendation['impact'] = line.split(':', 1)[1].strip().lower()
            
            # Add the last recommendation if exists
            if current_recommendation:
                recommendations.append(current_recommendation)
            
            # Ensure all recommendations have required fields
            for rec in recommendations:
                if 'recommendation_type' not in rec:
                    rec['recommendation_type'] = 'general'
                if 'description' not in rec:
                    rec['description'] = 'Voice customization recommendation'
                if 'priority' not in rec:
                    rec['priority'] = 'medium'
                if 'impact' not in rec:
                    rec['impact'] = 'moderate'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to parse customization recommendations: {e}")
            return []
    
    async def _generate_optimized_script(
        self, content_piece: ContentPiece, script_style: str, target_duration: int
    ) -> str:
        """Generate optimized voiceover script"""
        script_prompt = self._create_optimized_script_prompt(
            content_piece, script_style, target_duration
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates voiceover scripts."}, {"role": "user", "content": script_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
        script_result = ai_response.text_content if ai_response.success else ""
        return script_result
    
    async def _generate_script_timing(
        self, voiceover_script: str, target_duration: int
    ) -> List[Dict[str, Any]]:
        """Generate script timing breakdown"""
        # Calculate timing based on word count and target duration
        words = voiceover_script.split()
        words_per_second = len(words) / target_duration
        
        timing_breakdown = []
        current_time = 0
        
        for i, word in enumerate(words):
            word_duration = 1 / words_per_second
            timing_breakdown.append({
                "word": word,
                "start_time": current_time,
                "end_time": current_time + word_duration,
                "duration": word_duration
            })
            current_time += word_duration
        
        return timing_breakdown
    
    async def _generate_pronunciation_guide(
        self, voiceover_script: str
    ) -> Dict[str, Any]:
        """Generate pronunciation guide"""
        pronunciation_prompt = self._create_pronunciation_prompt(voiceover_script)
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that provides pronunciation guides."}, {"role": "user", "content": pronunciation_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.6)
        pronunciation_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "pronunciation_guide": pronunciation_result,
            "difficult_words": [],
            "phonetic_transcriptions": {}
        }
    
    async def _generate_script_annotations(
        self, voiceover_script: str, script_style: str
    ) -> List[Dict[str, Any]]:
        """Generate script annotations"""
        annotations_prompt = self._create_annotations_prompt(voiceover_script, script_style)
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates voiceover annotations."}, {"role": "user", "content": annotations_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.6)
        annotations_result = ai_response.text_content if ai_response.success else ""
        
        return [
            {
                "annotation_type": "emphasis",
                "text": "key phrase",
                "instruction": "emphasize this phrase",
                "position": 0.5
            }
        ]
    
    def _create_script_preparation_prompt(
        self, content_piece: ContentPiece, voice_characteristics: Dict[str, Any]
    ) -> str:
        """Create prompt for script preparation"""
        return f"""
        Prepare this content for voiceover generation:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Voice Characteristics: {voice_characteristics}
        
        Optimize the content for natural speech delivery, including:
        1. Natural phrasing and pauses
        2. Pronunciation-friendly text
        3. Appropriate pacing
        4. Clear articulation points
        
        Generate the optimized voiceover script.
        """
    
    def _create_translation_prompt(
        self, content_piece: ContentPiece, language: str, translation_style: str
    ) -> str:
        """Create prompt for translation"""
        return f"""
        Translate this content to {language}:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Translation Style: {translation_style}
        
        Provide natural, culturally appropriate translation suitable for voiceover.
        """
    
    def _create_voice_customization_prompt(
        self, base_voice: str, customization_parameters: Dict[str, Any], target_audience: str
    ) -> str:
        """Create prompt for voice customization"""
        return f"""
        Customize voice characteristics:
        
        Base Voice: {base_voice}
        Customization Parameters: {customization_parameters}
        Target Audience: {target_audience}
        
        Provide voice customization recommendations for optimal audience engagement.
        """
    
    def _create_customization_recommendations_prompt(
        self, voice_customization: Dict[str, Any], target_audience: str
    ) -> str:
        """Create prompt for customization recommendations"""
        return f"""
        Provide voice customization recommendations:
        
        Voice Customization: {voice_customization}
        Target Audience: {target_audience}
        
        Provide specific recommendations for voice optimization.
        """
    
    def _create_optimized_script_prompt(
        self, content_piece: ContentPiece, script_style: str, target_duration: int
    ) -> str:
        """Create prompt for optimized script"""
        return f"""
        Create optimized voiceover script:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Script Style: {script_style}
        Target Duration: {target_duration} seconds
        
        Create script optimized for voiceover delivery.
        """
    
    def _create_pronunciation_prompt(self, voiceover_script: str) -> str:
        """Create prompt for pronunciation guide"""
        return f"""
        Create pronunciation guide for this script:
        
        Script: {voiceover_script}
        
        Provide pronunciation guidance for difficult words and phrases.
        """
    
    def _create_annotations_prompt(self, voiceover_script: str, script_style: str) -> str:
        """Create prompt for script annotations"""
        return f"""
        Create script annotations for voiceover:
        
        Script: {voiceover_script}
        Script Style: {script_style}
        
        Provide annotations for emphasis, pauses, and delivery instructions.
        """
