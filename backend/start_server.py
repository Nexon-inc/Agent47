#!/usr/bin/env python3
"""
Agent47 Backend Server Startup Script
Ensures proper initialization of all services including database tables
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.config import settings
from core.database import get_supabase, DatabaseManager
from core.cache import init_redis, close_redis
from core.storage import init_chroma, close_chroma
from core.event_bus import init_kafka, close_kafka
from core.middleware import init_rate_limiter
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize all core services with comprehensive error handling"""
    try:
        logger.info("Starting Agent47 API server initialization...")
        
    # Initialize database
    logger.info("Initializing database...")
    db_manager = await get_supabase()
    await db_manager.initialize()
        
    # Create database tables
    logger.info("Creating database tables...")
    await db_manager.create_tables()
        logger.info("Database tables created successfully")
        
    # Verify database health
    logger.info("Performing database health check...")
    db_healthy = await db_manager.health_check()
        if not db_healthy:
            logger.error("Database health check failed")
            raise Exception("Database connection failed")
        logger.info("Database health check passed")
        
        # Initialize other services
        logger.info("Initializing Redis...")
        await init_redis()
        
        logger.info("Initializing ChromaDB...")
        await init_chroma()
        
        logger.info("Initializing Kafka...")
        await init_kafka()
        
        logger.info("Initializing rate limiter...")
        await init_rate_limiter()
        
        # Initialize agent services
        logger.info("Initializing agent services...")
        await initialize_agent_services()
        
        logger.info("All core services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        logger.exception("Full initialization error traceback:")
        return False

async def initialize_agent_services():
    """Initialize agent-specific services"""
    try:
        # Initialize AI service manager
        from core.ai.ai_service_manager import AIServiceManager
        ai_manager = AIServiceManager()
        await ai_manager.initialize()
        logger.info("AI Service Manager initialized")
        
        # Initialize integration manager
        from core.integrations.integration_manager import IntegrationManager
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        logger.info("Integration Manager initialized")
        
        # Initialize monitoring services
        from core.monitoring.grok_monitor import GrokMonitor
        grok_monitor = GrokMonitor()
        await grok_monitor.initialize()
        logger.info("Grok Monitor initialized")
        
        logger.info("All agent services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent services: {str(e)}")
        logger.exception("Agent services initialization error traceback:")
        raise

async def cleanup_services():
    """Cleanup all services"""
    try:
        logger.info("Cleaning up services...")
        
    # Close database
    db_manager = await get_supabase()
    await db_manager.close()
        
        # Close other services
        await close_redis()
        await close_chroma()
        await close_kafka()
        
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def main():
    """Main startup function"""
    try:
        # Initialize services
        success = asyncio.run(initialize_services())
        
        if not success:
            logger.error("Service initialization failed. Exiting.")
            sys.exit(1)
        
        # Start the server
        logger.info("Starting FastAPI server...")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception("Full error traceback:")
    finally:
        # Cleanup services
        asyncio.run(cleanup_services())
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    main()
