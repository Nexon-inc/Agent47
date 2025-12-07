from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..database import get_eric_database
# NLPUtils removed - not used
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.analytics.analytics_manager import AnalyticsManager
from backend.core.event_bus.kafka_manager import EventBus as KafkaManager
from backend.core.cache.redis_manager import RedisManager
from ..models import Lead, Deal, SalesActivity, SalesRep, CustomerProfile

logger = logging.getLogger(__name__)

class AutoPitchGeneratorService:
    """Service for generating automated sales pitches in different styles"""
    
    def __init__(self):
        # NLPUtils removed - not used in this service
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize auto pitch generator service"""
        if self._initialized:
            return
        
        try:
            from backend.core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.analytics_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Auto pitch generator service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize auto pitch generator service: {e}")
            raise
        
        # Define pitch styles with characteristics
        self.pitch_styles = {
            "bold": {
                "tone": "confident and assertive",
                "language": "powerful, direct, action-oriented",
                "structure": "problem-solution-benefit",
                "call_to_action": "urgent and compelling"
            },
            "formal": {
                "tone": "professional and authoritative",
                "language": "business-focused, data-driven",
                "structure": "logical progression with evidence",
                "call_to_action": "measured and professional"
            },
            "gen_z": {
                "tone": "casual and relatable",
                "language": "trendy, emoji-friendly, authentic",
                "structure": "story-driven with social proof",
                "call_to_action": "fun and engaging"
            },
            "consultative": {
                "tone": "helpful and educational",
                "language": "insightful, problem-focused",
                "structure": "discovery-solution-partnership",
                "call_to_action": "collaborative and consultative"
            },
            "storytelling": {
                "tone": "narrative and emotional",
                "language": "descriptive, relatable, memorable",
                "structure": "hero's journey with transformation",
                "call_to_action": "inspirational and aspirational"
            }
        }
    
    async def generate_pitch(
        self,
        lead_id: int,
        style: str,
        format_type: str,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a sales pitch in the specified style and format"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get lead information
                lead = await self._get_lead_with_context(session, lead_id)
                if not lead:
                    return {"success": False, "error": "Lead not found"}
                
                # Validate style
                if style not in self.pitch_styles:
                    return {"success": False, "error": f"Invalid pitch style: {style}"}
                
                # Get customer profile for personalization
                customer_profile = await self._get_customer_profile(session, lead.customer_id)
                
                # Generate pitch content
                pitch_content = await self._generate_pitch_content(
                    lead, customer_profile, style, format_type, custom_context
                )
                
                # Store pitch generation activity
                await self._store_pitch_activity(session, lead_id, style, format_type, pitch_content)
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "pitch_generated",
                    {
                        "lead_id": lead_id,
                        "style": style,
                        "format": format_type,
                        "lead_source": lead.source,
                        "lead_stage": lead.stage
                    }
                )
                
                return {
                    "success": True,
                    "pitch": pitch_content,
                    "style": style,
                    "format": format_type,
                    "generated_at": datetime.utcnow().isoformat(),
                    "lead_context": {
                        "name": lead.name,
                        "company": lead.company,
                        "source": lead.source,
                        "stage": lead.stage
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating pitch: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_bulk_pitches(
        self,
        lead_ids: List[int],
        style: str,
        format_type: str,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate pitches for multiple leads"""
        try:
            results = []
            for lead_id in lead_ids:
                result = await self.generate_pitch(lead_id, style, format_type, custom_context)
                results.append({
                    "lead_id": lead_id,
                    "result": result
                })
            
            # Track bulk generation analytics
            await self.analytics_manager.log_event(
                "bulk_pitches_generated",
                {
                    "lead_count": len(lead_ids),
                    "style": style,
                    "format": format_type,
                    "success_count": len([r for r in results if r["result"]["success"]])
                }
            )
            
            return {
                "success": True,
                "results": results,
                "total_leads": len(lead_ids),
                "successful_generations": len([r for r in results if r["result"]["success"]])
            }
            
        except Exception as e:
            logger.error(f"Error generating bulk pitches: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pitch_templates(
        self,
        industry: Optional[str] = None,
        use_case: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get pitch templates for different industries and use cases"""
        try:
            # Get templates from cache or database
            cache_key = f"pitch_templates:{industry}:{use_case}"
            cached_templates = await self.redis_manager.get(cache_key)
            
            if cached_templates:
                return {"success": True, "templates": json.loads(cached_templates)}
            
            # Generate templates based on industry and use case
            templates = await self._generate_templates(industry, use_case)
            
            # Cache templates
            await self.redis_manager.set(cache_key, json.dumps(templates), expire=3600)
            
            return {"success": True, "templates": templates}
            
        except Exception as e:
            logger.error(f"Error getting pitch templates: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_pitch_performance(
        self,
        pitch_id: int,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the performance of a generated pitch"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Store engagement data
                await self._store_engagement_data(session, pitch_id, engagement_data)
                
                # Analyze performance metrics
                performance_metrics = await self._analyze_performance_metrics(
                    session, pitch_id, engagement_data
                )
                
                # Generate recommendations for improvement
                recommendations = await self._generate_improvement_recommendations(
                    performance_metrics, engagement_data
                )
                
                return {
                    "success": True,
                    "performance_metrics": performance_metrics,
                    "recommendations": recommendations,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing pitch performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pitch_history(
        self,
        lead_id: Optional[int] = None,
        rep_id: Optional[int] = None,
        style: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get pitch generation history with filters"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Build query filters
                filters = []
                if lead_id:
                    filters.append(SalesActivity.lead_id == lead_id)
                if rep_id:
                    filters.append(SalesActivity.rep_id == rep_id)
                if style:
                    filters.append(SalesActivity.metadata.contains({"style": style}))
                
                # Query pitch activities
                query = select(SalesActivity).where(
                    and_(
                        SalesActivity.activity_type == "pitch_generation",
                        *filters
                    )
                ).order_by(SalesActivity.created_at.desc()).limit(limit)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Format results
                pitch_history = []
                for activity in activities:
                    pitch_history.append({
                        "id": activity.id,
                        "lead_id": activity.lead_id,
                        "rep_id": activity.rep_id,
                        "style": activity.metadata.get("style"),
                        "format": activity.metadata.get("format"),
                        "generated_at": activity.created_at.isoformat(),
                        "engagement_metrics": activity.metadata.get("engagement_metrics", {})
                    })
                
                return {
                    "success": True,
                    "pitch_history": pitch_history,
                    "total_count": len(pitch_history)
                }
                
        except Exception as e:
            logger.error(f"Error getting pitch history: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_lead_with_context(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> Optional[Lead]:
        """Get lead with full context for pitch generation"""
        query = select(Lead).where(Lead.id == lead_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_customer_profile(
        self,
        session: AsyncSession,
        customer_id: int
    ) -> Optional[CustomerProfile]:
        """Get customer profile for personalization"""
        query = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _generate_pitch_content(
        self,
        lead: Lead,
        customer_profile: Optional[CustomerProfile],
        style: str,
        format_type: str,
        custom_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate pitch content based on style and format"""
        style_config = self.pitch_styles[style]
        
        # Build context for pitch generation
        context = {
            "lead_name": lead.name,
            "company": lead.company,
            "industry": lead.industry,
            "source": lead.source,
            "stage": lead.stage,
            "pain_points": lead.pain_points,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "style_config": style_config,
            "format_type": format_type
        }
        
        if customer_profile:
            context.update({
                "customer_industry": customer_profile.industry,
                "customer_size": customer_profile.company_size,
                "customer_location": customer_profile.location
            })
        
        if custom_context:
            context.update(custom_context)
        
        # Generate pitch using NLP utils
        pitch_prompt = self._build_pitch_prompt(context, style)
        # Use AI Service Manager instead of NLPUtils
        from backend.core.ai import get_ai_service_manager
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that generates sales pitches."},
            {"role": "user", "content": pitch_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        pitch_content = ai_response.text_content if ai_response.success else ""
        
        # Format based on type (text/voice)
        if format_type == "voice":
            formatted_pitch = self._format_for_voice(pitch_content, style)
        else:
            formatted_pitch = self._format_for_text(pitch_content, style)
        
        return {
            "content": formatted_pitch,
            "style": style,
            "format": format_type,
            "word_count": len(formatted_pitch.split()),
            "estimated_duration": self._estimate_duration(formatted_pitch, format_type)
        }
    
    async def _generate_templates(
        self,
        industry: Optional[str],
        use_case: Optional[str]
    ) -> Dict[str, Any]:
        """Generate pitch templates for different scenarios"""
        templates = {}
        
        for style in self.pitch_styles.keys():
            templates[style] = {
                "cold_outreach": await self._generate_template_prompt(style, "cold_outreach", industry),
                "follow_up": await self._generate_template_prompt(style, "follow_up", industry),
                "demo_request": await self._generate_template_prompt(style, "demo_request", industry),
                "closing": await self._generate_template_prompt(style, "closing", industry)
            }
        
        return templates
    
    async def _generate_template_prompt(
        self,
        style: str,
        use_case: str,
        industry: Optional[str]
    ) -> str:
        """Generate a template prompt for specific use case"""
        base_prompt = f"Create a {style} style pitch for {use_case}"
        if industry:
            base_prompt += f" in the {industry} industry"
        
        # Use AI Service Manager instead of NLPUtils
        from backend.core.ai import get_ai_service_manager
        ai_manager = await get_ai_service_manager()
        messages = [
            {"role": "system", "content": "You are an AI assistant that generates sales pitch templates."},
            {"role": "user", "content": base_prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    def _build_pitch_prompt(self, context: Dict[str, Any], style: str) -> str:
        """Build a comprehensive prompt for pitch generation"""
        style_config = self.pitch_styles[style]
        
        prompt = f"""
        Generate a {style} sales pitch with the following characteristics:
        - Tone: {style_config['tone']}
        - Language: {style_config['language']}
        - Structure: {style_config['structure']}
        - Call to Action: {style_config['call_to_action']}
        
        Lead Context:
        - Name: {context.get('lead_name', 'Prospect')}
        - Company: {context.get('company', 'Unknown')}
        - Industry: {context.get('industry', 'General')}
        - Source: {context.get('source', 'Unknown')}
        - Stage: {context.get('stage', 'Prospecting')}
        - Pain Points: {context.get('pain_points', 'Not specified')}
        - Budget: {context.get('budget', 'Not specified')}
        - Timeline: {context.get('timeline', 'Not specified')}
        
        Create a compelling, personalized pitch that addresses their specific needs and follows the {style} style guidelines.
        """
        
        return prompt
    
    def _format_for_voice(self, content: str, style: str) -> str:
        """Format pitch content for voice delivery"""
        # Add voice-specific formatting
        if style == "gen_z":
            # Add pauses and emphasis for Gen Z style
            content = content.replace(".", "... ")
            content = content.replace("!", "! ")
        elif style == "storytelling":
            # Add dramatic pauses for storytelling
            content = content.replace(".", ". [pause] ")
        
        return content
    
    def _format_for_text(self, content: str, style: str) -> str:
        """Format pitch content for text delivery"""
        # Add text-specific formatting
        if style == "gen_z":
            # Add emojis and formatting for Gen Z
            content = content.replace("!", "! 🚀")
            content = content.replace("?", "? 🤔")
        elif style == "formal":
            # Ensure proper business formatting
            content = content.replace("\n", "\n\n")
        
        return content
    
    def _estimate_duration(self, content: str, format_type: str) -> int:
        """Estimate delivery duration in seconds"""
        word_count = len(content.split())
        
        if format_type == "voice":
            # Average speaking rate: 150 words per minute
            return int((word_count / 150) * 60)
        else:
            # Average reading rate: 200 words per minute
            return int((word_count / 200) * 60)
    
    async def _store_pitch_activity(
        self,
        session: AsyncSession,
        lead_id: int,
        style: str,
        format_type: str,
        pitch_content: Dict[str, Any]
    ) -> None:
        """Store pitch generation activity"""
        activity = SalesActivity(
            activity_type="pitch_generation",
            lead_id=lead_id,
            metadata={
                "style": style,
                "format": format_type,
                "content": pitch_content["content"],
                "word_count": pitch_content["word_count"],
                "estimated_duration": pitch_content["estimated_duration"]
            }
        )
        
        session.add(activity)
        await session.commit()
    
    async def _store_engagement_data(
        self,
        session: AsyncSession,
        pitch_id: int,
        engagement_data: Dict[str, Any]
    ) -> None:
        """Store engagement data for pitch performance analysis"""
        # Update the sales activity with engagement metrics
        query = select(SalesActivity).where(SalesActivity.id == pitch_id)
        activity = await session.execute(query)
        activity = activity.scalar_one_or_none()
        
        if activity:
            current_metadata = activity.metadata or {}
            current_metadata["engagement_metrics"] = engagement_data
            activity.metadata = current_metadata
            await session.commit()
    
    async def _analyze_performance_metrics(
        self,
        session: AsyncSession,
        pitch_id: int,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze performance metrics for the pitch"""
        metrics = {
            "open_rate": engagement_data.get("opened", False),
            "response_rate": engagement_data.get("responded", False),
            "engagement_score": 0,
            "conversion_likelihood": 0
        }
        
        # Calculate engagement score
        score = 0
        if engagement_data.get("opened"):
            score += 30
        if engagement_data.get("responded"):
            score += 50
        if engagement_data.get("clicked"):
            score += 20
        
        metrics["engagement_score"] = score
        
        # Calculate conversion likelihood based on engagement
        if score >= 80:
            metrics["conversion_likelihood"] = "high"
        elif score >= 50:
            metrics["conversion_likelihood"] = "medium"
        else:
            metrics["conversion_likelihood"] = "low"
        
        return metrics
    
    async def _generate_improvement_recommendations(
        self,
        performance_metrics: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for pitch improvement"""
        recommendations = []
        
        if performance_metrics["engagement_score"] < 50:
            recommendations.append("Consider using a more personalized opening")
            recommendations.append("Add social proof or testimonials")
            recommendations.append("Include a clear value proposition")
        
        if not engagement_data.get("opened"):
            recommendations.append("Revise subject line to be more compelling")
            recommendations.append("Send at optimal time for the prospect")
        
        if engagement_data.get("opened") and not engagement_data.get("responded"):
            recommendations.append("Simplify the call-to-action")
            recommendations.append("Add urgency or scarcity elements")
            recommendations.append("Follow up with a different approach")
        
        return recommendations
