import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.database.connection import init_supabase
from backend.core.cache.redis_manager import init_redis
from backend.core.event_bus.kafka_manager import EventBus
from backend.core.ai import init_ai_service_manager
from .database import init_jackie_database

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Jackie - Marketing Agent...")
    
    try:
        logger.info("📊 Initializing core services...")
        await init_supabase()
        await init_redis()
        
        logger.info("📡 Initializing event bus...")
        event_bus = EventBus()
        await event_bus.initialize()
        app.state.event_bus = event_bus
        
        logger.info("🤖 Initializing AI service manager...")
        await init_ai_service_manager()
        
        logger.info("🗄️ Initializing Jackie database...")
        await init_jackie_database()
        
        logger.info("✅ Jackie started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Jackie: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down Jackie...")
        
        if hasattr(app.state, 'event_bus'):
            await app.state.event_bus.close()
        
        logger.info("👋 Jackie shutdown complete")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Jackie - AI-Powered Marketing Agent",
        description="Intelligent marketing automation platform with AI-powered optimization",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app
