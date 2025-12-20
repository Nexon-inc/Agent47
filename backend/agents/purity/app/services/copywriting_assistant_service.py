from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BrandIdentity, BusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class CopywritingAssistantService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def generate_landing_page_copy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        value_proposition: str,
        call_to_action: str,
        page_sections: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"landing_page_copy:{business_idea_id}:{target_audience}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_landing_page_prompt(
                business_idea, target_audience, value_proposition, call_to_action, page_sections
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI copywriting assistant. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            copy_data = json.loads(ai_response)
            
            landing_page_copy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "value_proposition": value_proposition,
                "call_to_action": call_to_action,
                "page_sections": page_sections,
                "hero_section": copy_data.get("hero_section", ""),
                "benefits_section": copy_data.get("benefits_section", ""),
                "features_section": copy_data.get("features_section", ""),
                "testimonials_section": copy_data.get("testimonials_section", ""),
                "pricing_section": copy_data.get("pricing_section", ""),
                "faq_section": copy_data.get("faq_section", ""),
                "meta_tags": copy_data.get("meta_tags", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(copy_data), expire=3600)
            await self.event_bus.publish("purity.landing_page_copy_generated", {
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return landing_page_copy
            
        except Exception as e:
            raise e
    
    async def create_ad_copy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        ad_platform: str,
        ad_type: str,
        target_audience: str,
        ad_objective: str,
        budget_range: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_ad_copy_prompt(
                business_idea, ad_platform, ad_type, target_audience, ad_objective, budget_range
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI copywriting assistant. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            ad_data = json.loads(ai_response)
            
            ad_copy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "ad_platform": ad_platform,
                "ad_type": ad_type,
                "target_audience": target_audience,
                "ad_objective": ad_objective,
                "budget_range": budget_range,
                "headlines": ad_data.get("headlines", []),
                "descriptions": ad_data.get("descriptions", []),
                "call_to_actions": ad_data.get("call_to_actions", []),
                "keywords": ad_data.get("keywords", []),
                "targeting_suggestions": ad_data.get("targeting_suggestions", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.ad_copy_created", {
                "business_idea_id": business_idea_id,
                "ad_platform": ad_platform,
                "ad_type": ad_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return ad_copy
            
        except Exception as e:
            raise e
    
    async def write_product_description(
        self,
        db: AsyncSession,
        business_idea_id: int,
        product_name: str,
        product_features: List[str],
        target_audience: str,
        tone: str,
        length_preference: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_product_description_prompt(
                business_idea, product_name, product_features, target_audience, tone, length_preference
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI copywriting assistant. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            description_data = json.loads(ai_response)
            
            product_description = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "product_name": product_name,
                "product_features": product_features,
                "target_audience": target_audience,
                "tone": tone,
                "length_preference": length_preference,
                "short_description": description_data.get("short_description", ""),
                "detailed_description": description_data.get("detailed_description", ""),
                "feature_highlights": description_data.get("feature_highlights", []),
                "benefits_list": description_data.get("benefits_list", []),
                "technical_specs": description_data.get("technical_specs", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.product_description_written", {
                "business_idea_id": business_idea_id,
                "product_name": product_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return product_description
            
        except Exception as e:
            raise e
    
    async def create_email_copy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        email_type: str,
        target_audience: str,
        email_purpose: str,
        tone: str,
        include_offer: bool = False
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_email_copy_prompt(
                business_idea, email_type, target_audience, email_purpose, tone, include_offer
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI copywriting assistant. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            email_data = json.loads(ai_response)
            
            email_copy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "email_type": email_type,
                "target_audience": target_audience,
                "email_purpose": email_purpose,
                "tone": tone,
                "include_offer": include_offer,
                "subject_line": email_data.get("subject_line", ""),
                "preheader": email_data.get("preheader", ""),
                "opening": email_data.get("opening", ""),
                "body_content": email_data.get("body_content", ""),
                "call_to_action": email_data.get("call_to_action", ""),
                "closing": email_data.get("closing", ""),
                "personalization_tokens": email_data.get("personalization_tokens", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.email_copy_created", {
                "business_idea_id": business_idea_id,
                "email_type": email_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return email_copy
            
        except Exception as e:
            raise e
    
    def _create_landing_page_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        value_proposition: str,
        call_to_action: str,
        page_sections: List[str]
    ) -> str:
        return f"""
        Create landing page copy for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Value Proposition: {value_proposition}
        - Call to Action: {call_to_action}
        - Page Sections: {', '.join(page_sections)}
        
        Generate compelling landing page copy including:
        1. Hero section
        2. Benefits section
        3. Features section
        4. Testimonials section
        5. Pricing section
        6. FAQ section
        7. Meta tags for SEO
        
        Return the response as a JSON object with the following structure:
        {{
            "hero_section": {{
                "headline": "Compelling headline",
                "subheadline": "Supporting subheadline",
                "hero_description": "Hero section description"
            }},
            "benefits_section": {{
                "main_benefit": "Main benefit description",
                "benefit_list": ["Benefit 1", "Benefit 2", "Benefit 3"]
            }},
            "features_section": {{
                "feature_1": "Feature 1 description",
                "feature_2": "Feature 2 description",
                "feature_3": "Feature 3 description"
            }},
            "testimonials_section": {{
                "testimonial_1": "Customer testimonial 1",
                "testimonial_2": "Customer testimonial 2"
            }},
            "pricing_section": {{
                "pricing_headline": "Pricing headline",
                "pricing_description": "Pricing description"
            }},
            "faq_section": {{
                "faq_1": "FAQ question and answer 1",
                "faq_2": "FAQ question and answer 2"
            }},
            "meta_tags": {{
                "title": "SEO title",
                "description": "SEO description",
                "keywords": "SEO keywords"
            }}
        }}
        """
    
    def _create_ad_copy_prompt(
        self,
        business_idea: BusinessIdea,
        ad_platform: str,
        ad_type: str,
        target_audience: str,
        ad_objective: str,
        budget_range: str
    ) -> str:
        return f"""
        Create ad copy for:
        - Business Idea: {business_idea.description}
        - Ad Platform: {ad_platform}
        - Ad Type: {ad_type}
        - Target Audience: {target_audience}
        - Ad Objective: {ad_objective}
        - Budget Range: {budget_range}
        
        Generate comprehensive ad copy including:
        1. Multiple headline variations
        2. Description variations
        3. Call-to-action options
        4. Keywords for targeting
        5. Targeting suggestions
        
        Return the response as a JSON object with the following structure:
        {{
            "headlines": [
                "Headline variation 1",
                "Headline variation 2",
                "Headline variation 3"
            ],
            "descriptions": [
                "Description variation 1",
                "Description variation 2",
                "Description variation 3"
            ],
            "call_to_actions": [
                "CTA option 1",
                "CTA option 2",
                "CTA option 3"
            ],
            "keywords": [
                "Keyword 1",
                "Keyword 2",
                "Keyword 3"
            ],
            "targeting_suggestions": {{
                "demographics": "Demographic targeting",
                "interests": "Interest targeting",
                "behaviors": "Behavioral targeting"
            }}
        }}
        """
    
    def _create_product_description_prompt(
        self,
        business_idea: BusinessIdea,
        product_name: str,
        product_features: List[str],
        target_audience: str,
        tone: str,
        length_preference: str
    ) -> str:
        return f"""
        Write product description for:
        - Business Idea: {business_idea.description}
        - Product Name: {product_name}
        - Product Features: {', '.join(product_features)}
        - Target Audience: {target_audience}
        - Tone: {tone}
        - Length Preference: {length_preference}
        
        Create compelling product description including:
        1. Short description
        2. Detailed description
        3. Feature highlights
        4. Benefits list
        5. Technical specifications
        
        Return the response as a JSON object with the following structure:
        {{
            "short_description": "Concise product description",
            "detailed_description": "Comprehensive product description",
            "feature_highlights": [
                "Feature highlight 1",
                "Feature highlight 2",
                "Feature highlight 3"
            ],
            "benefits_list": [
                "Benefit 1",
                "Benefit 2",
                "Benefit 3"
            ],
            "technical_specs": {{
                "spec_1": "Technical specification 1",
                "spec_2": "Technical specification 2",
                "spec_3": "Technical specification 3"
            }}
        }}
        """
    
    def _create_email_copy_prompt(
        self,
        business_idea: BusinessIdea,
        email_type: str,
        target_audience: str,
        email_purpose: str,
        tone: str,
        include_offer: bool
    ) -> str:
        return f"""
        Create email copy for:
        - Business Idea: {business_idea.description}
        - Email Type: {email_type}
        - Target Audience: {target_audience}
        - Email Purpose: {email_purpose}
        - Tone: {tone}
        - Include Offer: {include_offer}
        
        Generate comprehensive email copy including:
        1. Subject line
        2. Preheader text
        3. Opening
        4. Body content
        5. Call to action
        6. Closing
        7. Personalization tokens
        
        Return the response as a JSON object with the following structure:
        {{
            "subject_line": "Compelling subject line",
            "preheader": "Preheader text",
            "opening": "Email opening",
            "body_content": "Main email content",
            "call_to_action": "Call to action text",
            "closing": "Email closing",
            "personalization_tokens": [
                "{{first_name}}",
                "{{company_name}}",
                "{{product_name}}"
            ]
        }}
        """
