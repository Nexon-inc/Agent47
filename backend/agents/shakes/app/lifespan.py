import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database.connection import init_supabase
from core.cache.redis_manager import init_redis
from core.event_bus.kafka_manager import EventBus
from core.ai import init_ai_service_manager
from .database import init_shakes_database

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Shakes application lifespan"""
    logger.info("🚀 Starting Shakes - Content Creation Agent...")
    
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
        
        # Initialize Shakes database
        logger.info("🗄️ Initializing Shakes database...")
        await init_shakes_database()
        
        logger.info("✅ Shakes started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Shakes: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Shakes...")
        
        # Cleanup
        if hasattr(app.state, 'event_bus'):
            await app.state.event_bus.close()
        
        logger.info("👋 Shakes shutdown complete")

def create_app() -> FastAPI:
    """Create Shakes FastAPI application with lifespan management"""
    app = FastAPI(
        title="Shakes - AI-Powered Content Creation",
        description="Intelligent content creation agent with AI-powered writing, SEO optimization, and multi-platform content generation",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app
