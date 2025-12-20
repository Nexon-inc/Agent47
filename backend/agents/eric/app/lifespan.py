from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.cache.redis_manager import init_redis
from core.event_bus.kafka_manager import KafkaManager
from core.storage.chroma_manager import ChromaManager
# Storage not used by Eric agent
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from .database import init_eric_database
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Eric - Sales Agent...")
    try:
        # Initialize Eric database (connects to core)
        await init_eric_database()
        logger.info("✅ Eric database initialized")
        
        # Initialize Redis
        await init_redis()
        logger.info("✅ Redis initialized")
        
        # Initialize Kafka
        kafka_manager = KafkaManager()
        await kafka_manager.initialize()
        logger.info("✅ Kafka initialized")
        
        # Initialize ChromaDB
        chroma_manager = ChromaManager()
        await chroma_manager.initialize()
        logger.info("✅ ChromaDB initialized")
        
        # Initialize Supabase Storage
        # Storage manager is already initialized globally
        logger.info("✅ Supabase Storage initialized")
        
        # Initialize Integration Manager
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        logger.info("✅ Integration Manager initialized")
        
        # Initialize Platform Manager
        platform_manager = PlatformManager()
        await platform_manager.initialize()
        logger.info("✅ Platform Manager initialized")
        
        logger.info("🚀 Eric - Sales Agent is ready!")
        
    except Exception as e:
        logger.error(f"Failed to start Eric - Sales Agent: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Eric - Sales Agent...")
    try:
        # Close database connections
        from .database import get_eric_database
        eric_db = await get_eric_database()
        await eric_db.close()
        logger.info("✅ Eric database connections closed")
        
        # Close other connections
        if 'kafka_manager' in locals():
            await kafka_manager.close()
            logger.info("✅ Kafka connections closed")
        
        if 'chroma_manager' in locals():
            await chroma_manager.close()
            logger.info("✅ ChromaDB connections closed")
        
        # Supabase Storage cleanup handled globally
        logger.info("✅ Supabase Storage connections closed")
        
        if 'integration_manager' in locals():
            await integration_manager.close()
            logger.info("✅ Integration Manager closed")
        
        if 'platform_manager' in locals():
            await platform_manager.close()
            logger.info("✅ Platform Manager closed")
        
        logger.info("✅ Eric - Sales Agent shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during Eric shutdown: {e}")

def create_app() -> FastAPI:
    """Create FastAPI app with lifespan"""
    app = FastAPI(
        title="Eric - Sales Agent",
        description="AI-Powered Sales Automation and Lead Management",
        version="1.0.0",
        lifespan=lifespan
    )
    return app
