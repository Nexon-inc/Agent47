import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieEcommerceConnection, JackieProductSync, OrderSync, CustomerSync, InventorySync

class EcommerceIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def connect_ecommerce_platform(self, platform: str, credentials: Dict[str, Any], 
                                 connection_name: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = str(uuid.uuid4())
        connection = JackieEcommerceConnection(
            id=connection_id, platform=platform, credentials=json.dumps(credentials),
            connection_name=connection_name, settings=json.dumps(settings),
            status="connected", created_at=datetime.utcnow()
        )
        self.db.add(connection)
        self.db.commit()
        return {"connection_id": connection_id, "platform": platform, "status": "connected"}
    
    def sync_products(self, connection_id: str, sync_options: Dict[str, Any]) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        sync_id = str(uuid.uuid4())
        sync_result = self.nlp_processor.sync_ecommerce_products(f"Platform: {connection.platform}, Options: {sync_options}")
        
        sync_record = JackieProductSync(
            id=sync_id, connection_id=connection_id, sync_type="products",
            sync_options=json.dumps(sync_options), sync_result=json.dumps(sync_result),
            status="completed", created_at=datetime.utcnow()
        )
        self.db.add(sync_record)
        self.db.commit()
        return {"sync_id": sync_id, "sync_type": "products", "status": "completed"}
    
    def sync_orders(self, connection_id: str, date_range: Dict[str, str], 
                   order_statuses: Optional[List[str]] = None) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        sync_id = str(uuid.uuid4())
        sync_result = self.nlp_processor.sync_ecommerce_orders(f"Platform: {connection.platform}, Date Range: {date_range}")
        
        sync_record = OrderSync(
            id=sync_id, connection_id=connection_id, sync_type="orders",
            date_range=json.dumps(date_range), order_statuses=json.dumps(order_statuses or []),
            sync_result=json.dumps(sync_result), status="completed", created_at=datetime.utcnow()
        )
        self.db.add(sync_record)
        self.db.commit()
        return {"sync_id": sync_id, "sync_type": "orders", "status": "completed"}
    
    def sync_customers(self, connection_id: str, customer_segments: Optional[List[str]] = None,
                      include_orders: bool = True) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        sync_id = str(uuid.uuid4())
        sync_result = self.nlp_processor.sync_ecommerce_customers(f"Platform: {connection.platform}, Segments: {customer_segments}")
        
        sync_record = CustomerSync(
            id=sync_id, connection_id=connection_id, sync_type="customers",
            customer_segments=json.dumps(customer_segments or []), include_orders=include_orders,
            sync_result=json.dumps(sync_result), status="completed", created_at=datetime.utcnow()
        )
        self.db.add(sync_record)
        self.db.commit()
        return {"sync_id": sync_id, "sync_type": "customers", "status": "completed"}
    
    def sync_inventory(self, connection_id: str, product_ids: Optional[List[str]] = None,
                      include_variants: bool = True) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        sync_id = str(uuid.uuid4())
        sync_result = self.nlp_processor.sync_ecommerce_inventory(f"Platform: {connection.platform}, Product IDs: {product_ids}")
        
        sync_record = InventorySync(
            id=sync_id, connection_id=connection_id, sync_type="inventory",
            product_ids=json.dumps(product_ids or []), include_variants=include_variants,
            sync_result=json.dumps(sync_result), status="completed", created_at=datetime.utcnow()
        )
        self.db.add(sync_record)
        self.db.commit()
        return {"sync_id": sync_id, "sync_type": "inventory", "status": "completed"}
    
    def get_ecommerce_analytics(self, connection_id: str, analytics_type: str,
                               date_range: Dict[str, str], metrics: List[str]) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        analytics_result = self.nlp_processor.get_ecommerce_analytics(f"Platform: {connection.platform}, Type: {analytics_type}")
        return {"connection_id": connection_id, "analytics_type": analytics_type, "analytics_data": analytics_result}
    
    def setup_webhooks(self, connection_id: str, webhook_config: Dict[str, Any]) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        webhook_result = self.nlp_processor.setup_ecommerce_webhooks(f"Platform: {connection.platform}, Config: {webhook_config}")
        return {"connection_id": connection_id, "webhook_result": webhook_result}
    
    def check_connection_health(self, connection_id: str) -> Dict[str, Any]:
        connection = self.db.query(JackieEcommerceConnection).filter(JackieEcommerceConnection.id == connection_id).first()
        if not connection:
            raise Exception("Ecommerce connection not found")
        
        health_result = self.nlp_processor.check_ecommerce_connection_health(f"Platform: {connection.platform}")
        connection.status = health_result.get("status", connection.status)
        connection.last_health_check = datetime.utcnow()
        self.db.commit()
        return {"connection_id": connection_id, "health_status": health_result}
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Shopify", "features": ["products", "orders", "customers", "inventory", "analytics"]},
            {"name": "WooCommerce", "features": ["products", "orders", "customers", "inventory", "analytics"]},
            {"name": "Magento", "features": ["products", "orders", "customers", "inventory", "analytics"]},
            {"name": "BigCommerce", "features": ["products", "orders", "customers", "inventory", "analytics"]}
        ]
    
    def batch_sync_data(self, connection_id: str, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        if sync_config.get("sync_products", False):
            results["products"] = self.sync_products(connection_id, sync_config.get("product_options", {}))
        if sync_config.get("sync_orders", False):
            results["orders"] = self.sync_orders(connection_id, sync_config.get("order_date_range", {}))
        if sync_config.get("sync_customers", False):
            results["customers"] = self.sync_customers(connection_id, sync_config.get("customer_segments"))
        if sync_config.get("sync_inventory", False):
            results["inventory"] = self.sync_inventory(connection_id, sync_config.get("product_ids"))
        return {"connection_id": connection_id, "results": results}
