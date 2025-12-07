import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import json
from backend.core.config import settings
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, CustomerProfile, SupportWorkflow,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel, TicketEscalation,
    SupportAgent
)

logger = logging.getLogger(__name__)

class CustomWorkflowsService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._workflow_cache = {}
        self._workflow_execution_history = []
    
    async def initialize(self):
        """Initialize custom workflows service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._load_workflows_from_database()
            self._initialized = True
            logger.info("Custom workflows service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize custom workflows service: {e}")
            raise
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        category: TicketCategory,
        priority: TicketPriority,
        steps: List[Dict[str, Any]],
        auto_assign: bool = False,
        auto_assign_agent_id: Optional[int] = None,
        sla_target: Optional[int] = None,
        escalation_rules: Optional[Dict[str, Any]] = None,
        conditions: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new custom workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Validate workflow steps
            await self._validate_workflow_steps(steps)
            
            # Validate escalation rules
            if escalation_rules:
                await self._validate_escalation_rules(escalation_rules)
            
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create workflow record
                workflow = SupportWorkflow(
                    name=name,
                    description=description,
                    category=category,
                    priority=priority,
                    steps=steps,
                    auto_assign=auto_assign,
                    auto_assign_agent_id=auto_assign_agent_id,
                    sla_target=sla_target,
                    escalation_rules=escalation_rules or {},
                    is_active=is_active
                )
                
                session.add(workflow)
                await session.commit()
                await session.refresh(workflow)
                
                # Add to cache
                self._workflow_cache[workflow.id] = {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "category": workflow.category.value,
                    "priority": workflow.priority.value,
                    "steps": workflow.steps,
                    "auto_assign": workflow.auto_assign,
                    "auto_assign_agent_id": workflow.auto_assign_agent_id,
                    "sla_target": workflow.sla_target,
                    "escalation_rules": workflow.escalation_rules,
                    "conditions": conditions,
                    "is_active": workflow.is_active,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at
                }
                
                # Publish event for workflow creation
                await self.event_bus.publish(
                    "clara.workflows.workflow_created",
                    {
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "category": workflow.category.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "workflow_id": workflow.id,
                    "workflow": self._workflow_cache[workflow.id],
                    "message": f"Workflow '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_workflow(
        self,
        workflow_id: int,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Get a specific workflow by ID"""
        if not self._initialized:
            await self.initialize()
        
        try:
            workflow = self._workflow_cache.get(workflow_id)
            
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            if not include_inactive and not workflow.get("is_active", True):
                raise ValueError(f"Workflow {workflow_id} is inactive")
            
            return {
                "success": True,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_workflows(
        self,
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        is_active: Optional[bool] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search workflows with filters"""
        if not self._initialized:
            await self.initialize()
        
        try:
            workflows = list(self._workflow_cache.values())
            
            # Apply filters
            if category:
                workflows = [w for w in workflows if w.get("category") == category.value]
            
            if priority:
                workflows = [w for w in workflows if w.get("priority") == priority.value]
            
            if is_active is not None:
                workflows = [w for w in workflows if w.get("is_active") == is_active]
            
            if search_term:
                search_lower = search_term.lower()
                workflows = [
                    w for w in workflows 
                    if search_lower in w.get("name", "").lower() or 
                       search_lower in w.get("description", "").lower()
                ]
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows)
            }
            
        except Exception as e:
            logger.error(f"Failed to search workflows: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_workflow(
        self,
        workflow_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            workflow = self._workflow_cache.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Validate updates
            allowed_updates = ["name", "description", "category", "priority", "steps", "auto_assign", "auto_assign_agent_id", "sla_target", "escalation_rules", "conditions", "is_active"]
            for key in updates:
                if key not in allowed_updates:
                    raise ValueError(f"Invalid update field: {key}")
            
            # Validate workflow steps if provided
            if "steps" in updates:
                await self._validate_workflow_steps(updates["steps"])
            
            # Validate escalation rules if provided
            if "escalation_rules" in updates:
                await self._validate_escalation_rules(updates["escalation_rules"])
            
            db = await get_clara_database()
            async with db.get_session() as session:
                # Update workflow in database
                workflow_query = select(SupportWorkflow).where(SupportWorkflow.id == workflow_id)
                workflow_result = await session.execute(workflow_query)
                db_workflow = workflow_result.scalar_one_or_none()
                
                if not db_workflow:
                    raise ValueError(f"Workflow {workflow_id} not found in database")
                
                # Apply updates
                for key, value in updates.items():
                    if hasattr(db_workflow, key):
                        setattr(db_workflow, key, value)
                
                db_workflow.updated_at = datetime.utcnow()
                await session.commit()
                
                # Update cache
                workflow.update(updates)
                workflow["updated_at"] = db_workflow.updated_at
                
                # Publish event for workflow update
                await self.event_bus.publish(
                    "clara.workflows.workflow_updated",
                    {
                        "workflow_id": workflow_id,
                        "updates": updates,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "workflow": workflow,
                    "message": f"Workflow {workflow_id} updated successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_workflow(self, workflow_id: int) -> Dict[str, Any]:
        """Delete a workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            workflow = self._workflow_cache.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            db = await get_clara_database()
            async with db.get_session() as session:
                # Delete from database
                workflow_query = select(SupportWorkflow).where(SupportWorkflow.id == workflow_id)
                workflow_result = await session.execute(workflow_query)
                db_workflow = workflow_result.scalar_one_or_none()
                
                if db_workflow:
                    await session.delete(db_workflow)
                    await session.commit()
                
                # Remove from cache
                del self._workflow_cache[workflow_id]
                
                # Publish event for workflow deletion
                await self.event_bus.publish(
                    "clara.workflows.workflow_deleted",
                    {
                        "workflow_id": workflow_id,
                        "workflow_name": workflow.get("name"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "message": f"Workflow {workflow_id} deleted successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_workflow(
        self,
        workflow_id: int,
        ticket_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow for a specific ticket"""
        if not self._initialized:
            await self.initialize()
        
        try:
            workflow = self._workflow_cache.get(workflow_id)
            if not workflow or not workflow.get("is_active", True):
                raise ValueError(f"Workflow {workflow_id} not found or inactive")
            
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Check if workflow conditions are met
                if not await self._check_workflow_conditions(workflow, ticket, context):
                    return {
                        "success": True,
                        "message": "Workflow conditions not met, skipping execution"
                    }
                
                # Execute workflow steps
                execution_results = []
                for step in workflow.get("steps", []):
                    step_result = await self._execute_workflow_step(step, ticket, session, context)
                    execution_results.append(step_result)
                    
                    # Check if step failed and workflow should stop
                    if not step_result.get("success", True) and step.get("stop_on_failure", False):
                        break
                
                # Record execution
                execution_record = {
                    "workflow_id": workflow_id,
                    "ticket_id": ticket_id,
                    "execution_results": execution_results,
                    "timestamp": datetime.utcnow(),
                    "success": all(r.get("success", True) for r in execution_results)
                }
                
                self._workflow_execution_history.append(execution_record)
                
                # Publish event for workflow execution
                await self.event_bus.publish(
                    "clara.workflows.workflow_executed",
                    {
                        "workflow_id": workflow_id,
                        "ticket_id": ticket_id,
                        "execution_results": execution_results,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "ticket_id": ticket_id,
                    "execution_results": execution_results,
                    "message": f"Workflow '{workflow['name']}' executed successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id} for ticket {ticket_id}: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "ticket_id": ticket_id,
                "error": str(e)
            }
    
    async def get_matching_workflows(
        self,
        ticket_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get workflows that match a ticket's criteria"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket
                ticket_query = select(SupportTicket).where(SupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if not ticket:
                    raise ValueError(f"Ticket {ticket_id} not found")
                
                # Find matching workflows
                matching_workflows = []
                for workflow in self._workflow_cache.values():
                    if not workflow.get("is_active", True):
                        continue
                    
                    # Check category match
                    if workflow.get("category") != ticket.category.value:
                        continue
                    
                    # Check priority match
                    if workflow.get("priority") != ticket.priority.value:
                        continue
                    
                    # Check conditions
                    if await self._check_workflow_conditions(workflow, ticket, context):
                        matching_workflows.append(workflow)
                
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "matching_workflows": matching_workflows,
                    "count": len(matching_workflows)
                }
                
        except Exception as e:
            logger.error(f"Failed to get matching workflows for ticket {ticket_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_workflow_execution_history(
        self,
        workflow_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get workflow execution history"""
        if not self._initialized:
            await self.initialize()
        
        try:
            history = self._workflow_execution_history
            
            # Apply filters
            if workflow_id:
                history = [h for h in history if h.get("workflow_id") == workflow_id]
            
            if ticket_id:
                history = [h for h in history if h.get("ticket_id") == ticket_id]
            
            # Sort by timestamp descending
            history.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            
            # Limit results
            history = history[:limit]
            
            return {
                "success": True,
                "executions": history,
                "count": len(history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow execution history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_workflow_steps(self, steps: List[Dict[str, Any]]) -> None:
        """Validate workflow steps"""
        try:
            if not steps:
                raise ValueError("Workflow must have at least one step")
            
            valid_step_types = [
                "assign_agent", "update_status", "update_priority", "add_tag",
                "send_notification", "create_follow_up", "escalate_ticket",
                "update_sla", "add_note", "trigger_webhook", "send_email"
            ]
            
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(f"Step {i} must be a dictionary")
                
                step_type = step.get("type")
                if not step_type:
                    raise ValueError(f"Step {i} must have a 'type' field")
                
                if step_type not in valid_step_types:
                    raise ValueError(f"Step {i} has invalid type '{step_type}'. Valid types: {valid_step_types}")
                
                # Validate step-specific parameters
                await self._validate_step_parameters(step, i)
                
        except Exception as e:
            logger.error(f"Workflow steps validation failed: {e}")
            raise
    
    async def _validate_step_parameters(self, step: Dict[str, Any], step_index: int) -> None:
        """Validate step-specific parameters"""
        try:
            step_type = step.get("type")
            
            if step_type == "assign_agent":
                if "agent_id" not in step and "agent_criteria" not in step:
                    raise ValueError(f"Step {step_index} (assign_agent) must have 'agent_id' or 'agent_criteria'")
            
            elif step_type == "update_status":
                if "status" not in step:
                    raise ValueError(f"Step {step_index} (update_status) must have 'status' field")
            
            elif step_type == "update_priority":
                if "priority" not in step:
                    raise ValueError(f"Step {step_index} (update_priority) must have 'priority' field")
            
            elif step_type == "send_notification":
                if "notification_type" not in step:
                    raise ValueError(f"Step {step_index} (send_notification) must have 'notification_type' field")
            
            elif step_type == "trigger_webhook":
                if "webhook_url" not in step:
                    raise ValueError(f"Step {step_index} (trigger_webhook) must have 'webhook_url' field")
            
            elif step_type == "send_email":
                if "template_id" not in step and "email_content" not in step:
                    raise ValueError(f"Step {step_index} (send_email) must have 'template_id' or 'email_content'")
                    
        except Exception as e:
            logger.error(f"Step parameters validation failed: {e}")
            raise
    
    async def _validate_escalation_rules(self, escalation_rules: Dict[str, Any]) -> None:
        """Validate escalation rules"""
        try:
            if not isinstance(escalation_rules, dict):
                raise ValueError("Escalation rules must be a dictionary")
            
            valid_rule_types = ["time_based", "priority_based", "volume_based", "satisfaction_based"]
            
            for rule_type, rule_config in escalation_rules.items():
                if rule_type not in valid_rule_types:
                    raise ValueError(f"Invalid escalation rule type: {rule_type}")
                
                if not isinstance(rule_config, dict):
                    raise ValueError(f"Escalation rule config for {rule_type} must be a dictionary")
                
                # Validate rule-specific parameters
                if rule_type == "time_based":
                    if "timeout_minutes" not in rule_config:
                        raise ValueError("Time-based escalation rule must have 'timeout_minutes'")
                
                elif rule_type == "priority_based":
                    if "priority_threshold" not in rule_config:
                        raise ValueError("Priority-based escalation rule must have 'priority_threshold'")
                
                elif rule_type == "volume_based":
                    if "ticket_count_threshold" not in rule_config:
                        raise ValueError("Volume-based escalation rule must have 'ticket_count_threshold'")
                
                elif rule_type == "satisfaction_based":
                    if "satisfaction_threshold" not in rule_config:
                        raise ValueError("Satisfaction-based escalation rule must have 'satisfaction_threshold'")
                        
        except Exception as e:
            logger.error(f"Escalation rules validation failed: {e}")
            raise
    
    async def _check_workflow_conditions(
        self,
        workflow: Dict[str, Any],
        ticket: SupportTicket,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if workflow conditions are met"""
        try:
            conditions = workflow.get("conditions", {})
            if not conditions:
                return True  # No conditions means always execute
            
            # Check ticket-based conditions
            if "customer_tier" in conditions:
                customer_profile = await self._get_customer_profile(ticket.customer_id)
                if customer_profile and customer_profile.support_tier != conditions["customer_tier"]:
                    return False
            
            if "channel" in conditions:
                if ticket.channel.value not in conditions["channel"]:
                    return False
            
            if "tags" in conditions:
                ticket_tags = ticket.tags or []
                required_tags = conditions["tags"]
                if not all(tag in ticket_tags for tag in required_tags):
                    return False
            
            # Check context-based conditions
            if context and "context_conditions" in conditions:
                context_conditions = conditions["context_conditions"]
                for key, value in context_conditions.items():
                    if context.get(key) != value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check workflow conditions: {e}")
            return False
    
    async def _execute_workflow_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            step_type = step.get("type")
            
            if step_type == "assign_agent":
                return await self._execute_assign_agent_step(step, ticket, session)
            
            elif step_type == "update_status":
                return await self._execute_update_status_step(step, ticket, session)
            
            elif step_type == "update_priority":
                return await self._execute_update_priority_step(step, ticket, session)
            
            elif step_type == "add_tag":
                return await self._execute_add_tag_step(step, ticket, session)
            
            elif step_type == "send_notification":
                return await self._execute_send_notification_step(step, ticket, context)
            
            elif step_type == "create_follow_up":
                return await self._execute_create_follow_up_step(step, ticket, session)
            
            elif step_type == "escalate_ticket":
                return await self._execute_escalate_ticket_step(step, ticket, session)
            
            elif step_type == "update_sla":
                return await self._execute_update_sla_step(step, ticket, session)
            
            elif step_type == "add_note":
                return await self._execute_add_note_step(step, ticket, session)
            
            elif step_type == "trigger_webhook":
                return await self._execute_trigger_webhook_step(step, ticket, context)
            
            elif step_type == "send_email":
                return await self._execute_send_email_step(step, ticket, context)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown step type: {step_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to execute workflow step {step.get('type')}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_assign_agent_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute assign agent step"""
        try:
            agent_id = step.get("agent_id")
            agent_criteria = step.get("agent_criteria", {})
            
            if agent_id:
                # Assign to specific agent
                ticket.assigned_agent_id = agent_id
            elif agent_criteria:
                # Find agent based on criteria
                agent = await self._find_agent_by_criteria(agent_criteria, session)
                if agent:
                    ticket.assigned_agent_id = agent.user_id
                else:
                    return {
                        "success": False,
                        "error": "No agent found matching criteria"
                    }
            
            await session.commit()
            
            return {
                "success": True,
                "action": "assign_agent",
                "agent_id": ticket.assigned_agent_id
            }
            
        except Exception as e:
            logger.error(f"Failed to execute assign agent step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_update_status_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute update status step"""
        try:
            new_status = TicketStatus(step["status"])
            old_status = ticket.status
            ticket.status = new_status
            
            await session.commit()
            
            return {
                "success": True,
                "action": "update_status",
                "old_status": old_status.value,
                "new_status": new_status.value
            }
            
        except Exception as e:
            logger.error(f"Failed to execute update status step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_update_priority_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute update priority step"""
        try:
            new_priority = TicketPriority(step["priority"])
            old_priority = ticket.priority
            ticket.priority = new_priority
            
            await session.commit()
            
            return {
                "success": True,
                "action": "update_priority",
                "old_priority": old_priority.value,
                "new_priority": new_priority.value
            }
            
        except Exception as e:
            logger.error(f"Failed to execute update priority step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_add_tag_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute add tag step"""
        try:
            tags_to_add = step.get("tags", [])
            if not isinstance(tags_to_add, list):
                tags_to_add = [tags_to_add]
            
            current_tags = ticket.tags or []
            new_tags = list(set(current_tags + tags_to_add))
            ticket.tags = new_tags
            
            await session.commit()
            
            return {
                "success": True,
                "action": "add_tag",
                "added_tags": tags_to_add,
                "total_tags": new_tags
            }
            
        except Exception as e:
            logger.error(f"Failed to execute add tag step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_send_notification_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute send notification step"""
        try:
            notification_type = step.get("notification_type")
            channels = step.get("channels", ["slack"])
            
            # Integrate with the notifications service
            try:
                from .real_time_notifications_service import RealTimeNotificationsService
                notification_service = RealTimeNotificationsService()
                
                # Prepare notification data
                notification_data = {
                    "title": f"Workflow Notification: {notification_type}",
                    "message": f"Workflow triggered notification for ticket #{ticket.ticket_number}",
                    "ticket_id": ticket.id,
                    "priority": ticket.priority,
                    "channels": channels
                }
                
                # Send notification
                result = await notification_service.send_notification(
                    rule_name=f"workflow_{notification_type}",
                    notification_data=notification_data
                )
                
                return {
                    "success": result.get("success", False),
                    "action": "send_notification",
                    "notification_type": notification_type,
                    "channels": channels,
                    "notification_result": result
                }
                
            except Exception as notification_error:
                logger.error(f"Failed to send workflow notification: {notification_error}")
                return {
                    "success": False,
                    "action": "send_notification",
                    "error": str(notification_error)
                }
            
        except Exception as e:
            logger.error(f"Failed to execute send notification step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_create_follow_up_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute create follow up step"""
        try:
            follow_up_days = step.get("follow_up_days", 7)
            follow_up_date = datetime.utcnow() + timedelta(days=follow_up_days)
            
            # Create follow-up ticket
            follow_up_ticket = SupportTicket(
                customer_id=ticket.customer_id,
                channel=ticket.channel,
                priority=ticket.priority,
                category=ticket.category,
                subject=f"Follow-up: {ticket.subject}",
                description=f"Follow-up for ticket #{ticket.ticket_number}",
                metadata={
                    "parent_ticket_id": ticket.id,
                    "follow_up_date": follow_up_date.isoformat(),
                    "workflow_generated": True
                }
            )
            
            session.add(follow_up_ticket)
            await session.commit()
            
            return {
                "success": True,
                "action": "create_follow_up",
                "follow_up_ticket_id": follow_up_ticket.id,
                "follow_up_date": follow_up_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute create follow up step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_escalate_ticket_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute escalate ticket step"""
        try:
            escalation_reason = step.get("reason", "Workflow escalation")
            escalated_to_agent_id = step.get("escalated_to_agent_id")
            
            # Update ticket status
            ticket.status = TicketStatus.ESCALATED
            
            # Create escalation record
            escalation = TicketEscalation(
                ticket_id=ticket.id,
                escalated_to_agent_id=escalated_to_agent_id,
                reason=escalation_reason,
                priority_increase=step.get("priority_increase", False)
            )
            
            session.add(escalation)
            await session.commit()
            
            return {
                "success": True,
                "action": "escalate_ticket",
                "escalation_reason": escalation_reason,
                "escalated_to_agent_id": escalated_to_agent_id
            }
            
        except Exception as e:
            logger.error(f"Failed to execute escalate ticket step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_update_sla_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute update SLA step"""
        try:
            new_sla = step.get("sla_minutes")
            if new_sla:
                ticket.estimated_resolution_time = new_sla
            
            await session.commit()
            
            return {
                "success": True,
                "action": "update_sla",
                "new_sla_minutes": new_sla
            }
            
        except Exception as e:
            logger.error(f"Failed to execute update SLA step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_add_note_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute add note step"""
        try:
            note_content = step.get("note", "")
            note_author = step.get("author", "Workflow System")
            
            # Add note to ticket metadata
            current_notes = ticket.metadata.get("notes", [])
            new_note = {
                "content": note_content,
                "author": note_author,
                "timestamp": datetime.utcnow().isoformat()
            }
            current_notes.append(new_note)
            
            ticket.metadata = {
                **ticket.metadata,
                "notes": current_notes
            }
            
            await session.commit()
            
            return {
                "success": True,
                "action": "add_note",
                "note_content": note_content,
                "note_author": note_author
            }
            
        except Exception as e:
            logger.error(f"Failed to execute add note step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_trigger_webhook_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute trigger webhook step"""
        try:
            webhook_url = step.get("webhook_url")
            webhook_data = step.get("data", {})
            
            # Prepare webhook payload
            payload = {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "customer_id": ticket.customer_id,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "subject": ticket.subject,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "workflow_data": webhook_data,
                "context": context or {}
            }
            
            # Send webhook using actual HTTP client
            try:
                import httpx
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        return {
                            "success": True,
                            "action": "trigger_webhook",
                            "webhook_url": webhook_url,
                            "payload": payload,
                            "response_status": response.status_code,
                            "response_body": response.text
                        }
                    else:
                        return {
                            "success": False,
                            "action": "trigger_webhook",
                            "webhook_url": webhook_url,
                            "error": f"Webhook failed with status {response.status_code}",
                            "response_body": response.text
                        }
                        
            except Exception as webhook_error:
                logger.error(f"Webhook error: {webhook_error}")
                return {
                    "success": False,
                    "action": "trigger_webhook",
                    "webhook_url": webhook_url,
                    "error": str(webhook_error)
                }
            
        except Exception as e:
            logger.error(f"Failed to execute trigger webhook step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_send_email_step(
        self,
        step: Dict[str, Any],
        ticket: SupportTicket,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute send email step"""
        try:
            template_id = step.get("template_id")
            email_content = step.get("email_content")
            recipients = step.get("recipients", [])
            
            # Integrate with email service
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                # Get SMTP configuration
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                smtp_username = os.getenv("SMTP_USERNAME")
                smtp_password = os.getenv("SMTP_PASSWORD")
                
                if not all([smtp_username, smtp_password]):
                    return {
                        "success": False,
                        "action": "send_email",
                        "error": "SMTP credentials not configured"
                    }
                
                # Create email message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = ", ".join(recipients)
                msg['Subject'] = f"Workflow Email: {ticket.subject}"
                
                # Use template or direct content
                if template_id:
                    # Load template from database
                    template = await self._get_email_template(template_id)
                    if template:
                        email_content = template.format(**{
                            "ticket_id": ticket.id,
                            "customer_name": ticket.customer.name if ticket.customer else "Customer",
                            "subject": ticket.subject,
                            "status": ticket.status.value
                        })
                
                msg.attach(MIMEText(email_content, 'plain'))
                
                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                return {
                    "success": True,
                    "action": "send_email",
                    "template_id": template_id,
                    "recipients": recipients,
                    "message": "Email sent successfully"
                }
                
            except Exception as email_error:
                logger.error(f"Email error: {email_error}")
                return {
                    "success": False,
                    "action": "send_email",
                    "error": str(email_error)
                }
            
        except Exception as e:
            logger.error(f"Failed to execute send email step: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_customer_profile(self, customer_id: int) -> Optional[CustomerProfile]:
        """Get customer profile"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                profile_query = select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                profile_result = await session.execute(profile_query)
                return profile_result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get customer profile: {e}")
            return None
    
    async def _find_agent_by_criteria(
        self,
        criteria: Dict[str, Any],
        session: AsyncSession
    ) -> Optional[SupportAgent]:
        """Find agent based on criteria"""
        try:
            query = select(SupportAgent).where(SupportAgent.availability_status == "available")
            
            if "skills" in criteria:
                required_skills = criteria["skills"]
                query = query.where(SupportAgent.skills.contains(required_skills))
            
            if "specializations" in criteria:
                required_specializations = criteria["specializations"]
                query = query.where(SupportAgent.specializations.contains(required_specializations))
            
            if "max_tickets" in criteria:
                max_tickets = criteria["max_tickets"]
                query = query.where(SupportAgent.current_ticket_count < max_tickets)
            
            # Order by performance score and current ticket count
            query = query.order_by(SupportAgent.performance_score.desc(), SupportAgent.current_ticket_count.asc())
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to find agent by criteria: {e}")
            return None
    
    async def _load_workflows_from_database(self):
        """Load workflows from database into cache"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                workflows_query = select(SupportWorkflow).where(SupportWorkflow.is_active == True)
                workflows_result = await session.execute(workflows_query)
                workflows = workflows_result.scalars().all()
                
                for workflow in workflows:
                    self._workflow_cache[workflow.id] = {
                        "id": workflow.id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "category": workflow.category.value,
                        "priority": workflow.priority.value,
                        "steps": workflow.steps,
                        "auto_assign": workflow.auto_assign,
                        "auto_assign_agent_id": workflow.auto_assign_agent_id,
                        "sla_target": workflow.sla_target,
                        "escalation_rules": workflow.escalation_rules,
                        "is_active": workflow.is_active,
                        "created_at": workflow.created_at,
                        "updated_at": workflow.updated_at
                    }
                    
        except Exception as e:
            logger.error(f"Failed to load workflows from database: {e}")
