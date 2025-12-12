from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
from datetime import datetime

# Ensure NLPUtils compatibility shim is loaded early
import core.utils.nlp_utils  # registers NLPUtils on builtins

from core.config import settings
from core.database import init_database, close_database, get_database, get_supabase
from core.cache import init_redis, close_redis
from core.storage import init_chroma, close_chroma
from core.event_bus import init_kafka, close_kafka
from core.middleware import init_rate_limiter
from core.middleware.tier_protection import TierProtectionMiddleware
from core.middleware.auth_middleware import AuthMiddleware
from core.authentication import auth_router
from core.event_bus.intercommunication_router import router as intercommunication_router
from core.user_management.calendar_router import router as calendar_router
from core.user_management.team_management_router import team_router as team_router
from core.user_management.team_agent_router import router as team_agent_router
from core.user_management.team_chat_router import router as team_chat_router
from core.user_management.user_admin_router import router as user_admin_router
from core.voice.voice_router import router as voice_router
from core.services.phone_router import router as phone_router
from core.services.google_maps_router import router as google_maps_router
from core.services.geolocation_router import router as geolocation_router
from core.user_management.inbox_router import inbox_router as inbox_router
from core.analytics.analytics_router import router as analytics_router
from core.notifications.notification_router import router as notification_router
from core.platforms.oauth_router import router as platform_router
from core.integrations.secure_integration_router import router as integration_router
from core.user_management.account_router import router as account_router
from core.user_management.selected_agents_router import router as selected_agents_router
from core.user_management.agent_data_router import router as agent_data_router
from core.ai.nlp_router import router as nlp_router
from admin.admin_router import router as admin_router
from core.realtime.websocket_router import router as websocket_router

# Agent routers (now directly under agents/)
from agents.aria.app.main import app as aria_app
from agents.clara.app.main import app as clara_app
from agents.eric.app.main import app as eric_app
from agents.jackie.app.main import app as jackie_app
from agents.joe.app.main import app as joe_app
from agents.purity.app.main import app as purity_app
from agents.shakes.app.main import app as shakes_app

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Agent47 API server...")

    try:
        # Initialize core services
        await init_database()

        # Create database tables
        supabase_manager = await get_supabase()
        await supabase_manager.create_tables()

        # Verify Supabase health
        supabase_healthy = await supabase_manager.health_check()
        if not supabase_healthy:
            logger.error("Supabase health check failed")
            raise Exception("Supabase connection failed")
        logger.info("Supabase health check passed")

        await init_redis()
        await init_chroma()
        await init_kafka()
        await init_rate_limiter()

        # Initialize admin system
        from admin import init_admin_core
        await init_admin_core()
        logger.info("Admin system initialized successfully")

        # Initialize system platform manager
        from core.platforms.system_platform_manager import get_system_platform_manager
        await get_system_platform_manager()
        logger.info("System platform manager initialized successfully")

        logger.info("All core services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize core services: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Agent47 API server...")

    try:
        await close_database()
        await close_redis()
        await close_chroma()
        await close_kafka()

        logger.info("All core services shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Agent47 API",
    description="AI Automation Platform API",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add tier protection middleware
app.add_middleware(TierProtectionMiddleware)

# Include API routes
app.include_router(auth_router)
app.include_router(intercommunication_router)
app.include_router(calendar_router)
app.include_router(team_router)
app.include_router(team_agent_router)
app.include_router(team_chat_router)
app.include_router(user_admin_router)
app.include_router(voice_router)
app.include_router(phone_router)
app.include_router(google_maps_router)
app.include_router(geolocation_router)
app.include_router(inbox_router)
app.include_router(analytics_router)
app.include_router(notification_router)
app.include_router(platform_router)
app.include_router(integration_router)
app.include_router(account_router)
app.include_router(selected_agents_router)
app.include_router(agent_data_router)
app.include_router(nlp_router)
app.include_router(admin_router)
app.include_router(websocket_router)

# Mount agent applications
app.mount("/api/agents/aria", aria_app)
app.mount("/api/agents/clara", clara_app)
app.mount("/api/agents/eric", eric_app)
app.mount("/api/agents/jackie", jackie_app)
app.mount("/api/agents/joe", joe_app)
app.mount("/api/agents/purity", purity_app)
app.mount("/api/agents/shakes", shakes_app)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Check Supabase health
        from core.database import get_supabase
        supabase_manager = await get_supabase()
        supabase_healthy = await supabase_manager.health_check()

        # Check Redis health
        from core.cache import get_redis
        redis_healthy = True
        try:
            redis_client = await get_redis()
            await redis_client.ping()
        except Exception:
            redis_healthy = False

        # Check agent status (static for now)
        agent_status = {
            "aria": {"port": settings.agents.aria_port, "status": "running"},
            "clara": {"port": settings.agents.clara_port, "status": "running"},
            "eric": {"port": settings.agents.eric_port, "status": "running"},
            "jackie": {"port": settings.agents.jackie_port, "status": "running"},
            "joe": {"port": settings.agents.joe_port, "status": "running"},
            "purity": {"port": settings.agents.purity_port, "status": "running"},
            "shakes": {"port": settings.agents.shakes_port, "status": "running"}
        }

        overall_status = "healthy" if supabase_healthy and redis_healthy else "degraded"

        return {
            "status": overall_status,
            "service": "Agent47 API",
            "version": settings.version,
            "environment": settings.environment,
            "components": {
                "supabase": "healthy" if supabase_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy",
                "agents": agent_status
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Agent47 API",
            "version": settings.version,
            "environment": settings.environment,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Agent47 API",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )