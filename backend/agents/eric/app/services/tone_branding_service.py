from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from backend.core.cache.redis_manager import RedisManager
from backend.core.messaging.kafka_manager import KafkaManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep
)

logger = logging.getLogger(__name__)

class ToneProfile(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    tone_characteristics: Dict[str, Any]
    language_style: str
    formality_level: str
    personality_traits: List[str]
    industry_specific: bool
    target_audience: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BrandingProfile(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    brand_voice: str
    brand_values: List[str]
    color_scheme: Dict[str, str]
    logo_url: Optional[str] = None
    tagline: Optional[str] = None
    company_info: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ToneBrandingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize tone branding service"""
        if self._initialized:
            return
        
        try:
            from backend.core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Tone branding service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tone branding service: {e}")
            raise
    
    async def create_tone_profile(self, tone_data: ToneProfile) -> ToneProfile:
        """Create a new tone profile for sales outreach"""
        async with get_eric_database() as session:
            try:
                # Validate tone characteristics
                if not self._validate_tone_characteristics(tone_data.tone_characteristics):
                    raise ValueError("Invalid tone characteristics")
                
                # Create tone profile record
                tone_profile = {
                    "name": tone_data.name,
                    "description": tone_data.description,
                    "tone_characteristics": json.dumps(tone_data.tone_characteristics),
                    "language_style": tone_data.language_style,
                    "formality_level": tone_data.formality_level,
                    "personality_traits": json.dumps(tone_data.personality_traits),
                    "industry_specific": tone_data.industry_specific,
                    "target_audience": json.dumps(tone_data.target_audience),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Store in database (simplified for demo)
                tone_data.id = 1  # Simulate ID generation
                tone_data.created_at = tone_profile["created_at"]
                tone_data.updated_at = tone_profile["updated_at"]
                
                # Cache tone profile
                await self.redis_manager.set_cache(
                    f"tone_profile_{tone_data.id}",
                    tone_data.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "tone_branding.tone_profile_created",
                    {
                        "tone_profile_id": tone_data.id,
                        "name": tone_data.name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created tone profile: {tone_data.name}")
                return tone_data
                
            except Exception as e:
                logger.error(f"Failed to create tone profile: {e}")
                raise
    
    async def create_branding_profile(self, branding_data: BrandingProfile) -> BrandingProfile:
        """Create a new branding profile for sales outreach"""
        async with get_eric_database() as session:
            try:
                # Validate branding data
                if not self._validate_branding_data(branding_data):
                    raise ValueError("Invalid branding data")
                
                # Create branding profile record
                branding_profile = {
                    "name": branding_data.name,
                    "description": branding_data.description,
                    "brand_voice": branding_data.brand_voice,
                    "brand_values": json.dumps(branding_data.brand_values),
                    "color_scheme": json.dumps(branding_data.color_scheme),
                    "logo_url": branding_data.logo_url,
                    "tagline": branding_data.tagline,
                    "company_info": json.dumps(branding_data.company_info),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Store in database (simplified for demo)
                branding_data.id = 1  # Simulate ID generation
                branding_data.created_at = branding_profile["created_at"]
                branding_data.updated_at = branding_profile["updated_at"]
                
                # Cache branding profile
                await self.redis_manager.set_cache(
                    f"branding_profile_{branding_data.id}",
                    branding_data.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "tone_branding.branding_profile_created",
                    {
                        "branding_profile_id": branding_data.id,
                        "name": branding_data.name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created branding profile: {branding_data.name}")
                return branding_data
                
            except Exception as e:
                logger.error(f"Failed to create branding profile: {e}")
                raise
    
    async def get_tone_profiles(self) -> List[ToneProfile]:
        """Get all tone profiles"""
        try:
            # Try to get from cache first
            cached_profiles = await self.redis_manager.get_cache("all_tone_profiles")
            if cached_profiles:
                return [ToneProfile(**profile) for profile in cached_profiles]
            
            # Get from database (simplified for demo)
            profiles = [
                ToneProfile(
                    id=1,
                    name="Professional Formal",
                    description="Formal and professional tone for enterprise clients",
                    tone_characteristics={
                        "formality": "high",
                        "confidence": "high",
                        "empathy": "medium",
                        "enthusiasm": "low"
                    },
                    language_style="formal",
                    formality_level="high",
                    personality_traits=["professional", "confident", "reliable"],
                    industry_specific=True,
                    target_audience=["enterprise", "executives"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                ToneProfile(
                    id=2,
                    name="Friendly Casual",
                    description="Casual and friendly tone for small businesses",
                    tone_characteristics={
                        "formality": "low",
                        "confidence": "medium",
                        "empathy": "high",
                        "enthusiasm": "high"
                    },
                    language_style="casual",
                    formality_level="low",
                    personality_traits=["friendly", "approachable", "helpful"],
                    industry_specific=False,
                    target_audience=["small_business", "startups"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            # Cache profiles
            await self.redis_manager.set_cache(
                "all_tone_profiles",
                [profile.dict() for profile in profiles],
                expire=3600  # 1 hour
            )
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to get tone profiles: {e}")
            raise
    
    async def get_branding_profiles(self) -> List[BrandingProfile]:
        """Get all branding profiles"""
        try:
            # Try to get from cache first
            cached_profiles = await self.redis_manager.get_cache("all_branding_profiles")
            if cached_profiles:
                return [BrandingProfile(**profile) for profile in cached_profiles]
            
            # Get from database (simplified for demo)
            profiles = [
                BrandingProfile(
                    id=1,
                    name="Enterprise Brand",
                    description="Professional branding for enterprise clients",
                    brand_voice="authoritative and trustworthy",
                    brand_values=["reliability", "innovation", "excellence"],
                    color_scheme={
                        "primary": "#1a365d",
                        "secondary": "#2d3748",
                        "accent": "#3182ce"
                    },
                    logo_url="https://example.com/enterprise-logo.png",
                    tagline="Driving Business Excellence",
                    company_info={
                        "name": "Enterprise Solutions Inc",
                        "industry": "Technology",
                        "founded": "2010"
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                BrandingProfile(
                    id=2,
                    name="Startup Brand",
                    description="Modern and innovative branding for startups",
                    brand_voice="innovative and approachable",
                    brand_values=["innovation", "growth", "collaboration"],
                    color_scheme={
                        "primary": "#38a169",
                        "secondary": "#48bb78",
                        "accent": "#68d391"
                    },
                    logo_url="https://example.com/startup-logo.png",
                    tagline="Building the Future Together",
                    company_info={
                        "name": "Innovation Labs",
                        "industry": "Technology",
                        "founded": "2020"
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ]
            
            # Cache profiles
            await self.redis_manager.set_cache(
                "all_branding_profiles",
                [profile.dict() for profile in profiles],
                expire=3600  # 1 hour
            )
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to get branding profiles: {e}")
            raise
    
    async def update_tone_profile(self, profile_id: int, updates: Dict[str, Any]) -> ToneProfile:
        """Update an existing tone profile"""
        async with get_eric_database() as session:
            try:
                # Get existing profile
                profiles = await self.get_tone_profiles()
                profile = next((p for p in profiles if p.id == profile_id), None)
                
                if not profile:
                    raise ValueError(f"Tone profile with ID {profile_id} not found")
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(profile, field):
                        setattr(profile, field, value)
                
                profile.updated_at = datetime.utcnow()
                
                # Update cache
                await self.redis_manager.set_cache(
                    f"tone_profile_{profile_id}",
                    profile.dict(),
                    expire=86400  # 24 hours
                )
                
                # Clear all profiles cache
                await self.redis_manager.delete_cache("all_tone_profiles")
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "tone_branding.tone_profile_updated",
                    {
                        "tone_profile_id": profile_id,
                        "updates": updates,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Updated tone profile: {profile.name}")
                return profile
                
            except Exception as e:
                logger.error(f"Failed to update tone profile: {e}")
                raise
    
    async def update_branding_profile(self, profile_id: int, updates: Dict[str, Any]) -> BrandingProfile:
        """Update an existing branding profile"""
        async with get_eric_database() as session:
            try:
                # Get existing profile
                profiles = await self.get_branding_profiles()
                profile = next((p for p in profiles if p.id == profile_id), None)
                
                if not profile:
                    raise ValueError(f"Branding profile with ID {profile_id} not found")
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(profile, field):
                        setattr(profile, field, value)
                
                profile.updated_at = datetime.utcnow()
                
                # Update cache
                await self.redis_manager.set_cache(
                    f"branding_profile_{profile_id}",
                    profile.dict(),
                    expire=86400  # 24 hours
                )
                
                # Clear all profiles cache
                await self.redis_manager.delete_cache("all_branding_profiles")
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "tone_branding.branding_profile_updated",
                    {
                        "branding_profile_id": profile_id,
                        "updates": updates,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Updated branding profile: {profile.name}")
                return profile
                
            except Exception as e:
                logger.error(f"Failed to update branding profile: {e}")
                raise
    
    async def delete_tone_profile(self, profile_id: int) -> bool:
        """Delete a tone profile"""
        try:
            # Get existing profile
            profiles = await self.get_tone_profiles()
            profile = next((p for p in profiles if p.id == profile_id), None)
            
            if not profile:
                raise ValueError(f"Tone profile with ID {profile_id} not found")
            
            # Delete from cache
            await self.redis_manager.delete_cache(f"tone_profile_{profile_id}")
            await self.redis_manager.delete_cache("all_tone_profiles")
            
            # Publish event
            await self.kafka_manager.publish_event(
                "tone_branding.tone_profile_deleted",
                {
                    "tone_profile_id": profile_id,
                    "name": profile.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Deleted tone profile: {profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tone profile: {e}")
            raise
    
    async def delete_branding_profile(self, profile_id: int) -> bool:
        """Delete a branding profile"""
        try:
            # Get existing profile
            profiles = await self.get_branding_profiles()
            profile = next((p for p in profiles if p.id == profile_id), None)
            
            if not profile:
                raise ValueError(f"Branding profile with ID {profile_id} not found")
            
            # Delete from cache
            await self.redis_manager.delete_cache(f"branding_profile_{profile_id}")
            await self.redis_manager.delete_cache("all_branding_profiles")
            
            # Publish event
            await self.kafka_manager.publish_event(
                "tone_branding.branding_profile_deleted",
                {
                    "branding_profile_id": profile_id,
                    "name": profile.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Deleted branding profile: {profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete branding profile: {e}")
            raise
    
    async def apply_tone_branding_to_content(self, content: str, tone_profile_id: int, branding_profile_id: int) -> str:
        """Apply tone and branding to content"""
        try:
            # Get profiles
            tone_profiles = await self.get_tone_profiles()
            branding_profiles = await self.get_branding_profiles()
            
            tone_profile = next((p for p in tone_profiles if p.id == tone_profile_id), None)
            branding_profile = next((p for p in branding_profiles if p.id == branding_profile_id), None)
            
            if not tone_profile:
                raise ValueError(f"Tone profile with ID {tone_profile_id} not found")
            if not branding_profile:
                raise ValueError(f"Branding profile with ID {branding_profile_id} not found")
            
            # Apply tone characteristics
            modified_content = self._apply_tone_characteristics(content, tone_profile)
            
            # Apply branding elements
            modified_content = self._apply_branding_elements(modified_content, branding_profile)
            
            # Publish event
            await self.kafka_manager.publish_event(
                "tone_branding.content_modified",
                {
                    "tone_profile_id": tone_profile_id,
                    "branding_profile_id": branding_profile_id,
                    "original_length": len(content),
                    "modified_length": len(modified_content),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Applied tone and branding to content")
            return modified_content
            
        except Exception as e:
            logger.error(f"Failed to apply tone and branding: {e}")
            raise
    
    async def get_tone_branding_analytics(self) -> Dict[str, Any]:
        """Get analytics for tone and branding usage"""
        try:
            # Get usage statistics
            tone_profiles = await self.get_tone_profiles()
            branding_profiles = await self.get_branding_profiles()
            
            analytics = {
                "total_tone_profiles": len(tone_profiles),
                "total_branding_profiles": len(branding_profiles),
                "most_used_tone": "Professional Formal",  # Simplified
                "most_used_branding": "Enterprise Brand",  # Simplified
                "content_modifications_today": 25,  # Simplified
                "content_modifications_this_week": 150,  # Simplified
                "average_content_length": 250,  # Simplified
                "popular_combinations": [
                    {
                        "tone": "Professional Formal",
                        "branding": "Enterprise Brand",
                        "usage_count": 45
                    },
                    {
                        "tone": "Friendly Casual",
                        "branding": "Startup Brand",
                        "usage_count": 32
                    }
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get tone branding analytics: {e}")
            raise
    
    def _validate_tone_characteristics(self, characteristics: Dict[str, Any]) -> bool:
        """Validate tone characteristics"""
        required_fields = ["formality", "confidence", "empathy", "enthusiasm"]
        valid_levels = ["low", "medium", "high"]
        
        for field in required_fields:
            if field not in characteristics:
                return False
            if characteristics[field] not in valid_levels:
                return False
        
        return True
    
    def _validate_branding_data(self, branding: BrandingProfile) -> bool:
        """Validate branding data"""
        if not branding.name or not branding.brand_voice:
            return False
        
        if not branding.brand_values or len(branding.brand_values) == 0:
            return False
        
        if not branding.color_scheme or len(branding.color_scheme) == 0:
            return False
        
        return True
    
    def _apply_tone_characteristics(self, content: str, tone_profile: ToneProfile) -> str:
        """Apply tone characteristics to content"""
        # Simplified tone application logic
        characteristics = tone_profile.tone_characteristics
        
        if characteristics.get("formality") == "high":
            # Make content more formal
            content = content.replace("Hi", "Hello")
            content = content.replace("Thanks", "Thank you")
            content = content.replace("You're", "You are")
        
        if characteristics.get("confidence") == "high":
            # Add confident language
            content = content.replace("might", "will")
            content = content.replace("could", "can")
        
        if characteristics.get("empathy") == "high":
            # Add empathetic language
            content = content.replace("I understand", "I completely understand")
            content = content.replace("your needs", "your unique needs")
        
        return content
    
    def _apply_branding_elements(self, content: str, branding_profile: BrandingProfile) -> str:
        """Apply branding elements to content"""
        # Add brand tagline if not present
        if branding_profile.tagline and branding_profile.tagline not in content:
            content += f"\n\n{branding_profile.tagline}"
        
        # Add company name if not present
        company_name = branding_profile.company_info.get("name", "")
        if company_name and company_name not in content:
            content = content.replace("our company", company_name)
        
        return content
