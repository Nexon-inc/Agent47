import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc

from core.ai import get_ai_service_manager, AIServiceManager
from core.cache.redis_manager import init_redis
from core.storage.chroma_manager import ChromaManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..models import EricLead, EricLeadInteraction, LeadSource, LeadStatus
from ..database import get_eric_database

logger = logging.getLogger(__name__)

class LeadGenerationService:
    """Service for lead generation and qualification"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self.chroma_manager = None
        self.integration_manager = None
        self.platform_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize lead generation service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self.chroma_manager = ChromaManager()
            await self.chroma_manager.initialize()
            self.integration_manager = IntegrationManager()
            await self.integration_manager.initialize()
            self.platform_manager = PlatformManager()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("Eric lead generation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize lead generation service: {e}")
            raise
    
    async def identify_leads_from_website(
        self,
        brand_id: int,
        website_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify leads from website analytics and forms"""
        try:
            await self.initialize()
            
            leads = []
            website_visitors = website_data.get("visitors", [])
            
            for visitor in website_visitors:
                if visitor.get("conversion_score", 0) > 0.7:
                    lead_data = {
                        "brand_id": brand_id,
                        "first_name": visitor.get("first_name", "Unknown"),
                        "last_name": visitor.get("last_name", "Unknown"),
                        "email": visitor.get("email"),
                        "phone": visitor.get("phone"),
                        "company": visitor.get("company"),
                        "job_title": visitor.get("job_title"),
                        "industry": visitor.get("industry"),
                        "lead_source": LeadSource.WEBSITE,
                        "lead_score": visitor.get("conversion_score", 0.0),
                        "pain_points": visitor.get("pain_points"),
                        "requirements": visitor.get("requirements"),
                        "location": visitor.get("location"),
                        "timezone": visitor.get("timezone"),
                        "language": visitor.get("language", "en"),
                        "website_activity": {
                            "pages_visited": visitor.get("pages_visited", []),
                            "time_spent": visitor.get("time_spent", 0),
                            "conversion_event": visitor.get("conversion_event")
                        }
                    }
                    
                    if lead_data["email"]:
                        leads.append(lead_data)
            
            return {
                "success": True,
                "leads_identified": len(leads),
                "leads": leads
            }
            
        except Exception as e:
            logger.error(f"Failed to identify leads from website: {e}")
            return {
                "success": False,
                "error": f"Failed to identify leads from website: {str(e)}"
            }
    
    async def identify_leads_from_social_media(
        self,
        brand_id: int,
        platform: str,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify leads from social media engagement"""
        try:
            await self.initialize()
            
            leads = []
            engagements = engagement_data.get("engagements", [])
            
            for engagement in engagements:
                if engagement.get("engagement_score", 0) > 0.6:
                    user_data = engagement.get("user", {})
                    
                    lead_data = {
                        "brand_id": brand_id,
                        "first_name": user_data.get("first_name", "Unknown"),
                        "last_name": user_data.get("last_name", "Unknown"),
                        "email": user_data.get("email"),
                        "phone": user_data.get("phone"),
                        "company": user_data.get("company"),
                        "job_title": user_data.get("job_title"),
                        "industry": user_data.get("industry"),
                        "lead_source": LeadSource.SOCIAL_MEDIA,
                        "lead_score": engagement.get("engagement_score", 0.0),
                        "social_profiles": {
                            platform: user_data.get("profile_url")
                        },
                        "engagement_history": {
                            "platform": platform,
                            "engagement_type": engagement.get("type"),
                            "engagement_score": engagement.get("engagement_score")
                        }
                    }
                    
                    if lead_data["email"] or user_data.get("profile_url"):
                        leads.append(lead_data)
            
            return {
                "success": True,
                "leads_identified": len(leads),
                "platform": platform,
                "leads": leads
            }
            
        except Exception as e:
            logger.error(f"Failed to identify leads from social media: {e}")
            return {
                "success": False,
                "error": f"Failed to identify leads from social media: {str(e)}"
            }
    
    async def qualify_lead(
        self,
        lead_id: int,
        qualification_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Qualify a lead based on criteria"""
        try:
            await self.initialize()
            
            db = await get_eric_database()
            async with db.get_session() as session:
                lead = session.query(EricLead).filter(EricLead.id == lead_id).first()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "EricLead not found"
                    }
                
                qualification_score = 0.0
                criteria_met = []
                
                # Budget qualification
                if lead.budget and lead.budget >= qualification_criteria.get("min_budget", 0):
                    qualification_score += 0.3
                    criteria_met.append("budget")
                
                # Authority qualification
                if lead.job_title and any(title in lead.job_title.lower() for title in ["manager", "director", "vp", "ceo", "founder"]):
                    qualification_score += 0.3
                    criteria_met.append("authority")
                
                # Need qualification
                if lead.pain_points and len(lead.pain_points.split()) > 10:
                    qualification_score += 0.2
                    criteria_met.append("need")
                
                # Timeline qualification
                if lead.timeline and lead.timeline in ["immediate", "this month", "next month"]:
                    qualification_score += 0.2
                    criteria_met.append("timeline")
                
                # Update lead score and status
                lead.lead_score = qualification_score
                if qualification_score >= 0.7:
                    lead.lead_status = LeadStatus.QUALIFIED
                elif qualification_score >= 0.4:
                    lead.lead_status = LeadStatus.CONTACTED
                else:
                    lead.lead_status = LeadStatus.NEW
                
                await session.commit()
            
            return {
                "success": True,
                "lead_id": lead_id,
                "qualification_score": qualification_score,
                "criteria_met": criteria_met,
                "lead_status": lead.lead_status.value,
                "recommendations": self._get_qualification_recommendations(qualification_score, criteria_met)
            }
            
        except Exception as e:
            logger.error(f"Failed to qualify lead: {e}")
            return {
                "success": False,
                "error": f"Failed to qualify lead: {str(e)}"
            }
    
    async def score_lead_intent(
        self,
        lead_id: int,
        intent_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score lead based on intent signals"""
        try:
            await self.initialize()
            
            db = await get_eric_database()
            async with db.get_session() as session:
                lead = session.query(EricLead).filter(EricLead.id == lead_id).first()
                
                if not lead:
                    return {
                        "success": False,
                        "error": "EricLead not found"
                    }
                
                intent_score = 0.0
                signals_detected = []
                
                # Website activity signals
                website_activity = intent_signals.get("website_activity", {})
                if website_activity.get("pricing_page_visits", 0) > 0:
                    intent_score += 0.2
                    signals_detected.append("pricing_interest")
                
                if website_activity.get("demo_page_visits", 0) > 0:
                    intent_score += 0.3
                    signals_detected.append("demo_interest")
                
                if website_activity.get("contact_page_visits", 0) > 0:
                    intent_score += 0.2
                    signals_detected.append("contact_interest")
                
                # Email engagement signals
                email_activity = intent_signals.get("email_activity", {})
                if email_activity.get("opens", 0) > 2:
                    intent_score += 0.1
                    signals_detected.append("email_engagement")
                
                if email_activity.get("clicks", 0) > 0:
                    intent_score += 0.2
                    signals_detected.append("email_clicks")
                
                # Social media signals
                social_activity = intent_signals.get("social_activity", {})
                if social_activity.get("profile_visits", 0) > 0:
                    intent_score += 0.1
                    signals_detected.append("social_interest")
                
                # Update lead score
                lead.lead_score = min(1.0, lead.lead_score + intent_score)
                
                # Update engagement history
                current_history = lead.engagement_history or {}
                current_history.update({
                    "intent_signals": signals_detected,
                    "intent_score": intent_score,
                    "last_updated": datetime.now().isoformat()
                })
                lead.engagement_history = current_history
                
                await session.commit()
            
            return {
                "success": True,
                "lead_id": lead_id,
                "intent_score": intent_score,
                "signals_detected": signals_detected,
                "updated_lead_score": lead.lead_score,
                "recommendations": self._get_intent_recommendations(intent_score, signals_detected)
            }
            
        except Exception as e:
            logger.error(f"Failed to score lead intent: {e}")
            return {
                "success": False,
                "error": f"Failed to score lead intent: {str(e)}"
            }
    
    async def get_lead_recommendations(
        self,
        brand_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get lead recommendations based on filters"""
        try:
            await self.initialize()
            
            db = next(get_db())
            query = db.query(EricLead).filter(EricLead.brand_id == brand_id)
            
            if filters:
                if filters.get("min_score"):
                    query = query.filter(EricLead.lead_score >= filters["min_score"])
                
                if filters.get("lead_status"):
                    query = query.filter(EricLead.lead_status == filters["lead_status"])
                
                if filters.get("lead_source"):
                    query = query.filter(EricLead.lead_source == filters["lead_source"])
                
                if filters.get("industry"):
                    query = query.filter(EricLead.industry == filters["industry"])
            
            leads = query.order_by(desc(EricLead.lead_score)).limit(50).all()
            
            recommendations = []
            for lead in leads:
                recommendations.append({
                    "lead_id": lead.id,
                    "name": f"{lead.first_name} {lead.last_name}",
                    "company": lead.company,
                    "job_title": lead.job_title,
                    "lead_score": lead.lead_score,
                    "lead_status": lead.lead_status.value,
                    "lead_source": lead.lead_source.value,
                    "last_activity": lead.updated_at.isoformat(),
                    "recommended_action": self._get_recommended_action(lead)
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total_leads": len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead recommendations: {e}")
            return {
                "success": False,
                "error": f"Failed to get lead recommendations: {str(e)}"
            }
    
    def _get_qualification_recommendations(
        self,
        qualification_score: float,
        criteria_met: List[str]
    ) -> List[str]:
        """Get recommendations based on qualification score"""
        recommendations = []
        
        if qualification_score >= 0.8:
            recommendations.append("High-priority lead - schedule immediate follow-up")
            recommendations.append("Prepare personalized proposal")
        elif qualification_score >= 0.6:
            recommendations.append("Qualified lead - add to nurture sequence")
            recommendations.append("Schedule discovery call")
        elif qualification_score >= 0.4:
            recommendations.append("Warm lead - continue nurturing")
            recommendations.append("Send educational content")
        else:
            recommendations.append("Cold lead - focus on education")
            recommendations.append("Add to long-term nurture sequence")
        
        missing_criteria = ["budget", "authority", "need", "timeline"] - set(criteria_met)
        for criterion in missing_criteria:
            recommendations.append(f"Gather more information about {criterion}")
        
        return recommendations
    
    def _get_intent_recommendations(
        self,
        intent_score: float,
        signals_detected: List[str]
    ) -> List[str]:
        """Get recommendations based on intent signals"""
        recommendations = []
        
        if intent_score >= 0.7:
            recommendations.append("High intent - immediate outreach recommended")
            recommendations.append("Prepare demo or proposal")
        elif intent_score >= 0.4:
            recommendations.append("Moderate intent - personalized follow-up")
            recommendations.append("Send case studies or testimonials")
        else:
            recommendations.append("Low intent - continue nurturing")
            recommendations.append("Focus on educational content")
        
        if "pricing_interest" in signals_detected:
            recommendations.append("Send pricing information")
        
        if "demo_interest" in signals_detected:
            recommendations.append("Offer product demo")
        
        if "contact_interest" in signals_detected:
            recommendations.append("Schedule discovery call")
        
        return recommendations
    
    def _get_recommended_action(self, lead: EricLead) -> str:
        """Get recommended action for a lead"""
        if lead.lead_score >= 0.8:
            return "Immediate follow-up call"
        elif lead.lead_score >= 0.6:
            return "Schedule discovery call"
        elif lead.lead_score >= 0.4:
            return "Send personalized email"
        else:
            return "Continue nurturing"
    
    async def _extract_criteria_from_message(self, message: str) -> Dict[str, Any]:
        """Extract lead generation criteria from user message using AI"""
        try:
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            
            extraction_prompt = f"""Extract lead generation criteria from this user message: "{message}"

Extract the following information if mentioned:
- industry (e.g., SaaS, healthcare, finance)
- role (e.g., Founder, CEO, CTO, Marketing Director)
- company_size (e.g., startup, small, medium, large, enterprise)
- location (e.g., United States, New York, California)
- count (number of leads to generate, default: 10)

Return as JSON only:
{{
  "industry": "...",
  "role": "...",
  "company_size": "...",
  "location": "...",
  "count": 10
}}

If a field is not mentioned, use null for that field."""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant that extracts structured information from user messages. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ]
            
            ai_response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            if not ai_response.success:
                return {}
            
            try:
                import json
                response_text = ai_response.text_content.strip()
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                response_text = response_text.strip()
                
                criteria = json.loads(response_text)
                # Filter out null values
                return {k: v for k, v in criteria.items() if v is not None}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse criteria extraction response: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to extract criteria from message: {e}")
            return {}
    
    def _parse_budget(self, budget_str: str) -> Optional[float]:
        """Parse budget string to float"""
        if not budget_str:
            return None
        
        try:
            # Try to extract number from strings like "$10,000-$50,000" or "10k-50k"
            import re
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', budget_str.lower())
            # Extract numbers
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            if numbers:
                # Use the first number or average if range
                if len(numbers) > 1:
                    return (float(numbers[0]) + float(numbers[1])) / 2
                return float(numbers[0])
            return None
        except (ValueError, TypeError):
            return None
    
    async def generate_leads(
        self,
        user_id: int,
        criteria: Dict[str, Any],
        db: AsyncSession,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate leads based on criteria using AI"""
        try:
            await self.initialize()
            
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            
            # Extract criteria from user message using AI if not provided
            if not criteria and user_message:
                criteria = await self._extract_criteria_from_message(user_message)
            
            # Use provided criteria or extracted criteria, no defaults
            industry = criteria.get("industry") if criteria.get("industry") else None
            target_role = criteria.get("role") if criteria.get("role") else None
            company_size = criteria.get("company_size") if criteria.get("company_size") else None
            location = criteria.get("location") if criteria.get("location") else None
            count = criteria.get("count", 10)  # Default count only
            
            # If no criteria extracted, ask user for more information
            if not any([industry, target_role, company_size, location]):
                return {
                    "success": False,
                    "error": "Please provide more details about the leads you want to generate. For example: industry, target role, company size, or location.",
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "sources": []
                }
            
            # Use AI to generate lead personas
            criteria_parts = []
            if industry:
                criteria_parts.append(f"- Industry: {industry}")
            if target_role:
                criteria_parts.append(f"- Role: {target_role}")
            if company_size:
                criteria_parts.append(f"- Company Size: {company_size}")
            if location:
                criteria_parts.append(f"- Location: {location}")
            
            criteria_text = "\n".join(criteria_parts) if criteria_parts else "General B2B leads"
            
            prompt = f"""Generate {count} qualified B2B lead personas targeting:
{criteria_text}

For each lead, provide:
- First Name
- Last Name
- Company Name
- Job Title
- Email (format: firstname.lastname@company.com)
- Industry
- Company Size
- Pain Points (3-5 key challenges)
- Budget Range
- Decision Timeline
- EricLead Score (0.0-1.0)

Return as JSON array with this structure:
[
  {{
    "first_name": "...",
    "last_name": "...",
    "company": "...",
    "job_title": "...",
    "email": "...",
    "industry": "...",
    "company_size": "...",
    "pain_points": ["...", "..."],
    "budget_range": "...",
    "timeline": "...",
    "lead_score": 0.0-1.0
  }}
]"""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert B2B lead generation specialist. Generate realistic, qualified lead personas based on the criteria provided. Return only valid JSON array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_response = await self.ai_service_manager.generate_text(
                messages=messages,
                max_tokens=3000,
                temperature=0.7
            )
            
            if not ai_response.success:
                return {
                    "success": False,
                    "error": "Failed to generate leads using AI",
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "sources": []
                }
            
            # Parse AI response
            import json
            try:
                # Extract JSON from response
                response_text = ai_response.text_content.strip()
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                response_text = response_text.strip()
                
                leads_data = json.loads(response_text)
                if not isinstance(leads_data, list):
                    leads_data = [leads_data]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response was: {response_text[:500]}")
                return {
                    "success": False,
                    "error": f"Failed to parse AI response: {str(e)}",
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "sources": []
                }
            
            # Save leads to database
            saved_leads = []
            qualified_count = 0
            sources = set()
            
            db_session = await get_eric_database()
            async with db_session.get_session() as session:
                for lead_data in leads_data:
                    try:
                        # Create lead record
                        # Note: user_id is used as brand_id for Eric agent
                        lead = EricLead(
                            brand_id=user_id,
                            first_name=lead_data.get("first_name", "Unknown"),
                            last_name=lead_data.get("last_name", "Unknown"),
                            email=lead_data.get("email", ""),
                            company=lead_data.get("company", ""),
                            job_title=lead_data.get("job_title", ""),
                            industry=lead_data.get("industry", industry),
                            lead_source=LeadSource.AI_GENERATED,
                            lead_score=float(lead_data.get("lead_score", 0.5)),
                            lead_status=LeadStatus.NEW,
                            pain_points=", ".join(lead_data.get("pain_points", [])),
                            budget=self._parse_budget(lead_data.get("budget_range", "")),
                            timeline=lead_data.get("timeline", ""),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        session.add(lead)
                        await session.flush()
                        
                        saved_leads.append({
                            "id": lead.id,
                            "name": f"{lead.first_name} {lead.last_name}",
                            "company": lead.company,
                            "job_title": lead.job_title,
                            "email": lead.email,
                            "lead_score": lead.lead_score
                        })
                        
                        if lead.lead_score >= 0.7:
                            qualified_count += 1
                        
                        sources.add(lead.lead_source.value)
                        
                    except Exception as e:
                        logger.error(f"Failed to save lead: {e}")
                        continue
                
                await session.commit()
            
            return {
                "success": True,
                "total_leads": len(saved_leads),
                "qualified_leads": qualified_count,
                "sources": list(sources),
                "leads": saved_leads
            }
            
        except Exception as e:
            logger.error(f"Failed to generate leads: {e}")
            return {
                "success": False,
                "error": f"Failed to generate leads: {str(e)}",
                "total_leads": 0,
                "qualified_leads": 0,
                "sources": []
            }
