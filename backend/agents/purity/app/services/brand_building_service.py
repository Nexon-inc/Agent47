from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BrandIdentity, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class BrandBuildingService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_brand_identity(
        self,
        db: AsyncSession,
        business_idea_id: int,
        brand_name: str,
        industry: str,
        target_audience: str,
        brand_personality: str,
        brand_values: List[str],
        color_preferences: Optional[List[str]] = None,
        style_preferences: Optional[str] = None
    ) -> BrandIdentity:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"brand_identity:{brand_name}:{industry}:{target_audience}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_brand_identity_prompt(
                brand_name, industry, target_audience, brand_personality,
                brand_values, color_preferences, style_preferences, business_idea.description
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with brand building. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            brand_data = json.loads(ai_response)
            
            brand_identity = BrandIdentity(
                business_idea_id=business_idea_id,
                brand_name=brand_name,
                industry=industry,
                target_audience=target_audience,
                brand_personality=brand_personality,
                brand_values=json.dumps(brand_values),
                brand_story=brand_data.get("brand_story", ""),
                brand_mission=brand_data.get("brand_mission", ""),
                brand_vision=brand_data.get("brand_vision", ""),
                brand_positioning=brand_data.get("brand_positioning", "")
            )
            
            db.add(brand_identity)
            await db.commit()
            await db.refresh(brand_identity)
            
            await self.redis_manager.set(cache_key, json.dumps(brand_data), expire=3600)
            await self.event_bus.publish("purity.brand_identity_created", {
                "business_idea_id": business_idea_id,
                "brand_name": brand_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return brand_identity
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def generate_logo_concepts(
        self,
        db: AsyncSession,
        brand_identity_id: int,
        logo_style: str,
        color_scheme: List[str],
        logo_type: str,
        additional_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            brand_identity_result = await db.execute(
                select(BrandIdentity).where(BrandIdentity.id == brand_identity_id)
            )
            brand_identity = brand_identity_result.scalar_one_or_none()
            if not brand_identity:
                raise ValueError("Brand identity not found")
            
            prompt = self._create_logo_generation_prompt(
                brand_identity, logo_style, color_scheme, logo_type, additional_requirements
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with brand building. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            logo_data = json.loads(ai_response)
            
            logo_concepts = {
                "id": brand_identity_id,
                "brand_identity_id": brand_identity_id,
                "logo_concepts": logo_data.get("logo_concepts", []),
                "logo_files": logo_data.get("logo_files", []),
                "color_palette": logo_data.get("color_palette", []),
                "typography_suggestions": logo_data.get("typography_suggestions", []),
                "logo_guidelines": logo_data.get("logo_guidelines", ""),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.logo_concepts_generated", {
                "brand_identity_id": brand_identity_id,
                "logo_style": logo_style,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return logo_concepts
            
        except Exception as e:
            raise e
    
    async def develop_brand_slogan(
        self,
        db: AsyncSession,
        brand_identity_id: int,
        tone: str,
        length_preference: str,
        key_message: str,
        target_emotion: str
    ) -> Dict[str, Any]:
        try:
            brand_identity_result = await db.execute(
                select(BrandIdentity).where(BrandIdentity.id == brand_identity_id)
            )
            brand_identity = brand_identity_result.scalar_one_or_none()
            if not brand_identity:
                raise ValueError("Brand identity not found")
            
            prompt = self._create_slogan_development_prompt(
                brand_identity, tone, length_preference, key_message, target_emotion
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with brand building. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            slogan_data = json.loads(ai_response)
            
            slogan_options = {
                "id": brand_identity_id,
                "brand_identity_id": brand_identity_id,
                "slogan_options": slogan_data.get("slogan_options", []),
                "tagline_variations": slogan_data.get("tagline_variations", []),
                "messaging_framework": slogan_data.get("messaging_framework", {}),
                "brand_voice_guidelines": slogan_data.get("brand_voice_guidelines", ""),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.brand_slogan_developed", {
                "brand_identity_id": brand_identity_id,
                "tone": tone,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return slogan_options
            
        except Exception as e:
            raise e
    
    async def create_style_guide(
        self,
        db: AsyncSession,
        brand_identity_id: int,
        include_logo_usage: bool = True,
        include_color_palette: bool = True,
        include_typography: bool = True,
        include_imagery: bool = True,
        include_voice_tone: bool = True
    ) -> Dict[str, Any]:
        try:
            brand_identity_result = await db.execute(
                select(BrandIdentity).where(BrandIdentity.id == brand_identity_id)
            )
            brand_identity = brand_identity_result.scalar_one_or_none()
            if not brand_identity:
                raise ValueError("Brand identity not found")
            
            prompt = self._create_style_guide_prompt(
                brand_identity, include_logo_usage, include_color_palette,
                include_typography, include_imagery, include_voice_tone
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with brand building. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            style_guide_data = json.loads(ai_response)
            
            style_guide = {
                "id": brand_identity_id,
                "brand_identity_id": brand_identity_id,
                "logo_usage_guidelines": style_guide_data.get("logo_usage_guidelines", {}),
                "color_palette": style_guide_data.get("color_palette", {}),
                "typography_guide": style_guide_data.get("typography_guide", {}),
                "imagery_guidelines": style_guide_data.get("imagery_guidelines", {}),
                "voice_tone_guide": style_guide_data.get("voice_tone_guide", {}),
                "brand_guidelines_document": style_guide_data.get("brand_guidelines_document", ""),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.style_guide_created", {
                "brand_identity_id": brand_identity_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return style_guide
            
        except Exception as e:
            raise e
    
    async def update_brand_identity(
        self,
        db: AsyncSession,
        identity_id: int,
        brand_name: str,
        industry: str,
        target_audience: str,
        brand_personality: str,
        brand_values: List[str],
        color_preferences: Optional[List[str]] = None,
        style_preferences: Optional[str] = None
    ) -> BrandIdentity:
        try:
            result = await db.execute(
                select(BrandIdentity).where(BrandIdentity.id == identity_id)
            )
            brand_identity = result.scalar_one_or_none()
            if not brand_identity:
                raise ValueError("Brand identity not found")
            
            prompt = self._create_brand_identity_prompt(
                brand_name, industry, target_audience, brand_personality,
                brand_values, color_preferences, style_preferences, ""
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with brand building. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            brand_data = json.loads(ai_response)
            
            brand_identity.brand_name = brand_name
            brand_identity.industry = industry
            brand_identity.target_audience = target_audience
            brand_identity.brand_personality = brand_personality
            brand_identity.brand_values = json.dumps(brand_values)
            brand_identity.brand_story = brand_data.get("brand_story", "")
            brand_identity.brand_mission = brand_data.get("brand_mission", "")
            brand_identity.brand_vision = brand_data.get("brand_vision", "")
            brand_identity.brand_positioning = brand_data.get("brand_positioning", "")
            brand_identity.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(brand_identity)
            
            await self.event_bus.publish("purity.brand_identity_updated", {
                "identity_id": identity_id,
                "brand_name": brand_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return brand_identity
            
        except Exception as e:
            await db.rollback()
            raise e
    
    def _create_brand_identity_prompt(
        self,
        brand_name: str,
        industry: str,
        target_audience: str,
        brand_personality: str,
        brand_values: List[str],
        color_preferences: Optional[List[str]],
        style_preferences: Optional[str],
        business_description: str
    ) -> str:
        return f"""
        Create a comprehensive brand identity for:
        - Brand Name: {brand_name}
        - Industry: {industry}
        - Target Audience: {target_audience}
        - Brand Personality: {brand_personality}
        - Brand Values: {', '.join(brand_values)}
        - Color Preferences: {', '.join(color_preferences) if color_preferences else 'None specified'}
        - Style Preferences: {style_preferences or 'None specified'}
        - Business Description: {business_description}
        
        Develop a complete brand identity including:
        1. Brand story
        2. Brand mission
        3. Brand vision
        4. Brand positioning statement
        
        Return the response as a JSON object with the following structure:
        {{
            "brand_story": "Compelling brand story that connects with the target audience",
            "brand_mission": "Clear and concise brand mission statement",
            "brand_vision": "Inspiring brand vision for the future",
            "brand_positioning": "Strategic brand positioning statement"
        }}
        """
    
    def _create_logo_generation_prompt(
        self,
        brand_identity: BrandIdentity,
        logo_style: str,
        color_scheme: List[str],
        logo_type: str,
        additional_requirements: Optional[str]
    ) -> str:
        return f"""
        Generate logo concepts for the brand:
        - Brand Name: {brand_identity.brand_name}
        - Industry: {brand_identity.industry}
        - Target Audience: {brand_identity.target_audience}
        - Brand Personality: {brand_identity.brand_personality}
        - Logo Style: {logo_style}
        - Color Scheme: {', '.join(color_scheme)}
        - Logo Type: {logo_type}
        - Additional Requirements: {additional_requirements or 'None'}
        
        Create comprehensive logo concepts including:
        1. Logo concept descriptions
        2. Logo file specifications
        3. Color palette recommendations
        4. Typography suggestions
        5. Logo usage guidelines
        
        Return the response as a JSON object with the following structure:
        {{
            "logo_concepts": [
                {{
                    "name": "Concept Name",
                    "description": "Concept description",
                    "style": "Style description",
                    "colors": ["Color 1", "Color 2"],
                    "typography": "Typography recommendation"
                }}
            ],
            "logo_files": ["file1.svg", "file2.png", "file3.ai"],
            "color_palette": ["Primary Color", "Secondary Color", "Accent Color"],
            "typography_suggestions": ["Font 1", "Font 2", "Font 3"],
            "logo_guidelines": "Comprehensive logo usage guidelines"
        }}
        """
    
    def _create_slogan_development_prompt(
        self,
        brand_identity: BrandIdentity,
        tone: str,
        length_preference: str,
        key_message: str,
        target_emotion: str
    ) -> str:
        return f"""
        Develop brand slogans for:
        - Brand Name: {brand_identity.brand_name}
        - Industry: {brand_identity.industry}
        - Target Audience: {brand_identity.target_audience}
        - Brand Personality: {brand_identity.brand_personality}
        - Tone: {tone}
        - Length Preference: {length_preference}
        - Key Message: {key_message}
        - Target Emotion: {target_emotion}
        
        Create comprehensive slogan options including:
        1. Multiple slogan variations
        2. Tagline options
        3. Messaging framework
        4. Brand voice guidelines
        
        Return the response as a JSON object with the following structure:
        {{
            "slogan_options": ["Slogan 1", "Slogan 2", "Slogan 3"],
            "tagline_variations": ["Tagline 1", "Tagline 2", "Tagline 3"],
            "messaging_framework": {{
                "primary_message": "Primary message",
                "supporting_points": ["Point 1", "Point 2"],
                "tone_guidelines": "Tone guidelines"
            }},
            "brand_voice_guidelines": "Comprehensive brand voice guidelines"
        }}
        """
    
    def _create_style_guide_prompt(
        self,
        brand_identity: BrandIdentity,
        include_logo_usage: bool,
        include_color_palette: bool,
        include_typography: bool,
        include_imagery: bool,
        include_voice_tone: bool
    ) -> str:
        return f"""
        Create a comprehensive style guide for:
        - Brand Name: {brand_identity.brand_name}
        - Industry: {brand_identity.industry}
        - Target Audience: {brand_identity.target_audience}
        - Brand Personality: {brand_identity.brand_personality}
        - Brand Values: {brand_identity.brand_values}
        
        Include the following sections:
        - Logo Usage: {include_logo_usage}
        - Color Palette: {include_color_palette}
        - Typography: {include_typography}
        - Imagery: {include_imagery}
        - Voice & Tone: {include_voice_tone}
        
        Return the response as a JSON object with the following structure:
        {{
            "logo_usage_guidelines": {{
                "clear_space": "Clear space requirements",
                "minimum_size": "Minimum size specifications",
                "color_variations": "Color variation guidelines",
                "placement_rules": "Placement rules and restrictions"
            }},
            "color_palette": {{
                "primary_colors": ["Color 1", "Color 2"],
                "secondary_colors": ["Color 3", "Color 4"],
                "accent_colors": ["Color 5", "Color 6"],
                "usage_guidelines": "Color usage guidelines"
            }},
            "typography_guide": {{
                "primary_font": "Primary font family",
                "secondary_font": "Secondary font family",
                "font_hierarchy": "Font hierarchy guidelines",
                "usage_rules": "Typography usage rules"
            }},
            "imagery_guidelines": {{
                "style": "Image style guidelines",
                "composition": "Composition rules",
                "color_treatment": "Color treatment guidelines",
                "subject_matter": "Subject matter guidelines"
            }},
            "voice_tone_guide": {{
                "voice_characteristics": "Voice characteristics",
                "tone_variations": "Tone variations for different contexts",
                "writing_guidelines": "Writing guidelines",
                "examples": "Voice and tone examples"
            }},
            "brand_guidelines_document": "Complete brand guidelines document"
        }}
        """
