import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database.connection import init_supabase
from core.cache.redis_manager import init_redis
from core.event_bus.kafka_manager import EventBus
from core.ai import init_ai_service_manager
from .database import init_joe_database

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Joe application lifespan"""
    logger.info("🔍 Starting Joe - Research Agent...")
    
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
        
        # Initialize Joe database
        logger.info("🗄️ Initializing Joe database...")
        await init_joe_database()
        
        logger.info("✅ Joe started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Joe: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Joe...")
        
        # Cleanup
        if hasattr(app.state, 'event_bus'):
            await app.state.event_bus.close()
        
        logger.info("👋 Joe shutdown complete")

def create_app() -> FastAPI:
    """Create Joe FastAPI application with lifespan management"""
    app = FastAPI(
        title="Joe - AI-Powered Research Agent",
        description="Intelligent research and data analysis agent with market research, competitor analysis, and trend tracking",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app

# Export lifespan for use in main.py
__all__ = ["lifespan", "create_app"]