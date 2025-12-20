from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from core.config import settings
from core.database.models import Base
from core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

class JoeDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Use core Supabase connection
            core_db = await get_supabase()
            self.engine = core_db.engine
            self.session_factory = core_db.async_session_maker
            self._initialized = True
            
            logger.info("Joe database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Joe database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session for Joe agent"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
    
    async def create_tables(self):
        """Initialize Joe's database tables"""
        if not self._initialized:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close Joe's database connections"""
        if self._initialized:
            await self.engine.dispose()
            self._initialized = False

# Global instance
joe_database = JoeDatabase()

async def get_joe_database() -> AsyncSession:
    """Get database session for Joe agent"""
    async for session in joe_database.get_session():
        yield session

async def get_db() -> AsyncSession:
    """Get database session for FastAPI dependency injection"""
    async for session in joe_database.get_session():
        yield session

async def init_joe_database():
    """Initialize Joe's database tables"""
    await joe_database.initialize()
    await joe_database.create_tables()

async def close_joe_database():
    """Close Joe's database connections"""
    await joe_database.close()
