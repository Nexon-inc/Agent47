from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.core.config import settings
from backend.core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

# Import Shakes models
from .models import Base

class ShakesDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Shakes database connection"""
        if self._initialized:
            return
        
        try:
            # Use core Supabase connection
            core_db = await get_supabase()
            self.engine = core_db.engine
            self.session_factory = core_db.async_session_maker
            self._initialized = True
            
            logger.info("Shakes database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Shakes database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    async def create_tables(self):
        """Create all Shakes tables"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Shakes database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create Shakes database tables: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("Shakes database connections closed")

# Global database instance
_shakes_db = None

async def get_shakes_database() -> ShakesDatabase:
    """Get Shakes database instance"""
    global _shakes_db
    if _shakes_db is None:
        _shakes_db = ShakesDatabase()
        await _shakes_db.initialize()
    return _shakes_db

async def get_db():
    """Get database session for FastAPI dependency injection"""
    db = await get_shakes_database()
    async with db.session_factory() as session:
        yield session

async def init_shakes_database():
    """Initialize Shakes database"""
    db = await get_shakes_database()
    await db.create_tables()
    return db
