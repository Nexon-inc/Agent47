import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import selectinload

from ..database import get_purity_database
from ..models import PurityMVPBlueprint, PurityBusinessIdea
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager

class MVPBuilderService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()

    async def create_mvp_blueprint(
        self,
        db: AsyncSession,
        business_idea: str,
        target_market: str,
        budget_constraints: Dict[str, Any],
        timeline: str,
        technical_requirements: List[str]
    ) -> Dict[str, Any]:
        try:
            cache_key = f"mvp_blueprint:{business_idea[:50]}:{target_market}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            prompt = f"""
            Create MVP blueprint for business idea: {business_idea}
            Target Market: {target_market}
            Budget Constraints: {budget_constraints}
            Timeline: {timeline}
            Technical Requirements: {technical_requirements}

            Provide comprehensive MVP blueprint including:
            1. Core features (Must-have)
            2. Nice-to-have features
            3. Technical stack recommendations
            4. Development phases
            5. Resource requirements
            6. Success metrics

            Return the response as a JSON object with the following structure:
            {{
                "core_features": [
                    {{
                        "feature_name": "User Registration",
                        "priority": "Must-have",
                        "description": "Basic user registration and authentication",
                        "development_effort": "2 weeks",
                        "cost_estimate": "$5,000",
                        "success_metrics": ["User signup rate", "Registration completion"]
                    }}
                ],
                "nice_to_have_features": [
                    {{
                        "feature_name": "Advanced Analytics",
                        "priority": "Nice-to-have",
                        "description": "Detailed user analytics and reporting",
                        "development_effort": "3 weeks",
                        "cost_estimate": "$8,000",
                        "success_metrics": ["Feature adoption rate", "User engagement"]
                    }}
                ],
                "technical_stack": {{
                    "frontend": ["React", "TypeScript", "Tailwind CSS"],
                    "backend": ["Node.js", "Express", "PostgreSQL"],
                    "deployment": ["AWS", "Docker", "CI/CD"],
                    "third_party": ["Stripe", "SendGrid", "Google Analytics"]
                }},
                "development_phases": [
                    {{
                        "phase": "Phase 1 - Core MVP",
                        "duration": "8 weeks",
                        "features": ["User registration", "Core functionality"],
                        "deliverables": ["Working prototype", "Basic UI"]
                    }}
                ],
                "resource_requirements": {{
                    "team_size": "3-5 people",
                    "roles": ["Full-stack developer", "UI/UX designer", "Product manager"],
                    "estimated_cost": "$25,000",
                    "timeline": "12 weeks"
                }},
                "success_metrics": [
                    "User acquisition rate",
                    "Feature adoption rate",
                    "User retention rate",
                    "Revenue per user"
                ],
                "risk_mitigation": [
                    "Start with minimal viable features",
                    "Regular user feedback loops",
                    "Iterative development approach"
                ],
                "blueprint_score": 88.5
            }}
            """

            blueprint_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            mvp_blueprint = {
                "id": f"mvp_{business_idea[:30]}",
                "business_idea": business_idea,
                "target_market": target_market,
                "budget_constraints": budget_constraints,
                "timeline": timeline,
                "technical_requirements": technical_requirements,
                "blueprint_data": blueprint_data,
                "blueprint_score": blueprint_data.get("blueprint_score", 0),
                "created_at": datetime.utcnow()
            }

            stmt = insert(PurityMVPBlueprint).values(**mvp_blueprint)
            await db.execute(stmt)
            await db.commit()

            await self.redis_manager.set(cache_key, json.dumps(mvp_blueprint), expire=3600)
            await self.event_bus.publish("purity.mvp_blueprint_created", {
                "business_idea": business_idea[:50],
                "target_market": target_market,
                "blueprint_score": mvp_blueprint["blueprint_score"],
                "estimated_cost": blueprint_data.get("resource_requirements", {}).get("estimated_cost", ""),
                "timestamp": datetime.utcnow().isoformat()
            })

            return mvp_blueprint

        except Exception as e:
            await db.rollback()
            raise Exception(f"Failed to create MVP blueprint: {str(e)}")

    async def prioritize_features(
        self,
        db: AsyncSession,
        mvp_blueprint_id: str,
        user_feedback: Dict[str, Any],
        market_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            stmt = select(PurityMVPBlueprint).where(PurityMVPBlueprint.id == mvp_blueprint_id)
            result = await db.execute(stmt)
            blueprint = result.scalar_one_or_none()

            if not blueprint:
                raise Exception("MVP blueprint not found")

            prompt = f"""
            Prioritize features based on feedback and validation:
            Blueprint Data: {blueprint.blueprint_data}
            User Feedback: {user_feedback}
            Market Validation: {market_validation}

            Provide comprehensive feature prioritization including:
            1. Updated feature priorities
            2. Development roadmap
            3. Resource allocation
            4. Risk assessment

            Return the response as a JSON object with the following structure:
            {{
                "prioritized_features": [
                    {{
                        "feature_name": "Core Feature 1",
                        "priority_score": 95.0,
                        "business_value": "High",
                        "technical_feasibility": "Medium",
                        "user_demand": "High",
                        "development_effort": "3 weeks"
                    }}
                ],
                "development_roadmap": [
                    {{
                        "sprint": "Sprint 1",
                        "duration": "2 weeks",
                        "features": ["Feature 1", "Feature 2"],
                        "success_criteria": ["Criteria 1", "Criteria 2"]
                    }}
                ],
                "resource_allocation": {{
                    "development_team": "3 developers",
                    "design_team": "1 designer",
                    "testing_team": "1 QA engineer",
                    "estimated_budget": "$30,000"
                }},
                "risk_assessment": [
                    "Technical risk: Integration complexity",
                    "Market risk: User adoption uncertainty",
                    "Resource risk: Team availability"
                ],
                "prioritization_score": 92.0
            }}
            """

            prioritization_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            feature_prioritization = {
                "id": f"prioritization_{mvp_blueprint_id}",
                "mvp_blueprint_id": mvp_blueprint_id,
                "user_feedback": user_feedback,
                "market_validation": market_validation,
                "prioritization_data": prioritization_data,
                "prioritization_score": prioritization_data.get("prioritization_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.event_bus.publish("purity.features_prioritized", {
                "mvp_blueprint_id": mvp_blueprint_id,
                "feature_count": len(prioritization_data.get("prioritized_features", [])),
                "prioritization_score": feature_prioritization["prioritization_score"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return feature_prioritization

        except Exception as e:
            raise Exception(f"Failed to prioritize features: {str(e)}")

    async def recommend_development_tools(
        self,
        db: AsyncSession,
        mvp_blueprint_id: str,
        team_expertise: List[str],
        budget_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            stmt = select(PurityMVPBlueprint).where(PurityMVPBlueprint.id == mvp_blueprint_id)
            result = await db.execute(stmt)
            blueprint = result.scalar_one_or_none()

            if not blueprint:
                raise Exception("MVP blueprint not found")

            prompt = f"""
            Recommend development tools based on requirements:
            Blueprint Data: {blueprint.blueprint_data}
            Team Expertise: {team_expertise}
            Budget Constraints: {budget_constraints}

            Provide comprehensive tool recommendations including:
            1. Development tools
            2. Design tools
            3. Testing tools
            4. Deployment tools
            5. Cost estimates

            Return the response as a JSON object with the following structure:
            {{
                "development_tools": [
                    {{
                        "category": "Frontend Framework",
                        "tool_name": "React",
                        "cost": "Free",
                        "learning_curve": "Medium",
                        "recommendation_reason": "Popular, well-documented, large community"
                    }}
                ],
                "design_tools": [
                    {{
                        "category": "UI Design",
                        "tool_name": "Figma",
                        "cost": "$12/month",
                        "learning_curve": "Low",
                        "recommendation_reason": "Collaborative, cloud-based, industry standard"
                    }}
                ],
                "testing_tools": [
                    {{
                        "category": "Testing Framework",
                        "tool_name": "Jest",
                        "cost": "Free",
                        "learning_curve": "Low",
                        "recommendation_reason": "JavaScript testing, easy setup"
                    }}
                ],
                "deployment_tools": [
                    {{
                        "category": "Cloud Platform",
                        "tool_name": "Vercel",
                        "cost": "$20/month",
                        "learning_curve": "Low",
                        "recommendation_reason": "Easy deployment, good for React apps"
                    }}
                ],
                "total_monthly_cost": "$50",
                "total_setup_cost": "$200",
                "tool_recommendation_score": 89.0
            }}
            """

            tool_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            tool_recommendations = {
                "id": f"tools_{mvp_blueprint_id}",
                "mvp_blueprint_id": mvp_blueprint_id,
                "team_expertise": team_expertise,
                "budget_constraints": budget_constraints,
                "tool_recommendations": tool_data,
                "total_monthly_cost": tool_data.get("total_monthly_cost", ""),
                "total_setup_cost": tool_data.get("total_setup_cost", ""),
                "recommendation_score": tool_data.get("tool_recommendation_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.event_bus.publish("purity.development_tools_recommended", {
                "mvp_blueprint_id": mvp_blueprint_id,
                "tool_count": len(tool_data.get("development_tools", [])) + len(tool_data.get("design_tools", [])) + len(tool_data.get("testing_tools", [])) + len(tool_data.get("deployment_tools", [])),
                "total_monthly_cost": tool_recommendations["total_monthly_cost"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return tool_recommendations

        except Exception as e:
            raise Exception(f"Failed to recommend development tools: {str(e)}")

    async def validate_mvp_blueprint(
        self,
        db: AsyncSession,
        mvp_blueprint_id: str,
        validation_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            stmt = select(PurityMVPBlueprint).where(PurityMVPBlueprint.id == mvp_blueprint_id)
            result = await db.execute(stmt)
            blueprint = result.scalar_one_or_none()

            if not blueprint:
                raise Exception("MVP blueprint not found")

            prompt = f"""
            Validate MVP blueprint against criteria:
            Blueprint Data: {blueprint.blueprint_data}
            Validation Criteria: {validation_criteria}

            Provide comprehensive validation including:
            1. Feasibility assessment
            2. Resource adequacy
            3. Timeline realism
            4. Risk evaluation

            Return the response as a JSON object with the following structure:
            {{
                "feasibility_score": 85.0,
                "resource_adequacy": "Sufficient",
                "timeline_realism": "Realistic",
                "risk_level": "Medium",
                "validation_issues": [
                    "Budget may be insufficient for all features",
                    "Timeline may be too aggressive"
                ],
                "improvement_suggestions": [
                    "Consider reducing feature scope",
                    "Extend timeline by 2 weeks"
                ],
                "overall_validation_score": 82.5
            }}
            """

            validation_data = await self.nlp_processor.generate_response(prompt, self.model_config)
            
            validation_result = {
                "id": f"validation_{mvp_blueprint_id}",
                "mvp_blueprint_id": mvp_blueprint_id,
                "validation_criteria": validation_criteria,
                "validation_data": validation_data,
                "overall_score": validation_data.get("overall_validation_score", 0),
                "created_at": datetime.utcnow()
            }

            await self.event_bus.publish("purity.mvp_blueprint_validated", {
                "mvp_blueprint_id": mvp_blueprint_id,
                "validation_score": validation_result["overall_score"],
                "timestamp": datetime.utcnow().isoformat()
            })

            return validation_result

        except Exception as e:
            raise Exception(f"Failed to validate MVP blueprint: {str(e)}")
