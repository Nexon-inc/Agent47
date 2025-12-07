from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, TaskAutomation, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class TaskAutomationService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_workflow_automation(
        self,
        db: AsyncSession,
        business_idea_id: int,
        workflow_type: str,
        current_processes: List[str],
        automation_goals: List[str],
        integration_platforms: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"workflow_automation:{business_idea_id}:{workflow_type}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_workflow_automation_prompt(
                business_idea, workflow_type, current_processes, automation_goals, integration_platforms
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps automate business tasks. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            automation_data = json.loads(ai_response)
            
            workflow_automation = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "workflow_type": workflow_type,
                "current_processes": current_processes,
                "automation_goals": automation_goals,
                "integration_platforms": integration_platforms,
                "automated_workflows": automation_data.get("automated_workflows", []),
                "integration_setup": automation_data.get("integration_setup", {}),
                "automation_rules": automation_data.get("automation_rules", []),
                "efficiency_metrics": automation_data.get("efficiency_metrics", {}),
                "implementation_plan": automation_data.get("implementation_plan", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(automation_data), expire=3600)
            await self.event_bus.publish("purity.workflow_automation_created", {
                "business_idea_id": business_idea_id,
                "workflow_type": workflow_type,
                "automation_goals": automation_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return workflow_automation
            
        except Exception as e:
            raise e
    
    async def setup_integrations(
        self,
        db: AsyncSession,
        business_idea_id: int,
        platform_integrations: List[str],
        data_flow_requirements: Dict[str, Any],
        security_requirements: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_integration_setup_prompt(
                business_idea, platform_integrations, data_flow_requirements, security_requirements
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps automate business tasks. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            integration_data = json.loads(ai_response)
            
            integration_setup = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "platform_integrations": platform_integrations,
                "data_flow_requirements": data_flow_requirements,
                "security_requirements": security_requirements,
                "integration_configurations": integration_data.get("integration_configurations", []),
                "data_mapping": integration_data.get("data_mapping", {}),
                "api_endpoints": integration_data.get("api_endpoints", []),
                "security_protocols": integration_data.get("security_protocols", {}),
                "testing_procedures": integration_data.get("testing_procedures", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.integration_setup_completed", {
                "business_idea_id": business_idea_id,
                "platform_integrations": platform_integrations,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return integration_setup
            
        except Exception as e:
            raise e
    
    async def optimize_business_processes(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_processes: Dict[str, Any],
        optimization_goals: List[str],
        resource_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_process_optimization_prompt(
                business_idea, current_processes, optimization_goals, resource_constraints
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps automate business tasks. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            optimization_data = json.loads(ai_response)
            
            process_optimization = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_processes": current_processes,
                "optimization_goals": optimization_goals,
                "resource_constraints": resource_constraints,
                "optimized_processes": optimization_data.get("optimized_processes", []),
                "efficiency_improvements": optimization_data.get("efficiency_improvements", {}),
                "automation_opportunities": optimization_data.get("automation_opportunities", []),
                "resource_allocation": optimization_data.get("resource_allocation", {}),
                "implementation_timeline": optimization_data.get("implementation_timeline", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.process_optimization_completed", {
                "business_idea_id": business_idea_id,
                "optimization_goals": optimization_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return process_optimization
            
        except Exception as e:
            raise e
    
    async def create_automation_dashboard(
        self,
        db: AsyncSession,
        business_idea_id: int,
        automation_metrics: Dict[str, Any],
        monitoring_requirements: List[str],
        alert_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_automation_dashboard_prompt(
                business_idea, automation_metrics, monitoring_requirements, alert_settings
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps automate business tasks. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            dashboard_data = json.loads(ai_response)
            
            automation_dashboard = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "automation_metrics": automation_metrics,
                "monitoring_requirements": monitoring_requirements,
                "alert_settings": alert_settings,
                "dashboard_widgets": dashboard_data.get("dashboard_widgets", []),
                "monitoring_alerts": dashboard_data.get("monitoring_alerts", []),
                "performance_metrics": dashboard_data.get("performance_metrics", {}),
                "reporting_features": dashboard_data.get("reporting_features", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.automation_dashboard_created", {
                "business_idea_id": business_idea_id,
                "monitoring_requirements": monitoring_requirements,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return automation_dashboard
            
        except Exception as e:
            raise e
    
    def _create_workflow_automation_prompt(
        self,
        business_idea: BusinessIdea,
        workflow_type: str,
        current_processes: List[str],
        automation_goals: List[str],
        integration_platforms: List[str]
    ) -> str:
        return f"""
        Create workflow automation for:
        - Business Idea: {business_idea.description}
        - Workflow Type: {workflow_type}
        - Current Processes: {', '.join(current_processes)}
        - Automation Goals: {', '.join(automation_goals)}
        - Integration Platforms: {', '.join(integration_platforms)}
        
        Develop comprehensive workflow automation including:
        1. Automated workflows
        2. Integration setup
        3. Automation rules
        4. Efficiency metrics
        5. Implementation plan
        
        Return the response as a JSON object with the following structure:
        {{
            "automated_workflows": [
                {{
                    "workflow_name": "Workflow name",
                    "description": "Workflow description",
                    "triggers": ["Trigger 1", "Trigger 2"],
                    "actions": ["Action 1", "Action 2"],
                    "conditions": ["Condition 1", "Condition 2"],
                    "expected_outcome": "Expected outcome"
                }}
            ],
            "integration_setup": {{
                "platform_connections": ["Connection 1", "Connection 2"],
                "data_sync_rules": ["Rule 1", "Rule 2"],
                "api_configurations": ["Config 1", "Config 2"]
            }},
            "automation_rules": [
                {{
                    "rule_name": "Rule name",
                    "trigger_condition": "Trigger condition",
                    "automated_action": "Automated action",
                    "success_criteria": "Success criteria"
                }}
            ],
            "efficiency_metrics": {{
                "time_savings": "Time savings estimate",
                "cost_reduction": "Cost reduction estimate",
                "error_reduction": "Error reduction estimate",
                "productivity_gain": "Productivity gain estimate"
            }},
            "implementation_plan": {{
                "phase_1": {{
                    "duration": "3 weeks",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }},
                "phase_2": {{
                    "duration": "6 weeks",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }}
            }}
        }}
        """
    
    def _create_integration_setup_prompt(
        self,
        business_idea: BusinessIdea,
        platform_integrations: List[str],
        data_flow_requirements: Dict[str, Any],
        security_requirements: List[str]
    ) -> str:
        return f"""
        Setup integrations for:
        - Business Idea: {business_idea.description}
        - Platform Integrations: {', '.join(platform_integrations)}
        - Data Flow Requirements: {data_flow_requirements}
        - Security Requirements: {', '.join(security_requirements)}
        
        Provide comprehensive integration setup including:
        1. Integration configurations
        2. Data mapping
        3. API endpoints
        4. Security protocols
        5. Testing procedures
        
        Return the response as a JSON object with the following structure:
        {{
            "integration_configurations": [
                {{
                    "platform_name": "Platform name",
                    "connection_type": "Connection type",
                    "authentication_method": "Authentication method",
                    "data_permissions": ["Permission 1", "Permission 2"]
                }}
            ],
            "data_mapping": {{
                "source_fields": ["Field 1", "Field 2"],
                "target_fields": ["Field 1", "Field 2"],
                "transformation_rules": ["Rule 1", "Rule 2"],
                "validation_rules": ["Rule 1", "Rule 2"]
            }},
            "api_endpoints": [
                {{
                    "endpoint_name": "Endpoint name",
                    "url": "API URL",
                    "method": "HTTP method",
                    "parameters": ["Parameter 1", "Parameter 2"],
                    "response_format": "Response format"
                }}
            ],
            "security_protocols": {{
                "authentication": "Authentication protocol",
                "encryption": "Encryption method",
                "access_control": "Access control rules",
                "data_protection": "Data protection measures"
            }},
            "testing_procedures": [
                "Procedure 1: API endpoint testing",
                "Procedure 2: Data flow validation",
                "Procedure 3: Security testing",
                "Procedure 4: Performance testing"
            ]
        }}
        """
    
    def _create_process_optimization_prompt(
        self,
        business_idea: BusinessIdea,
        current_processes: Dict[str, Any],
        optimization_goals: List[str],
        resource_constraints: Dict[str, Any]
    ) -> str:
        return f"""
        Optimize business processes for:
        - Business Idea: {business_idea.description}
        - Current Processes: {current_processes}
        - Optimization Goals: {', '.join(optimization_goals)}
        - Resource Constraints: {resource_constraints}
        
        Provide comprehensive process optimization including:
        1. Optimized processes
        2. Efficiency improvements
        3. Automation opportunities
        4. Resource allocation
        5. Implementation timeline
        
        Return the response as a JSON object with the following structure:
        {{
            "optimized_processes": [
                {{
                    "process_name": "Process name",
                    "current_state": "Current process state",
                    "optimized_state": "Optimized process state",
                    "improvements": ["Improvement 1", "Improvement 2"],
                    "implementation_steps": ["Step 1", "Step 2"]
                }}
            ],
            "efficiency_improvements": {{
                "time_reduction": "Time reduction estimate",
                "cost_savings": "Cost savings estimate",
                "quality_improvement": "Quality improvement estimate",
                "productivity_gain": "Productivity gain estimate"
            }},
            "automation_opportunities": [
                {{
                    "opportunity_name": "Opportunity name",
                    "automation_type": "Automation type",
                    "expected_benefits": ["Benefit 1", "Benefit 2"],
                    "implementation_complexity": "High/Medium/Low"
                }}
            ],
            "resource_allocation": {{
                "human_resources": "Human resource allocation",
                "technical_resources": "Technical resource allocation",
                "financial_resources": "Financial resource allocation",
                "timeline": "Implementation timeline"
            }},
            "implementation_timeline": {{
                "phase_1": {{
                    "duration": "4 weeks",
                    "activities": ["Activity 1", "Activity 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }},
                "phase_2": {{
                    "duration": "8 weeks",
                    "activities": ["Activity 1", "Activity 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }}
            }}
        }}
        """
    
    def _create_automation_dashboard_prompt(
        self,
        business_idea: BusinessIdea,
        automation_metrics: Dict[str, Any],
        monitoring_requirements: List[str],
        alert_settings: Dict[str, Any]
    ) -> str:
        return f"""
        Create automation dashboard for:
        - Business Idea: {business_idea.description}
        - Automation Metrics: {automation_metrics}
        - Monitoring Requirements: {', '.join(monitoring_requirements)}
        - Alert Settings: {alert_settings}
        
        Develop comprehensive automation dashboard including:
        1. Dashboard widgets
        2. Monitoring alerts
        3. Performance metrics
        4. Reporting features
        
        Return the response as a JSON object with the following structure:
        {{
            "dashboard_widgets": [
                {{
                    "widget_name": "Widget name",
                    "widget_type": "Widget type",
                    "data_source": "Data source",
                    "refresh_rate": "Refresh rate",
                    "display_options": ["Option 1", "Option 2"]
                }}
            ],
            "monitoring_alerts": [
                {{
                    "alert_name": "Alert name",
                    "trigger_condition": "Trigger condition",
                    "notification_method": "Notification method",
                    "severity_level": "High/Medium/Low",
                    "escalation_rules": ["Rule 1", "Rule 2"]
                }}
            ],
            "performance_metrics": {{
                "automation_efficiency": "Efficiency metric",
                "error_rate": "Error rate metric",
                "response_time": "Response time metric",
                "uptime": "Uptime metric"
            }},
            "reporting_features": [
                "Feature 1: Real-time monitoring",
                "Feature 2: Historical data analysis",
                "Feature 3: Custom report generation",
                "Feature 4: Export capabilities"
            ]
        }}
        """
