import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.database.connection import init_supabase
from backend.core.cache.redis_manager import init_redis
from backend.core.event_bus.kafka_manager import EventBus
from backend.core.ai import init_ai_service_manager
from .database import init_purity_database

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Purity application lifespan"""
    logger.info("🚀 Starting Purity - Business Creator & Money Maker...")
    
    try:
        # Initialize core services
        logger.info("📊 Initializing core services...")
        await init_supabase()
        await init_redis()
        
        # Initialize Kafka event bus
        logger.info("📡 Initializing event bus...")
        event_bus = EventBus()
        await event_bus.initialize()
        app.state.event_bus = event_bus
        
        # Initialize AI service manager
        logger.info("🤖 Initializing AI service manager...")
        await init_ai_service_manager()
        
        # Initialize Purity database
        logger.info("🗄️ Initializing Purity database...")
        await init_purity_database()
        
        logger.info("✅ Purity started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Purity: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Purity...")
        
        # Cleanup
        if hasattr(app.state, 'event_bus'):
            await app.state.event_bus.close()
        
        logger.info("👋 Purity shutdown complete")

def create_app() -> FastAPI:
    """Create Purity FastAPI application with lifespan management"""
    from fastapi import FastAPI
    from backend.core.config import settings
    
    app = FastAPI(
        title=f"{settings.project_name} - Purity",
        description="AI-Powered Business Creator & Money Maker",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app
