from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.integrations.models import IntegrationType, IntegrationStatus, CredentialStatus
from backend.core.authentication.auth_manager import get_current_user
from backend.core.user_management.user_manager import User

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

class IntegrationResponse(BaseModel):
    id: int
    name: str
    display_name: str
    integration_type: str
    description: str
    provider: str
    api_version: str
    base_url: str
    status: str
    pricing_tier: str
    rate_limits: Dict[str, Any]
    supported_features: Dict[str, Any]
    authentication_methods: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class IntegrationUsageResponse(BaseModel):
    id: int
    user_id: int
    integration_id: int
    integration_name: str
    status: str
    connected_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    error_count: int
    success_rate: float
    credentials_status: str
    metadata: Optional[Dict[str, Any]]

class IntegrationStatsResponse(BaseModel):
    total_integrations: int
    connected_count: int
    available_count: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    total_usage: int
    success_rate: float
    error_rate: float

@router.get("/", response_model=List[IntegrationResponse])
async def get_available_integrations(
    integration_type: Optional[str] = Query(None, description="Filter by integration type"),
    current_user: User = Depends(get_current_user)
):
    """Get all available integrations"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        integrations = await integration_manager.get_available_integrations(
            integration_type=integration_type
        )
        
        return [
            IntegrationResponse(
                id=integration.id,
                name=integration.name,
                display_name=integration.display_name,
                integration_type=integration.integration_type.value,
                description=integration.description,
                provider=integration.provider,
                api_version=integration.api_version,
                base_url=integration.base_url,
                status=integration.status.value,
                pricing_tier=integration.pricing_tier,
                rate_limits=integration.rate_limits,
                supported_features=integration.supported_features,
                authentication_methods=integration.authentication_methods,
                created_at=integration.created_at,
                updated_at=integration.updated_at
            )
            for integration in integrations
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integrations: {str(e)}"
        )

@router.get("/usage", response_model=List[IntegrationUsageResponse])
async def get_user_integration_usage(
    current_user: User = Depends(get_current_user)
):
    """Get user's integration usage"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        usage = await integration_manager.get_user_integration_usage(current_user.id)
        
        return [
            IntegrationUsageResponse(
                id=usage_item.id,
                user_id=usage_item.user_id,
                integration_id=usage_item.integration_id,
                integration_name=usage_item.integration_name,
                status=usage_item.status.value,
                connected_at=usage_item.connected_at,
                last_used=usage_item.last_used,
                usage_count=usage_item.usage_count,
                error_count=usage_item.error_count,
                success_rate=usage_item.success_rate,
                credentials_status=usage_item.credentials_status.value,
                metadata=usage_item.metadata
            )
            for usage_item in usage
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration usage: {str(e)}"
        )

@router.get("/stats", response_model=IntegrationStatsResponse)
async def get_integration_stats(
    current_user: User = Depends(get_current_user)
):
    """Get integration statistics for the user"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        stats = await integration_manager.get_integration_stats(current_user.id)
        
        return IntegrationStatsResponse(
            total_integrations=stats["total_integrations"],
            connected_count=stats["connected_count"],
            available_count=stats["available_count"],
            by_type=stats["by_type"],
            by_status=stats["by_status"],
            total_usage=stats["total_usage"],
            success_rate=stats["success_rate"],
            error_rate=stats["error_rate"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration stats: {str(e)}"
        )

@router.post("/connect")
async def connect_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user)
):
    """Connect an integration"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        result = await integration_manager.connect_integration(
            user_id=current_user.id,
            integration_id=integration_id
        )
        
        return {
            "success": True,
            "message": "Integration connected successfully",
            "usage_id": result.get("usage_id")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect integration: {str(e)}"
        )

@router.post("/disconnect")
async def disconnect_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user)
):
    """Disconnect an integration"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        success = await integration_manager.disconnect_integration(
            user_id=current_user.id,
            integration_id=integration_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration connection not found"
            )
        
        return {
            "success": True,
            "message": "Integration disconnected successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect integration: {str(e)}"
        )

@router.post("/test")
async def test_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user)
):
    """Test integration connection"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        result = await integration_manager.test_integration_connection(
            user_id=current_user.id,
            integration_id=integration_id
        )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result.get("details", {})
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test integration: {str(e)}"
        )

@router.get("/health")
async def get_integration_health(
    current_user: User = Depends(get_current_user)
):
    """Get health status of all connected integrations"""
    try:
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        health_status = await integration_manager.get_integration_health_status(current_user.id)
        
        return {
            "success": True,
            "health_status": health_status
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration health: {str(e)}"
        )
