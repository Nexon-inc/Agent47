from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.core.database.models import Base
from backend.core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

class AriaDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        try:
            core_db = await get_supabase()
            # Use SupabaseManager engine and async_session_maker
            self.engine = core_db.engine
            self.session_factory = core_db.async_session_maker
            self._initialized = True
            logger.info("Aria database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Aria database: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        if not self._initialized:
            await self.initialize()

        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def create_tables(self):
        if not self._initialized:
            await self.initialize()

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        if self._initialized:
            await self.engine.dispose()
            self._initialized = False

# global instance
aria_database = AriaDatabase()

async def get_db() -> AsyncSession:
    async for session in aria_database.get_session():
        yield session

async def init_aria_database():
    await aria_database.initialize()
    await aria_database.create_tables()

async def close_aria_database():
    await aria_database.close()
