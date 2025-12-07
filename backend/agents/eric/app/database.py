from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from backend.core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

# Import Eric models
from .models import Base

class EricDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Eric database connection"""
        if self._initialized:
            return
        
        try:
            # Use core Supabase connection
            core_db = await get_supabase()
            if core_db.engine:
                self.engine = core_db.engine
                self.session_factory = core_db.async_session_maker
                self._initialized = True
                logger.info("Eric database initialized successfully")
            else:
                logger.warning("Core database not initialized, Eric will use fallback")
                self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Eric database: {e}")
            # Don't raise, just mark as initialized to prevent blocking
            self._initialized = True
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    async def create_tables(self):
        """Create all Eric tables"""
        if not self._initialized:
            await self.initialize()
        
        if not self.engine:
            logger.warning("No database engine available, skipping table creation")
            return
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Eric database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create Eric database tables: {e}")
            # Don't raise, just log the error
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("Eric database connections closed")

# Global database instance
_eric_db = None

async def get_eric_database() -> EricDatabase:
    """Get Eric database instance"""
    global _eric_db
    if _eric_db is None:
        _eric_db = EricDatabase()
        await _eric_db.initialize()
    return _eric_db

async def init_eric_database():
    """Initialize Eric database"""
    db = await get_eric_database()
    await db.create_tables()
    return db

async def get_db():
    """Get database session for FastAPI dependency injection"""
    db = await get_eric_database()
    async with db.session_factory() as session:
        yield session
