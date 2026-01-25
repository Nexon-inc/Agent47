from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
import asyncio
from datetime import datetime

# Ensure NLPUtils compatibility shim is loaded early
import core.utils.nlp_utils  

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
from core.ai.nlp_router import router as nlp_router
from admin.admin_router import router as admin_router
from core.realtime.websocket_router import router as websocket_router
from core.user_management.system_debug_router import router as system_debug_router

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


async def _init_with_timeout(coro, timeout: float, service_name: str, critical: bool = True):
    try:
        await asyncio.wait_for(coro, timeout=timeout)
        logger.info(f"{service_name} initialized successfully")
        return True
    except asyncio.TimeoutError:
        logger.error(f"{service_name} initialization timed out after {timeout}s")
        if critical:
            raise
        return False
    except Exception as e:
        logger.error(f"{service_name} initialization failed: {str(e)}")
        if critical:
            raise
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agent47 API server...")

    try:
        await _init_with_timeout(init_database(), timeout=30.0, service_name="Database", critical=True)

        supabase_manager = await get_supabase()
        await _init_with_timeout(supabase_manager.create_tables(), timeout=30.0, service_name="Database tables", critical=True)

        supabase_healthy, health_exception = await supabase_manager.health_check()
        if not supabase_healthy:
            error_message = f"Supabase connection failed: {health_exception}"
            logger.error(error_message)
            raise Exception(error_message)
        logger.info("Supabase health check passed")

        await _init_with_timeout(init_redis(), timeout=10.0, service_name="Redis", critical=True)

        await _init_with_timeout(init_chroma(), timeout=20.0, service_name="ChromaDB", critical=True)
        await _init_with_timeout(init_kafka(), timeout=10.0, service_name="Kafka", critical=True)
        await _init_with_timeout(init_rate_limiter(), timeout=5.0, service_name="Rate limiter", critical=True)

        # Initialize Email Verification Manager
        from core.authentication.email_verification_manager import email_verification_manager
        await _init_with_timeout(email_verification_manager.initialize(), timeout=20.0, service_name="Email Verification Manager", critical=False)

        from admin import init_admin_core
        await _init_with_timeout(init_admin_core(), timeout=15.0, service_name="Admin core", critical=True)

        from core.platforms.system_platform_manager import get_system_platform_manager
        await _init_with_timeout(get_system_platform_manager(), timeout=15.0, service_name="System platform manager", critical=True)

        logger.info("Critical services initialized, server ready")

    except Exception as e:
        logger.error(f"Failed to initialize critical services: {str(e)}")
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
app.include_router(system_debug_router)

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
        supabase_healthy, _ = await supabase_manager.health_check()

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
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
