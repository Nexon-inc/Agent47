import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_joe_database

logger = logging.getLogger(__name__)

class DataVisualizationService:
    """Service for creating data visualizations and charts"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize data visualization service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Data visualization service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data visualization service: {e}")
            raise
    
    async def create_visualization(
        self,
        user_id: int,
        data: Dict[str, Any],
        chart_type: str = "bar",
        title: str = None
    ) -> Dict[str, Any]:
        """Create data visualization"""
        if not self._initialized:
            await self.initialize()
            
        try:
            db = await get_joe_database()
            async with db.get_session() as session:
                # Simulate visualization creation
                visualization_data = {
                    "chart_type": chart_type,
                    "title": title or "Data Visualization",
                    "data": data,
                    "config": {
                        "width": 800,
                        "height": 600,
                        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
                        "responsive": True
                    },
                    "created_at": datetime.now().isoformat()
                }
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "visualization": visualization_data,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Data visualization creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_visualization_templates(
        self,
        user_id: int,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Get visualization templates"""
        if not self._initialized:
            await self.initialize()
            
        try:
            db = await get_joe_database()
            async with db.get_session() as session:
                # Simulate templates
                templates = [
                    {
                        "id": "bar_chart",
                        "name": "Bar Chart",
                        "category": "general",
                        "description": "Simple bar chart for comparing values"
                    },
                    {
                        "id": "line_chart",
                        "name": "Line Chart",
                        "category": "trends",
                        "description": "Line chart for showing trends over time"
                    },
                    {
                        "id": "pie_chart",
                        "name": "Pie Chart",
                        "category": "general",
                        "description": "Pie chart for showing proportions"
                    }
                ]
                
                return {
                    "success": True,
                    "category": category,
                    "templates": templates,
                    "total_templates": len(templates)
                }
                
        except Exception as e:
            logger.error(f"Failed to get visualization templates: {e}")
            return {"success": False, "error": str(e)}
