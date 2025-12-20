from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os

# Add the backend directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from core.config import settings
    from core.database.connection import init_supabase, close_supabase
    from core.cache.redis_manager import init_redis, close_redis
    from core.event_bus.kafka_manager import init_kafka, close_kafka
    from core.ai import init_ai_service_manager
    from .workers.scheduler_consumer import scheduler_consumer
    from .workers.publisher_consumer import publisher_consumer
except ImportError:
    # Fallback for direct execution
    from core.config import settings
    from core.database.connection import init_supabase, close_supabase
    from core.cache.redis_manager import init_redis, close_redis
    from core.event_bus.kafka_manager import init_kafka, close_kafka
    from core.ai import init_ai_service_manager
    from .workers.scheduler_consumer import scheduler_consumer
    from .workers.publisher_consumer import publisher_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import Aria models before DB table creation so metadata includes them
    from . import models  # noqa: F401
    await init_supabase()
    await init_redis()
    await init_kafka()
    await init_ai_service_manager()
    await scheduler_consumer.initialize()
    await publisher_consumer.initialize()
    yield
    await close_kafka()
    await close_redis()
    await close_supabase()


def create_app() -> FastAPI:
    app = FastAPI(title=f"{settings.project_name} - Aria", version=settings.version)
    app.router.lifespan_context = lifespan
    return app


