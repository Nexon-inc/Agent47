import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database.connection import init_supabase
from core.cache.redis_manager import init_redis
from core.event_bus.kafka_manager import EventBus
from core.ai import init_ai_service_manager
from .database import init_clara_database

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Clara application lifespan"""
    logger.info("🚀 Starting Clara - Customer Support Agent...")
    
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
        
        # Initialize Clara database
        logger.info("🗄️ Initializing Clara database...")
        await init_clara_database()
        
        logger.info("✅ Clara started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Clara: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Clara...")
        
        # Cleanup
        if hasattr(app.state, 'event_bus'):
            await app.state.event_bus.close()
        
        logger.info("👋 Clara shutdown complete")

def create_app() -> FastAPI:
    """Create Clara FastAPI application with lifespan management"""
    app = FastAPI(
        title="Clara - AI-Powered Customer Support",
        description="Intelligent, 24/7 customer support agent with AI chatbot, voice support, and ticket management",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app
