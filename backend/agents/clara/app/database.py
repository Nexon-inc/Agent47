from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from backend.core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

# Import Clara models
from .models import Base

class ClaraDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Clara database connection"""
        if self._initialized:
            return
        
        try:
            # Use core Supabase connection
            core_db = await get_supabase()
            self.engine = core_db.engine
            self.session_factory = core_db.async_session_maker
            self._initialized = True
            
            logger.info("Clara database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Clara database: {e}")
            raise
    
    def get_session(self) -> AsyncSession:
        """Get database session (async context manager).

        Returns an AsyncSession compatible with `async with db.get_session()`.
        """
        return self.session_factory()
    
    async def create_tables(self):
        """Create all Clara tables"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Clara database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create Clara database tables: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("Clara database connections closed")

# Global database instance
_clara_db = None

async def get_clara_database() -> ClaraDatabase:
    """Get Clara database instance"""
    global _clara_db
    if _clara_db is None:
        _clara_db = ClaraDatabase()
        await _clara_db.initialize()
    return _clara_db

async def init_clara_database():
    """Initialize Clara database"""
    db = await get_clara_database()
    await db.create_tables()
    return db


async def get_db() -> AsyncSession:
    """FastAPI dependency generator returning an AsyncSession instance.

    This matches the pattern used across other agent database modules and allows
    route functions to declare `db: AsyncSession = Depends(get_db)`.
    """
    db = await get_clara_database()
    async with db.get_session() as session:
        yield session
