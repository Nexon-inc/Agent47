import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import json
import openai
from core.config import settings
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import EventBus
from core.cache.redis_manager import init_redis
from ..database import get_purity_database
from ..models import (
    PurityBusinessIdea, PurityBusinessModel, PurityMarketResearch, PurityCustomerAvatar,
    IndustryType, ValidationStatus, RevenueModel
)

logger = logging.getLogger(__name__)

class BusinessIntelligenceService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = EventBus()
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize business intelligence service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.event_bus.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Business intelligence service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize business intelligence service: {e}")
            raise
    
    async def generate_business_ideas(
        self,
        user_id: int,
        skills: List[str],
        interests: List[str],
        budget_range: str,
        industry_preference: Optional[IndustryType] = None,
        market_trends: Optional[List[str]] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered business ideas based on user inputs"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create prompt for idea generation
            prompt = self._create_idea_generation_prompt(
                skills, interests, budget_range, industry_preference,
                market_trends, location
            )
            
            # Generate ideas using OpenAI
            ideas = await self._generate_ideas_with_ai(prompt)
            
            # Save ideas to database
            saved_ideas = []
            for idea_data in ideas:
                idea = await self._save_business_idea(user_id, idea_data)
                saved_ideas.append(idea)
            
            # Publish event for idea generation
            await self.event_bus.publish(
                "business.ideas.generated",
                {
                    "user_id": user_id,
                    "ideas_count": len(saved_ideas),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "ideas": saved_ideas,
                "total_generated": len(saved_ideas)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate business ideas: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_business_idea(
        self,
        idea_id: int,
        validation_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate a business idea using AI and market data"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea details
                idea_query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Perform validation analysis
                validation_result = await self._perform_validation_analysis(idea, validation_criteria)
                
                # Update idea with validation results
                idea.validation_score = validation_result["score"]
                idea.status = validation_result["status"]
                idea.metadata = {
                    **idea.metadata,
                    "validation": validation_result
                }
                
                await session.commit()
                
                # Publish validation event
                await self.event_bus.publish(
                    "business.idea.validated",
                    {
                        "idea_id": idea_id,
                        "validation_score": validation_result["score"],
                        "status": validation_result["status"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "validation_result": validation_result,
                    "idea": idea
                }
                
        except Exception as e:
            logger.error(f"Failed to validate business idea: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_business_model_canvas(
        self,
        idea_id: int,
        canvas_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a complete business model canvas using AI"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea details
                idea_query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Generate business model canvas using AI
                canvas = await self._generate_business_model_canvas(idea, canvas_data)
                
                # Save business model
                business_model = PurityBusinessModel(
                    idea_id=idea_id,
                    key_partners=canvas["key_partners"],
                    key_activities=canvas["key_activities"],
                    key_resources=canvas["key_resources"],
                    value_propositions=canvas["value_propositions"],
                    customer_relationships=canvas["customer_relationships"],
                    channels=canvas["channels"],
                    customer_segments=canvas["customer_segments"],
                    cost_structure=canvas["cost_structure"],
                    revenue_streams=canvas["revenue_streams"],
                    revenue_model=canvas.get("revenue_model"),
                    pricing_strategy=canvas.get("pricing_strategy"),
                    competitive_advantage=canvas.get("competitive_advantage"),
                    scalability_factors=canvas.get("scalability_factors", []),
                    risk_factors=canvas.get("risk_factors", [])
                )
                
                session.add(business_model)
                await session.commit()
                
                return {
                    "success": True,
                    "business_model": business_model,
                    "canvas_data": canvas
                }
                
        except Exception as e:
            logger.error(f"Failed to create business model canvas: {e}")
            return {"success": False, "error": str(e)}
    
    async def build_customer_avatar(
        self,
        idea_id: int,
        avatar_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build detailed customer personas using AI"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_purity_database()
            async with db.get_session() as session:
                # Get idea details
                idea_query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
                idea_result = await session.execute(idea_query)
                idea = idea_result.scalar_one_or_none()
                
                if not idea:
                    return {"success": False, "error": "Idea not found"}
                
                # Generate customer avatars using AI
                avatars = await self._generate_customer_avatars(idea, avatar_data)
                
                # Save customer avatars
                saved_avatars = []
                for avatar_data in avatars:
                    avatar = PurityCustomerAvatar(
                        idea_id=idea_id,
                        name=avatar_data["name"],
                        age_range=avatar_data.get("age_range"),
                        gender=avatar_data.get("gender"),
                        income_level=avatar_data.get("income_level"),
                        education_level=avatar_data.get("education_level"),
                        occupation=avatar_data.get("occupation"),
                        location=avatar_data.get("location"),
                        interests=avatar_data.get("interests", []),
                        pain_points=avatar_data.get("pain_points", []),
                        goals=avatar_data.get("goals", []),
                        buying_behavior=avatar_data.get("buying_behavior"),
                        preferred_channels=avatar_data.get("preferred_channels", []),
                        decision_factors=avatar_data.get("decision_factors", []),
                        objections=avatar_data.get("objections", [])
                    )
                    session.add(avatar)
                    saved_avatars.append(avatar)
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_avatars": saved_avatars,
                    "total_avatars": len(saved_avatars)
                }
                
        except Exception as e:
            logger.error(f"Failed to build customer avatar: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_idea_generation_prompt(
        self,
        skills: List[str],
        interests: List[str],
        budget_range: str,
        industry_preference: Optional[IndustryType],
        market_trends: Optional[List[str]],
        location: Optional[str]
    ) -> str:
        """Create AI prompt for business idea generation"""
        prompt = f"""
        Generate 5 innovative business ideas based on the following criteria:
        
        Skills: {', '.join(skills)}
        Interests: {', '.join(interests)}
        Budget Range: {budget_range}
        Industry Preference: {industry_preference.value if industry_preference else 'Any'}
        Market Trends: {', '.join(market_trends) if market_trends else 'Current market trends'}
        Location: {location if location else 'Global'}
        
        For each idea, provide:
        1. Business Name
        2. Brief Description
        3. Target Market
        4. Unique Value Proposition
        5. Revenue Potential (estimated annual revenue)
        6. Startup Cost
        7. Time to Market (in months)
        8. Competition Level (Low/Medium/High)
        9. Market Size
        10. Key Success Factors
        
        Format the response as JSON with an array of business ideas.
        """
        return prompt
    
    async def _generate_ideas_with_ai(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate business ideas using OpenAI API"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["idea_generation"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert business consultant and entrepreneur with deep knowledge of market trends, business models, and startup strategies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["idea_generation"]["temperature"],
                max_tokens=self._ai_config["idea_generation"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            ideas = json.loads(content)
            return ideas if isinstance(ideas, list) else []
            
        except Exception as e:
            logger.error(f"Failed to generate ideas with AI: {e}")
            return []
    
    async def _save_business_idea(self, user_id: int, idea_data: Dict[str, Any]) -> PurityBusinessIdea:
        """Save business idea to database"""
        db = await get_purity_database()
        async with db.get_session() as session:
            idea = PurityBusinessIdea(
                user_id=user_id,
                title=idea_data["business_name"],
                description=idea_data["description"],
                industry=IndustryType.OTHER,  # Will be refined later
                target_market=idea_data["target_market"],
                unique_value_proposition=idea_data["unique_value_proposition"],
                revenue_potential=float(idea_data.get("revenue_potential", 0)),
                startup_cost=float(idea_data.get("startup_cost", 0)),
                time_to_market=int(idea_data.get("time_to_market", 12)),
                competition_level=idea_data.get("competition_level", "Medium"),
                market_size=idea_data.get("market_size", "Unknown"),
                tags=idea_data.get("key_success_factors", []),
                metadata=idea_data
            )
            
            session.add(idea)
            await session.commit()
            return idea
    
    async def _perform_validation_analysis(
        self,
        idea: PurityBusinessIdea,
        validation_criteria: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform comprehensive validation analysis"""
        try:
            # Create validation prompt
            prompt = f"""
            Validate this business idea:
            
            Title: {idea.title}
            Description: {idea.description}
            Target Market: {idea.target_market}
            Unique Value Proposition: {idea.unique_value_proposition}
            Industry: {idea.industry.value}
            
            Provide a comprehensive validation analysis including:
            1. Market Demand Score (0-100)
            2. Competition Analysis Score (0-100)
            3. Feasibility Score (0-100)
            4. Scalability Score (0-100)
            5. Overall Validation Score (0-100)
            6. Key Strengths
            7. Key Weaknesses
            8. Recommendations
            9. Validation Status (validated/invalid/needs_more_data)
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["validation"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert business validator with deep market analysis skills."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["validation"]["temperature"],
                max_tokens=self._ai_config["validation"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            validation_data = json.loads(content)
            
            # Calculate overall score
            overall_score = (
                validation_data.get("market_demand_score", 0) * 0.3 +
                validation_data.get("competition_analysis_score", 0) * 0.2 +
                validation_data.get("feasibility_score", 0) * 0.25 +
                validation_data.get("scalability_score", 0) * 0.25
            )
            
            # Determine status
            if overall_score >= 80:
                status = ValidationStatus.VALIDATED
            elif overall_score >= 60:
                status = ValidationStatus.NEEDS_MORE_DATA
            else:
                status = ValidationStatus.INVALID
            
            return {
                "score": overall_score,
                "status": status,
                "analysis": validation_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to perform validation analysis: {e}")
            return {
                "score": 0.0,
                "status": ValidationStatus.NEEDS_MORE_DATA,
                "analysis": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _generate_business_model_canvas(
        self,
        idea: PurityBusinessIdea,
        canvas_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate business model canvas using AI"""
        try:
            prompt = f"""
            Create a complete Business Model Canvas for this business idea:
            
            Title: {idea.title}
            Description: {idea.description}
            Target Market: {idea.target_market}
            Unique Value Proposition: {idea.unique_value_proposition}
            Industry: {idea.industry.value}
            
            Fill in all 9 components of the Business Model Canvas:
            1. Key Partners
            2. Key Activities
            3. Key Resources
            4. Value Propositions
            5. Customer Relationships
            6. Channels
            7. Customer Segments
            8. Cost Structure
            9. Revenue Streams
            
            Also include:
            - Recommended Revenue Model
            - Pricing Strategy
            - Competitive Advantage
            - Scalability Factors
            - Risk Factors
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["business_model"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert business model strategist with deep knowledge of the Business Model Canvas framework."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["business_model"]["temperature"],
                max_tokens=self._ai_config["business_model"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Failed to generate business model canvas: {e}")
            return {}
    
    async def _generate_customer_avatars(
        self,
        idea: PurityBusinessIdea,
        avatar_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate customer avatars using AI"""
        try:
            prompt = f"""
            Create 3 detailed customer personas for this business idea:
            
            Title: {idea.title}
            Description: {idea.description}
            Target Market: {idea.target_market}
            Industry: {idea.industry.value}
            
            For each persona, provide:
            1. Name
            2. Age Range
            3. Gender
            4. Income Level
            5. Education Level
            6. Occupation
            7. Location
            8. Interests
            9. Pain Points
            10. Goals
            11. Buying Behavior
            12. Preferred Channels
            13. Decision Factors
            14. Objections
            
            Format as JSON array.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self._ai_config["idea_generation"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert in customer persona development and market segmentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self._ai_config["idea_generation"]["temperature"],
                max_tokens=self._ai_config["idea_generation"]["max_tokens"]
            )
            
            content = response.choices[0].message.content
            return json.loads(content) if isinstance(json.loads(content), list) else []
            
        except Exception as e:
            logger.error(f"Failed to generate customer avatars: {e}")
            return []
