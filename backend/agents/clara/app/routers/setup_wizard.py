from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_clara_database, get_db
from ..services.setup_wizard_service import SetupWizardService
from ..schemas.setup_wizard import (
    CreateSetupWizardStepRequest, UpdateSetupWizardStepRequest,
    CreateSetupWizardSessionRequest, UpdateSetupWizardSessionRequest,
    CreateSetupWizardConfigRequest, UpdateSetupWizardConfigRequest,
    CreateSetupWizardValidationRequest, UpdateSetupWizardValidationRequest,
    SetupWizardStepResponse, SetupWizardSessionResponse, SetupWizardConfigResponse,
    SetupWizardValidationResponse, SetupWizardAnalyticsResponse
)

router = APIRouter()
setup_wizard_service = SetupWizardService()


@router.post("/steps", response_model=SetupWizardStepResponse)
async def create_setup_wizard_step(
    request: CreateSetupWizardStepRequest,
    db: Session = Depends(get_db)
):
    """Create a new setup wizard step"""
    return await setup_wizard_service.create_setup_wizard_step(db, request)


@router.get("/steps/{step_id}", response_model=SetupWizardStepResponse)
async def get_setup_wizard_step(
    step_id: int,
    db: Session = Depends(get_db)
):
    """Get setup wizard step by ID"""
    return await setup_wizard_service.get_setup_wizard_step(db, step_id)


@router.get("/steps", response_model=List[SetupWizardStepResponse])
async def list_setup_wizard_steps(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    step_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List setup wizard steps"""
    return await setup_wizard_service.list_setup_wizard_steps(
        db, skip=skip, limit=limit, step_type=step_type, is_active=is_active
    )


@router.put("/steps/{step_id}", response_model=SetupWizardStepResponse)
async def update_setup_wizard_step(
    step_id: int,
    request: UpdateSetupWizardStepRequest,
    db: Session = Depends(get_db)
):
    """Update setup wizard step"""
    return await setup_wizard_service.update_setup_wizard_step(db, step_id, request)


@router.delete("/steps/{step_id}")
async def delete_setup_wizard_step(
    step_id: int,
    db: Session = Depends(get_db)
):
    """Delete setup wizard step"""
    return await setup_wizard_service.delete_setup_wizard_step(db, step_id)


@router.get("/steps/{step_id}/next", response_model=SetupWizardStepResponse)
async def get_next_step(
    step_id: int,
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Get the next setup wizard step for a user"""
    return await setup_wizard_service.get_next_step(db, step_id, user_id)


@router.post("/steps/{step_id}/validate")
async def validate_step_data(
    step_id: int,
    request: CreateSetupWizardValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate step data"""
    return await setup_wizard_service.validate_step_data(db, step_id, request)


@router.post("/sessions", response_model=SetupWizardSessionResponse)
async def create_setup_wizard_session(
    request: CreateSetupWizardSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new setup wizard session"""
    return await setup_wizard_service.create_setup_wizard_session(db, request)


@router.get("/sessions/{session_id}", response_model=SetupWizardSessionResponse)
async def get_setup_wizard_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get setup wizard session by ID"""
    return await setup_wizard_service.get_setup_wizard_session(db, session_id)


@router.get("/sessions", response_model=List[SetupWizardSessionResponse])
async def list_setup_wizard_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List setup wizard sessions"""
    return await setup_wizard_service.list_setup_wizard_sessions(
        db, skip=skip, limit=limit, user_id=user_id, status=status
    )


@router.put("/sessions/{session_id}", response_model=SetupWizardSessionResponse)
async def update_setup_wizard_session(
    session_id: int,
    request: UpdateSetupWizardSessionRequest,
    db: Session = Depends(get_db)
):
    """Update setup wizard session"""
    return await setup_wizard_service.update_setup_wizard_session(db, session_id, request)


@router.delete("/sessions/{session_id}")
async def delete_setup_wizard_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete setup wizard session"""
    return await setup_wizard_service.delete_setup_wizard_session(db, session_id)


@router.post("/configs", response_model=SetupWizardConfigResponse)
async def create_setup_wizard_config(
    request: CreateSetupWizardConfigRequest,
    db: Session = Depends(get_db)
):
    """Create a new setup wizard configuration"""
    return await setup_wizard_service.create_setup_wizard_config(db, request)


@router.get("/configs/{config_id}", response_model=SetupWizardConfigResponse)
async def get_setup_wizard_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get setup wizard configuration by ID"""
    return await setup_wizard_service.get_setup_wizard_config(db, config_id)


@router.get("/configs", response_model=List[SetupWizardConfigResponse])
async def list_setup_wizard_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    config_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List setup wizard configurations"""
    return await setup_wizard_service.list_setup_wizard_configs(
        db, skip=skip, limit=limit, config_type=config_type, is_active=is_active
    )


@router.put("/configs/{config_id}", response_model=SetupWizardConfigResponse)
async def update_setup_wizard_config(
    config_id: int,
    request: UpdateSetupWizardConfigRequest,
    db: Session = Depends(get_db)
):
    """Update setup wizard configuration"""
    return await setup_wizard_service.update_setup_wizard_config(db, config_id, request)


@router.delete("/configs/{config_id}")
async def delete_setup_wizard_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete setup wizard configuration"""
    return await setup_wizard_service.delete_setup_wizard_config(db, config_id)


@router.post("/configs/{config_id}/test")
async def test_integration(
    config_id: int,
    integration_type: str = Query(...),
    db: Session = Depends(get_db)
):
    """Test integration configuration"""
    return await setup_wizard_service.test_integration(db, config_id, integration_type)


@router.post("/validations", response_model=SetupWizardValidationResponse)
async def create_setup_wizard_validation(
    request: CreateSetupWizardValidationRequest,
    db: Session = Depends(get_db)
):
    """Create a new setup wizard validation"""
    return await setup_wizard_service.create_setup_wizard_validation(db, request)


@router.get("/validations/{validation_id}", response_model=SetupWizardValidationResponse)
async def get_setup_wizard_validation(
    validation_id: int,
    db: Session = Depends(get_db)
):
    """Get setup wizard validation by ID"""
    return await setup_wizard_service.get_setup_wizard_validation(db, validation_id)


@router.get("/validations", response_model=List[SetupWizardValidationResponse])
async def list_setup_wizard_validations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    validation_type: Optional[str] = Query(None),
    is_valid: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List setup wizard validations"""
    return await setup_wizard_service.list_setup_wizard_validations(
        db, skip=skip, limit=limit, validation_type=validation_type, is_valid=is_valid
    )


@router.put("/validations/{validation_id}", response_model=SetupWizardValidationResponse)
async def update_setup_wizard_validation(
    validation_id: int,
    request: UpdateSetupWizardValidationRequest,
    db: Session = Depends(get_db)
):
    """Update setup wizard validation"""
    return await setup_wizard_service.update_setup_wizard_validation(db, validation_id, request)


@router.delete("/validations/{validation_id}")
async def delete_setup_wizard_validation(
    validation_id: int,
    db: Session = Depends(get_db)
):
    """Delete setup wizard validation"""
    return await setup_wizard_service.delete_setup_wizard_validation(db, validation_id)


@router.get("/analytics", response_model=SetupWizardAnalyticsResponse)
async def get_setup_wizard_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get setup wizard analytics"""
    return await setup_wizard_service.get_setup_wizard_analytics(db, start_date, end_date, user_id)


@router.get("/health")
async def health_check():
    """Check the health of setup wizard system"""
    return await setup_wizard_service.health_check()
