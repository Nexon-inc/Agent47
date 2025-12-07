"""
Backend test configuration and fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Also add the workspace root to path for CI
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

try:
    from backend.core.config import settings
except ImportError:
    # Fallback for CI environment - try relative import
    try:
        import sys
        import os
        # Add the parent directory to path to find backend
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from backend.core.config import settings
    except ImportError:
        raise

try:
    from backend.core.database.connection import get_database_url
    from backend.core.database.models import Base
    from backend.main import app
    from backend.core.cache.redis_manager import RedisManager
    from backend.core.event_bus.kafka_manager import EventBus
except ImportError:
    # Fallback for CI environment - try relative import
    try:
        import sys
        import os
        # Add the parent directory to path to find backend
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from backend.core.database.connection import get_database_url
        from backend.core.database.models import Base
        from backend.main import app
        from backend.core.cache.redis_manager import RedisManager
        from backend.core.event_bus.kafka_manager import EventBus
    except ImportError:
        raise
from backend.core.ai import AIServiceManager

# Test database URL - use environment variable if available
import os
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def test_client() -> TestClient:
    """Create a test client for FastAPI."""
    return TestClient(app)

@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def redis_manager() -> AsyncGenerator[RedisManager, None]:
    """Create a test Redis manager."""
    # Use test Redis URL from environment
    test_redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
    redis_manager = RedisManager()
    # Override Redis URL for testing
    redis_manager.redis_url = test_redis_url
    await redis_manager.initialize()
    yield redis_manager
    await redis_manager.close()

@pytest_asyncio.fixture(scope="function")
async def event_bus() -> AsyncGenerator[EventBus, None]:
    """Create a test event bus."""
    event_bus = EventBus()
    await event_bus.initialize()
    yield event_bus
    await event_bus.close()

@pytest_asyncio.fixture(scope="function")
async def ai_service_manager() -> AsyncGenerator[AIServiceManager, None]:
    """Create a test AI service manager."""
    ai_manager = AIServiceManager()
    await ai_manager.initialize()
    yield ai_manager

@pytest.fixture(scope="function")
def mock_user_data():
    """Mock user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "pro"
    }

@pytest.fixture(scope="function")
def mock_business_idea_data():
    """Mock business idea data for testing."""
    return {
        "id": 1,
        "title": "Test Business Idea",
        "description": "A test business idea for testing purposes",
        "industry": "Technology",
        "target_market": "Small businesses",
        "revenue_model": "SaaS",
        "user_id": 1
    }

@pytest.fixture(scope="function")
def mock_market_research_data():
    """Mock market research data for testing."""
    return {
        "id": 1,
        "business_idea_id": 1,
        "market_size": 1000000,
        "competition_level": "Medium",
        "growth_rate": 0.15,
        "barriers_to_entry": ["High capital requirements", "Regulatory compliance"],
        "opportunities": ["Growing market", "Technology advancement"],
        "threats": ["Economic downturn", "New competitors"]
    }

@pytest.fixture(scope="function")
def mock_financial_forecast_data():
    """Mock financial forecast data for testing."""
    return {
        "id": 1,
        "business_idea_id": 1,
        "forecast_period": 36,
        "revenue_forecast": {
            "year_1": 100000,
            "year_2": 250000,
            "year_3": 500000
        },
        "expense_forecast": {
            "year_1": 80000,
            "year_2": 150000,
            "year_3": 300000
        },
        "profit_forecast": {
            "year_1": 20000,
            "year_2": 100000,
            "year_3": 200000
        }
    }

# Override database dependency for testing
async def override_get_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        yield session

# Apply the override
app.dependency_overrides[get_database_url] = override_get_db
