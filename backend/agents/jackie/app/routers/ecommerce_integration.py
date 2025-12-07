from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.ecommerce_integration_service import EcommerceIntegrationService

router = APIRouter(prefix="/ecommerce", tags=["E-commerce Integration"])

class EcommerceConnectionRequest(BaseModel):
    platform: str
    credentials: Dict[str, Any]
    store_url: str
    integration_type: str = "full"


class ProductSyncRequest(BaseModel):
    product_data: Dict[str, Any]
    sync_type: str = "create"
    platform_specific: Optional[Dict[str, Any]] = Field(default_factory=dict)

@router.post("/connect")
async def connect_ecommerce_platform(
    request: EcommerceConnectionRequest,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.connect_ecommerce_platform(
            request.platform,
            request.credentials,
            request.store_url,
            request.integration_type
        )
        return {
            "message": f"Successfully connected to {request.platform}",
            "connection_id": result["connection_id"],
            "status": result["status"],
            "capabilities": result["capabilities"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_ecommerce_connections(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        connections = service.list_ecommerce_connections(platform, status)
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}")
async def get_ecommerce_connection(
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        connection = service.get_ecommerce_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        return connection
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{connection_id}")
async def disconnect_ecommerce_platform(
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.disconnect_ecommerce_platform(connection_id)
        if not result:
            raise HTTPException(status_code=404, detail="Connection not found")
        return {"message": "Successfully disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products/sync")
async def sync_products(
    request: ProductSyncRequest,
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_products(
            connection_id,
            request.product_data,
            request.sync_type,
            request.platform_specific
        )
        return {
            "message": "Product sync completed",
            "synced_products": result["synced_products"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{connection_id}")
async def get_products(
    connection_id: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        products = service.get_products(connection_id, category, status, limit, offset)
        return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{connection_id}/{product_id}")
async def get_product(
    connection_id: str,
    product_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        product = service.get_product(connection_id, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/sync")
async def sync_orders(
    connection_id: str,
    sync_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_orders(connection_id, sync_config)
        return {
            "message": "Order sync completed",
            "synced_orders": result["synced_orders"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{connection_id}")
async def get_orders(
    connection_id: str,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        orders = service.get_orders(connection_id, status, date_from, date_to, limit, offset)
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{connection_id}/{order_id}")
async def get_order(
    connection_id: str,
    order_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        order = service.get_order(connection_id, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customers/sync")
async def sync_customers(
    connection_id: str,
    sync_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_customers(connection_id, sync_config)
        return {
            "message": "Customer sync completed",
            "synced_customers": result["synced_customers"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{connection_id}")
async def get_customers(
    connection_id: str,
    segment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        customers = service.get_customers(connection_id, segment, limit, offset)
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{connection_id}/{customer_id}")
async def get_customer(
    connection_id: str,
    customer_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        customer = service.get_customer(connection_id, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/sync")
async def sync_inventory(
    connection_id: str,
    sync_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_inventory(connection_id, sync_config)
        return {
            "message": "Inventory sync completed",
            "synced_items": result["synced_items"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/{connection_id}")
async def get_inventory(
    connection_id: str,
    low_stock: bool = False,
    out_of_stock: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        inventory = service.get_inventory(connection_id, low_stock, out_of_stock, limit, offset)
        return {"inventory": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/sync")
async def sync_analytics(
    connection_id: str,
    analytics_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_analytics(connection_id, analytics_config)
        return {
            "message": "Analytics sync completed",
            "synced_data": result["synced_data"],
            "metrics": result["metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{connection_id}")
async def get_analytics(
    connection_id: str,
    metric_type: str,
    date_from: str,
    date_to: str,
    granularity: str = "daily",
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        analytics = service.get_analytics(connection_id, metric_type, date_from, date_to, granularity)
        return {"analytics": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/setup")
async def setup_webhooks(
    connection_id: str,
    webhook_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.setup_webhooks(connection_id, webhook_config)
        return {
            "message": "Webhooks setup completed",
            "webhook_urls": result["webhook_urls"],
            "events": result["events"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks/{connection_id}")
async def get_webhooks(
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        webhooks = service.get_webhooks(connection_id)
        return {"webhooks": webhooks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhooks/{connection_id}/{webhook_id}")
async def delete_webhook(
    connection_id: str,
    webhook_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.delete_webhook(connection_id, webhook_id)
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return {"message": "Webhook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/design/sync")
async def sync_design_assets(
    connection_id: str,
    design_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_design_assets(connection_id, design_config)
        return {
            "message": "Design assets sync completed",
            "synced_assets": result["synced_assets"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/design/{connection_id}")
async def get_design_assets(
    connection_id: str,
    asset_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        assets = service.get_design_assets(connection_id, asset_type, limit, offset)
        return {"assets": assets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/marketing/sync")
async def sync_marketing_data(
    connection_id: str,
    marketing_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.sync_marketing_data(connection_id, marketing_config)
        return {
            "message": "Marketing data sync completed",
            "synced_data": result["synced_data"],
            "campaigns": result["campaigns"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/marketing/{connection_id}")
async def get_marketing_data(
    connection_id: str,
    data_type: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        data = service.get_marketing_data(connection_id, data_type, date_from, date_to)
        return {"marketing_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/setup")
async def setup_automation(
    connection_id: str,
    automation_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.setup_automation(connection_id, automation_config)
        return {
            "message": "Automation setup completed",
            "automation_id": result["automation_id"],
            "triggers": result["triggers"],
            "actions": result["actions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automation/{connection_id}")
async def get_automations(
    connection_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        automations = service.get_automations(connection_id, status)
        return {"automations": automations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/{automation_id}/toggle")
async def toggle_automation(
    automation_id: str,
    enabled: bool,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.toggle_automation(automation_id, enabled)
        if not result:
            raise HTTPException(status_code=404, detail="Automation not found")
        return {"message": f"Automation {'enabled' if enabled else 'disabled'} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/schedule")
async def schedule_sync(
    connection_id: str,
    sync_schedule: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.schedule_sync(connection_id, sync_schedule)
        return {
            "message": "Sync schedule created",
            "schedule_id": result["schedule_id"],
            "next_sync": result["next_sync"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/schedules/{connection_id}")
async def get_sync_schedules(
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        schedules = service.get_sync_schedules(connection_id)
        return {"schedules": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sync/schedules/{schedule_id}")
async def delete_sync_schedule(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.delete_sync_schedule(schedule_id)
        if not result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Sync schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/supported")
async def get_supported_platforms(
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        platforms = service.get_supported_platforms()
        return {"platforms": platforms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/{platform}/capabilities")
async def get_platform_capabilities(
    platform: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        capabilities = service.get_platform_capabilities(platform)
        return {"capabilities": capabilities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_connection(
    platform: str,
    credentials: Dict[str, Any],
    store_url: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.test_connection(platform, credentials, store_url)
        return {
            "connection_test": result["connection_test"],
            "capabilities": result["capabilities"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/{connection_id}")
async def check_connection_health(
    connection_id: str,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        health = service.check_connection_health(connection_id)
        if not health:
            raise HTTPException(status_code=404, detail="Connection not found")
        return health
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup/create")
async def create_backup(
    connection_id: str,
    backup_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.create_backup(connection_id, backup_config)
        return {
            "message": "Backup created successfully",
            "backup_id": result["backup_id"],
            "backup_size": result["backup_size"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/{connection_id}")
async def get_backups(
    connection_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        backups = service.get_backups(connection_id, limit, offset)
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    restore_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = EcommerceIntegrationService(db)
    try:
        result = service.restore_backup(backup_id, restore_config)
        if not result:
            raise HTTPException(status_code=404, detail="Backup not found")
        return {"message": "Backup restored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
