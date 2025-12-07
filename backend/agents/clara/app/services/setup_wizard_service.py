from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    SetupWizardStep, SetupWizardSession, SetupWizardConfig, SetupWizardValidation,
    SupportAgent, CustomerProfile, SupportTicket
)
from ..schemas.setup_wizard import (
    CreateSetupWizardStepRequest, UpdateSetupWizardStepRequest,
    CreateSetupWizardSessionRequest, UpdateSetupWizardSessionRequest,
    CreateSetupWizardConfigRequest, UpdateSetupWizardConfigRequest,
    SetupWizardStepResponse, SetupWizardSessionResponse, SetupWizardConfigResponse,
    SetupWizardValidationResponse, SetupWizardAnalyticsResponse
)
from ..database import get_clara_database
from backend.core.config import settings
from backend.core.integrations import IntegrationManager
from backend.core.analytics import AnalyticsManager
# NLPUtils removed - not used


class SetupWizardStepType(str, Enum):
    WELCOME = "welcome"
    ACCOUNT_INFO = "account_info"
    INTEGRATION_SETUP = "integration_setup"
    CONFIGURATION = "configuration"
    TESTING = "testing"
    COMPLETION = "completion"


class SetupWizardStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SetupWizardValidationType(str, Enum):
    REQUIRED_FIELD = "required_field"
    EMAIL_FORMAT = "email_format"
    URL_FORMAT = "url_format"
    API_KEY = "api_key"
    CONNECTION_TEST = "connection_test"


class SetupWizardService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_setup_wizard_step(
        self, 
        db: Session, 
        request: CreateSetupWizardStepRequest
    ) -> SetupWizardStepResponse:
        """Create a new setup wizard step"""
        try:
            step = SetupWizardStep(
                title=request.title,
                description=request.description,
                step_type=request.step_type,
                content=request.content,
                order_index=request.order_index,
                is_required=request.is_required,
                validation_rules=request.validation_rules,
                help_text=request.help_text,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(step)
            db.commit()
            db.refresh(step)
            
            return SetupWizardStepResponse(
                id=step.id,
                title=step.title,
                description=step.description,
                step_type=step.step_type,
                content=step.content,
                order_index=step.order_index,
                is_required=step.is_required,
                validation_rules=step.validation_rules,
                help_text=step.help_text,
                is_active=step.is_active,
                created_at=step.created_at,
                updated_at=step.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create setup wizard step: {str(e)}")
    
    async def get_setup_wizard_step(
        self, 
        db: Session, 
        step_id: int
    ) -> SetupWizardStepResponse:
        """Get setup wizard step by ID"""
        step = db.query(SetupWizardStep).filter(SetupWizardStep.id == step_id).first()
        if not step:
            raise HTTPException(status_code=404, detail="Setup wizard step not found")
        
        return SetupWizardStepResponse(
            id=step.id,
            title=step.title,
            description=step.description,
            step_type=step.step_type,
            content=step.content,
            order_index=step.order_index,
            is_required=step.is_required,
            validation_rules=step.validation_rules,
            help_text=step.help_text,
            is_active=step.is_active,
            created_at=step.created_at,
            updated_at=step.updated_at
        )
    
    async def list_setup_wizard_steps(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        step_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[SetupWizardStepResponse]:
        """List setup wizard steps"""
        query = db.query(SetupWizardStep)
        
        if step_type:
            query = query.filter(SetupWizardStep.step_type == step_type)
        if is_active is not None:
            query = query.filter(SetupWizardStep.is_active == is_active)
        
        steps = query.order_by(SetupWizardStep.order_index).offset(skip).limit(limit).all()
        
        return [
            SetupWizardStepResponse(
                id=step.id,
                title=step.title,
                description=step.description,
                step_type=step.step_type,
                content=step.content,
                order_index=step.order_index,
                is_required=step.is_required,
                validation_rules=step.validation_rules,
                help_text=step.help_text,
                is_active=step.is_active,
                created_at=step.created_at,
                updated_at=step.updated_at
            ) for step in steps
        ]
    
    async def update_setup_wizard_step(
        self, 
        db: Session, 
        step_id: int, 
        request: UpdateSetupWizardStepRequest
    ) -> SetupWizardStepResponse:
        """Update setup wizard step"""
        step = db.query(SetupWizardStep).filter(SetupWizardStep.id == step_id).first()
        if not step:
            raise HTTPException(status_code=404, detail="Setup wizard step not found")
        
        try:
            if request.title is not None:
                step.title = request.title
            if request.description is not None:
                step.description = request.description
            if request.step_type is not None:
                step.step_type = request.step_type
            if request.content is not None:
                step.content = request.content
            if request.order_index is not None:
                step.order_index = request.order_index
            if request.is_required is not None:
                step.is_required = request.is_required
            if request.validation_rules is not None:
                step.validation_rules = request.validation_rules
            if request.help_text is not None:
                step.help_text = request.help_text
            if request.is_active is not None:
                step.is_active = request.is_active
            
            step.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(step)
            
            return SetupWizardStepResponse(
                id=step.id,
                title=step.title,
                description=step.description,
                step_type=step.step_type,
                content=step.content,
                order_index=step.order_index,
                is_required=step.is_required,
                validation_rules=step.validation_rules,
                help_text=step.help_text,
                is_active=step.is_active,
                created_at=step.created_at,
                updated_at=step.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update setup wizard step: {str(e)}")
    
    async def delete_setup_wizard_step(
        self, 
        db: Session, 
        step_id: int
    ) -> Dict[str, str]:
        """Delete setup wizard step"""
        step = db.query(SetupWizardStep).filter(SetupWizardStep.id == step_id).first()
        if not step:
            raise HTTPException(status_code=404, detail="Setup wizard step not found")
        
        try:
            db.delete(step)
            db.commit()
            return {"message": "Setup wizard step deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete setup wizard step: {str(e)}")
    
    async def create_setup_wizard_session(
        self, 
        db: Session, 
        request: CreateSetupWizardSessionRequest
    ) -> SetupWizardSessionResponse:
        """Create a new setup wizard session"""
        try:
            session = SetupWizardSession(
                user_id=request.user_id,
                user_type=request.user_type,
                current_step_id=request.current_step_id,
                status=SetupWizardStatus.NOT_STARTED,
                configuration_data=request.configuration_data or {},
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return SetupWizardSessionResponse(
                id=session.id,
                user_id=session.user_id,
                user_type=session.user_type,
                current_step_id=session.current_step_id,
                status=session.status,
                configuration_data=session.configuration_data,
                started_at=session.started_at,
                completed_at=session.completed_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create setup wizard session: {str(e)}")
    
    async def get_setup_wizard_session(
        self, 
        db: Session, 
        session_id: int
    ) -> SetupWizardSessionResponse:
        """Get setup wizard session by ID"""
        session = db.query(SetupWizardSession).filter(SetupWizardSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Setup wizard session not found")
        
        return SetupWizardSessionResponse(
            id=session.id,
            user_id=session.user_id,
            user_type=session.user_type,
            current_step_id=session.current_step_id,
            status=session.status,
            configuration_data=session.configuration_data,
            started_at=session.started_at,
            completed_at=session.completed_at,
            updated_at=session.updated_at
        )
    
    async def update_setup_wizard_session(
        self, 
        db: Session, 
        session_id: int, 
        request: UpdateSetupWizardSessionRequest
    ) -> SetupWizardSessionResponse:
        """Update setup wizard session"""
        session = db.query(SetupWizardSession).filter(SetupWizardSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Setup wizard session not found")
        
        try:
            if request.current_step_id is not None:
                session.current_step_id = request.current_step_id
            if request.status is not None:
                session.status = request.status
                if request.status == SetupWizardStatus.COMPLETED:
                    session.completed_at = datetime.utcnow()
            if request.configuration_data is not None:
                session.configuration_data = request.configuration_data
            
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            return SetupWizardSessionResponse(
                id=session.id,
                user_id=session.user_id,
                user_type=session.user_type,
                current_step_id=session.current_step_id,
                status=session.status,
                configuration_data=session.configuration_data,
                started_at=session.started_at,
                completed_at=session.completed_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update setup wizard session: {str(e)}")
    
    async def get_next_step(
        self, 
        db: Session, 
        session_id: int
    ) -> Optional[SetupWizardStepResponse]:
        """Get the next step for a setup wizard session"""
        session = db.query(SetupWizardSession).filter(SetupWizardSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Setup wizard session not found")
        
        if session.current_step_id:
            current_step = db.query(SetupWizardStep).filter(SetupWizardStep.id == session.current_step_id).first()
            if current_step:
                next_step = db.query(SetupWizardStep).filter(
                    and_(
                        SetupWizardStep.order_index > current_step.order_index,
                        SetupWizardStep.is_active == True
                    )
                ).order_by(SetupWizardStep.order_index).first()
                
                if next_step:
                    return SetupWizardStepResponse(
                        id=next_step.id,
                        title=next_step.title,
                        description=next_step.description,
                        step_type=next_step.step_type,
                        content=next_step.content,
                        order_index=next_step.order_index,
                        is_required=next_step.is_required,
                        validation_rules=next_step.validation_rules,
                        help_text=next_step.help_text,
                        is_active=next_step.is_active,
                        created_at=next_step.created_at,
                        updated_at=next_step.updated_at
                    )
        else:
            # Get first step
            first_step = db.query(SetupWizardStep).filter(
                SetupWizardStep.is_active == True
            ).order_by(SetupWizardStep.order_index).first()
            
            if first_step:
                return SetupWizardStepResponse(
                    id=first_step.id,
                    title=first_step.title,
                    description=first_step.description,
                    step_type=first_step.step_type,
                    content=first_step.content,
                    order_index=first_step.order_index,
                    is_required=first_step.is_required,
                    validation_rules=first_step.validation_rules,
                    help_text=first_step.help_text,
                    is_active=first_step.is_active,
                    created_at=first_step.created_at,
                    updated_at=first_step.updated_at
                )
        
        return None
    
    async def validate_step_data(
        self, 
        db: Session, 
        step_id: int,
        data: Dict[str, Any]
    ) -> List[SetupWizardValidationResponse]:
        """Validate data for a setup wizard step"""
        try:
            step = db.query(SetupWizardStep).filter(SetupWizardStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Setup wizard step not found")
            
            validations = []
            
            if step.validation_rules:
                for rule in step.validation_rules:
                    validation_result = await self._validate_field(rule, data)
                    if validation_result:
                        validations.append(validation_result)
            
            return validations
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to validate step data: {str(e)}")
    
    async def create_setup_wizard_config(
        self, 
        db: Session, 
        request: CreateSetupWizardConfigRequest
    ) -> SetupWizardConfigResponse:
        """Create a new setup wizard configuration"""
        try:
            config = SetupWizardConfig(
                name=request.name,
                description=request.description,
                configuration_data=request.configuration_data,
                user_id=request.user_id,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
            
            return SetupWizardConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                configuration_data=config.configuration_data,
                user_id=config.user_id,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create setup wizard config: {str(e)}")
    
    async def get_setup_wizard_config(
        self, 
        db: Session, 
        config_id: int
    ) -> SetupWizardConfigResponse:
        """Get setup wizard configuration by ID"""
        config = db.query(SetupWizardConfig).filter(SetupWizardConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Setup wizard configuration not found")
        
        return SetupWizardConfigResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            configuration_data=config.configuration_data,
            user_id=config.user_id,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    
    async def list_setup_wizard_configs(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[SetupWizardConfigResponse]:
        """List setup wizard configurations"""
        query = db.query(SetupWizardConfig)
        
        if user_id:
            query = query.filter(SetupWizardConfig.user_id == user_id)
        if is_active is not None:
            query = query.filter(SetupWizardConfig.is_active == is_active)
        
        configs = query.offset(skip).limit(limit).all()
        
        return [
            SetupWizardConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                configuration_data=config.configuration_data,
                user_id=config.user_id,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at
            ) for config in configs
        ]
    
    async def update_setup_wizard_config(
        self, 
        db: Session, 
        config_id: int, 
        request: UpdateSetupWizardConfigRequest
    ) -> SetupWizardConfigResponse:
        """Update setup wizard configuration"""
        config = db.query(SetupWizardConfig).filter(SetupWizardConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Setup wizard configuration not found")
        
        try:
            if request.name is not None:
                config.name = request.name
            if request.description is not None:
                config.description = request.description
            if request.configuration_data is not None:
                config.configuration_data = request.configuration_data
            if request.is_active is not None:
                config.is_active = request.is_active
            
            config.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(config)
            
            return SetupWizardConfigResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                configuration_data=config.configuration_data,
                user_id=config.user_id,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update setup wizard config: {str(e)}")
    
    async def delete_setup_wizard_config(
        self, 
        db: Session, 
        config_id: int
    ) -> Dict[str, str]:
        """Delete setup wizard configuration"""
        config = db.query(SetupWizardConfig).filter(SetupWizardConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Setup wizard configuration not found")
        
        try:
            db.delete(config)
            db.commit()
            return {"message": "Setup wizard configuration deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete setup wizard config: {str(e)}")
    
    async def test_integration(
        self, 
        db: Session, 
        integration_type: str,
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test integration configuration"""
        try:
            if integration_type == "email":
                return await self._test_email_integration(config_data)
            elif integration_type == "crm":
                return await self._test_crm_integration(config_data)
            elif integration_type == "api":
                return await self._test_api_integration(config_data)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported integration type: {integration_type}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to test integration: {str(e)}")
    
    async def get_setup_wizard_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> SetupWizardAnalyticsResponse:
        """Get setup wizard analytics"""
        try:
            # Get sessions in date range
            sessions = db.query(SetupWizardSession).filter(
                and_(
                    SetupWizardSession.started_at >= start_date,
                    SetupWizardSession.started_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.status == SetupWizardStatus.COMPLETED])
            failed_sessions = len([s for s in sessions if s.status == SetupWizardStatus.FAILED])
            in_progress_sessions = len([s for s in sessions if s.status == SetupWizardStatus.IN_PROGRESS])
            
            # Calculate average completion time
            completion_times = []
            for session in sessions:
                if session.status == SetupWizardStatus.COMPLETED and session.completed_at:
                    duration = (session.completed_at - session.started_at).total_seconds() / 60  # minutes
                    completion_times.append(duration)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Step completion rates
            step_completion_rates = {}
            steps = db.query(SetupWizardStep).filter(SetupWizardStep.is_active == True).all()
            
            for step in steps:
                step_sessions = [s for s in sessions if s.current_step_id == step.id]
                if step_sessions:
                    step_completion_rates[step.title] = len(step_sessions) / total_sessions
            
            return SetupWizardAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_sessions=total_sessions,
                completed_sessions=completed_sessions,
                failed_sessions=failed_sessions,
                in_progress_sessions=in_progress_sessions,
                completion_rate=completed_sessions / total_sessions if total_sessions > 0 else 0,
                failure_rate=failed_sessions / total_sessions if total_sessions > 0 else 0,
                avg_completion_time_minutes=avg_completion_time,
                step_completion_rates=step_completion_rates
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get setup wizard analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of setup wizard system"""
        try:
            db = next(get_db())
            step_count = db.query(SetupWizardStep).count()
            session_count = db.query(SetupWizardSession).count()
            config_count = db.query(SetupWizardConfig).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "steps_count": step_count,
                    "sessions_count": session_count,
                    "configs_count": config_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _validate_field(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Optional[SetupWizardValidationResponse]:
        """Validate a single field based on rule"""
        try:
            field_name = rule.get("field")
            validation_type = rule.get("type")
            value = data.get(field_name)
            
            if validation_type == SetupWizardValidationType.REQUIRED_FIELD:
                if not value or value.strip() == "":
                    return SetupWizardValidationResponse(
                        field_name=field_name,
                        validation_type=validation_type,
                        is_valid=False,
                        error_message=f"{field_name} is required"
                    )
            
            elif validation_type == SetupWizardValidationType.EMAIL_FORMAT:
                if value and not self._is_valid_email(value):
                    return SetupWizardValidationResponse(
                        field_name=field_name,
                        validation_type=validation_type,
                        is_valid=False,
                        error_message=f"{field_name} must be a valid email address"
                    )
            
            elif validation_type == SetupWizardValidationType.URL_FORMAT:
                if value and not self._is_valid_url(value):
                    return SetupWizardValidationResponse(
                        field_name=field_name,
                        validation_type=validation_type,
                        is_valid=False,
                        error_message=f"{field_name} must be a valid URL"
                    )
            
            elif validation_type == SetupWizardValidationType.API_KEY:
                if value and not self._is_valid_api_key(value):
                    return SetupWizardValidationResponse(
                        field_name=field_name,
                        validation_type=validation_type,
                        is_valid=False,
                        error_message=f"{field_name} must be a valid API key"
                    )
            
            return SetupWizardValidationResponse(
                field_name=field_name,
                validation_type=validation_type,
                is_valid=True,
                error_message=None
            )
            
        except Exception:
            return SetupWizardValidationResponse(
                field_name=field_name,
                validation_type=validation_type,
                is_valid=False,
                error_message="Validation failed"
            )
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        import re
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    def _is_valid_api_key(self, api_key: str) -> bool:
        """Check if API key is valid"""
        return len(api_key) >= 10 and api_key.isalnum()
    
    async def _test_email_integration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test email integration"""
        try:
            # Test email configuration
            test_result = await self.integration_manager.test_email_config(config_data)
            return {
                "success": test_result.get("success", False),
                "message": test_result.get("message", "Email integration test completed"),
                "details": test_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Email integration test failed: {str(e)}",
                "details": {}
            }
    
    async def _test_crm_integration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test CRM integration"""
        try:
            # Test CRM configuration
            test_result = await self.integration_manager.test_crm_config(config_data)
            return {
                "success": test_result.get("success", False),
                "message": test_result.get("message", "CRM integration test completed"),
                "details": test_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"CRM integration test failed: {str(e)}",
                "details": {}
            }
    
    async def _test_api_integration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test API integration"""
        try:
            # Test API configuration
            test_result = await self.integration_manager.test_api_config(config_data)
            return {
                "success": test_result.get("success", False),
                "message": test_result.get("message", "API integration test completed"),
                "details": test_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"API integration test failed: {str(e)}",
                "details": {}
            }
