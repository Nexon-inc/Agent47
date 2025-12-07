import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import BusinessIdea, CustomerAvatar, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
from ..core.kafka_manager import KafkaManager
from ..core.redis_manager import RedisManager
from ..core.integration_manager import IntegrationManager
from ..core.platform_manager import PlatformManager

class CustomerAvatarService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()

    async def create_customer_avatar(
        self,
        db: AsyncSession,
        business_idea: str,
        target_market: str,
        demographics: Dict[str, Any],
        psychographics: Dict[str, Any],
        pain_points: List[str],
        goals: List[str],
        buying_behavior: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            cache_key = f"customer_avatar:{business_idea[:50]}:{target_market}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            prompt = f"""
            Create a detailed customer avatar for a business idea: {business_idea}
            Target Market: {target_market}
            Demographics: {demographics}
            Psychographics: {psychographics}
            Pain Points: {pain_points}
            Goals: {goals}
            Buying Behavior: {buying_behavior}

            Provide comprehensive customer avatar including:
            1. Persona details
            2. Demographics analysis
            3. Psychographics profile
            4. Pain points and challenges
            5. Goals and aspirations
            6. Buying behavior patterns
            7. Communication preferences
            8. Marketing insights

            Return the response as a JSON object with the following structure:
            {{
                "persona_name": "Sarah Johnson",
                "age_range": "28-35",
                "occupation": "Marketing Manager",
                "income_level": "$60K-$80K",
                "location": "Urban areas",
                "education": "Bachelor's degree",
                "family_status": "Single, no children",
                "lifestyle": "Busy professional, health-conscious",
                "values": ["Efficiency", "Quality", "Sustainability"],
                "interests": ["Technology", "Fitness", "Travel"],
                "pain_points": [
                    "Limited time for personal tasks",
                    "Difficulty finding quality products",
                    "Budget constraints"
                ],
                "goals": [
                    "Advance career",
                    "Maintain work-life balance",
                    "Save money"
                ],
                "buying_behavior": {{
                    "decision_factors": ["Quality", "Convenience", "Price"],
                    "research_methods": ["Online reviews", "Social media", "Word of mouth"],
                    "purchase_frequency": "Monthly",
                    "budget_allocation": "Moderate",
                    "brand_preferences": "Established brands with good reviews"
                }},
                "communication_preferences": {{
                    "channels": ["Email", "Social media", "Mobile apps"],
                    "tone": "Professional but friendly",
                    "frequency": "Weekly",
                    "content_type": ["Educational", "Promotional", "Community"]
                }},
                "marketing_insights": [
                    "Responds well to time-saving solutions",
                    "Values social proof and reviews",
                    "Prefers mobile-first experiences",
                    "Appreciates personalized recommendations"
                ],
                "avatar_score": 85.5
            }}
            """

            avatar_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            customer_avatar = {
                "id": f"avatar_{business_idea[:30]}",
                "business_idea": business_idea,
                "target_market": target_market,
                "persona_name": avatar_data.get("persona_name", ""),
                "demographics": demographics,
                "psychographics": psychographics,
                "pain_points": pain_points,
                "goals": goals,
                "buying_behavior": buying_behavior,
                "avatar_details": avatar_data,
                "avatar_score": avatar_data.get("avatar_score", 0),
                "created_at": datetime.utcnow()
            }

            stmt = insert(CustomerAvatar).values(**customer_avatar)
            await db.execute(stmt)
            await db.commit()

            await self.redis_manager.set(cache_key, json.dumps(customer_avatar), expire=3600)
            await self.event_bus.publish("purity.customer_avatar_created", {
                "business_idea": business_idea[:50],
                "target_market": target_market,
                "avatar_score": customer_avatar["avatar_score"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return customer_avatar

        except Exception as e:
            await db.rollback()
            raise Exception(f"Failed to create customer avatar: {str(e)}")

    async def analyze_customer_segments(
        self,
        db: AsyncSession,
        business_idea: str,
        market_data: Dict[str, Any],
        segmentation_criteria: List[str]
    ) -> Dict[str, Any]:
        try:
            cache_key = f"customer_segments:{business_idea[:50]}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            prompt = f"""
            Analyze customer segments for business idea: {business_idea}
            Market Data: {market_data}
            Segmentation Criteria: {segmentation_criteria}

            Provide comprehensive customer segmentation including:
            1. Primary segments
            2. Secondary segments
            3. Segment characteristics
            4. Market size estimates
            5. Targeting strategies

            Return the response as a JSON object with the following structure:
            {{
                "primary_segments": [
                    {{
                        "segment_name": "Early Adopters",
                        "size_estimate": "2M people",
                        "characteristics": ["Tech-savvy", "High income", "Innovation-driven"],
                        "targeting_strategy": "Digital marketing, influencer partnerships"
                    }}
                ],
                "secondary_segments": [
                    {{
                        "segment_name": "Mainstream Users",
                        "size_estimate": "8M people",
                        "characteristics": ["Practical", "Value-conscious", "Social proof seekers"],
                        "targeting_strategy": "Traditional advertising, word-of-mouth"
                    }}
                ],
                "segment_priorities": [
                    "Primary: Early Adopters (High value, low acquisition cost)",
                    "Secondary: Mainstream Users (Large market, higher acquisition cost)"
                ],
                "total_addressable_market": "10M people",
                "segmentation_score": 88.0
            }}
            """

            segment_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            segment_analysis = {
                "id": f"segments_{business_idea[:30]}",
                "business_idea": business_idea,
                "market_data": market_data,
                "segmentation_criteria": segmentation_criteria,
                "segment_analysis": segment_data,
                "total_addressable_market": segment_data.get("total_addressable_market", ""),
                "segmentation_score": segment_data.get("segmentation_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.redis_manager.set(cache_key, json.dumps(segment_analysis), expire=3600)
            await self.event_bus.publish("purity.customer_segments_analyzed", {
                "business_idea": business_idea[:50],
                "segment_count": len(segment_data.get("primary_segments", [])) + len(segment_data.get("secondary_segments", [])),
                "timestamp": datetime.utcnow().isoformat()
            })

            return segment_analysis

        except Exception as e:
            raise Exception(f"Failed to analyze customer segments: {str(e)}")

    async def generate_marketing_personas(
        self,
        db: AsyncSession,
        customer_avatar_id: str,
        marketing_channels: List[str],
        campaign_objectives: List[str]
    ) -> Dict[str, Any]:
        try:
            cache_key = f"marketing_personas:{customer_avatar_id}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            stmt = select(CustomerAvatar).where(CustomerAvatar.id == customer_avatar_id)
            result = await db.execute(stmt)
            avatar = result.scalar_one_or_none()

            if not avatar:
                raise Exception("Customer avatar not found")

            prompt = f"""
            Generate marketing personas based on customer avatar:
            Avatar Details: {avatar.avatar_details}
            Marketing Channels: {marketing_channels}
            Campaign Objectives: {campaign_objectives}

            Provide comprehensive marketing personas including:
            1. Channel-specific personas
            2. Messaging strategies
            3. Content recommendations
            4. Engagement tactics

            Return the response as a JSON object with the following structure:
            {{
                "channel_personas": [
                    {{
                        "channel": "Social Media",
                        "persona_name": "Social Sarah",
                        "messaging_tone": "Casual and engaging",
                        "content_types": ["Visual posts", "Stories", "Live videos"],
                        "engagement_tactics": ["User-generated content", "Influencer partnerships"]
                    }}
                ],
                "messaging_strategies": [
                    "Emphasize time-saving benefits",
                    "Highlight quality and convenience",
                    "Use social proof and testimonials"
                ],
                "content_recommendations": [
                    "Educational blog posts",
                    "Product demonstration videos",
                    "Customer success stories"
                ],
                "engagement_tactics": [
                    "Interactive polls and surveys",
                    "Exclusive offers for followers",
                    "Community building activities"
                ],
                "persona_score": 82.5
            }}
            """

            persona_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            marketing_personas = {
                "id": f"marketing_personas_{customer_avatar_id}",
                "customer_avatar_id": customer_avatar_id,
                "marketing_channels": marketing_channels,
                "campaign_objectives": campaign_objectives,
                "persona_data": persona_data,
                "persona_score": persona_data.get("persona_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.redis_manager.set(cache_key, json.dumps(marketing_personas), expire=3600)
            await self.event_bus.publish("purity.marketing_personas_generated", {
                "customer_avatar_id": customer_avatar_id,
                "channel_count": len(marketing_channels),
                "persona_score": marketing_personas["persona_score"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return marketing_personas

        except Exception as e:
            raise Exception(f"Failed to generate marketing personas: {str(e)}")

    async def validate_customer_avatar(
        self,
        db: AsyncSession,
        customer_avatar_id: str,
        validation_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            stmt = select(CustomerAvatar).where(CustomerAvatar.id == customer_avatar_id)
            result = await db.execute(stmt)
            avatar = result.scalar_one_or_none()

            if not avatar:
                raise Exception("Customer avatar not found")

            prompt = f"""
            Validate customer avatar against criteria:
            Avatar Details: {avatar.avatar_details}
            Validation Criteria: {validation_criteria}

            Provide comprehensive validation including:
            1. Avatar completeness
            2. Market alignment
            3. Targeting accuracy
            4. Actionability

            Return the response as a JSON object with the following structure:
            {{
                "completeness_score": 90.0,
                "market_alignment": "High",
                "targeting_accuracy": "Strong",
                "actionability": "Excellent",
                "validation_issues": [
                    "Consider adding more specific pain points",
                    "Include preferred communication channels"
                ],
                "improvement_suggestions": [
                    "Add more demographic details",
                    "Include buying journey stages"
                ],
                "overall_validation_score": 87.5
            }}
            """

            validation_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            validation_result = {
                "id": f"validation_{customer_avatar_id}",
                "customer_avatar_id": customer_avatar_id,
                "validation_criteria": validation_criteria,
                "validation_data": validation_data,
                "overall_score": validation_data.get("overall_validation_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.event_bus.publish("purity.customer_avatar_validated", {
                "customer_avatar_id": customer_avatar_id,
                "validation_score": validation_result["overall_score"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return validation_result

        except Exception as e:
            raise Exception(f"Failed to validate customer avatar: {str(e)}")
