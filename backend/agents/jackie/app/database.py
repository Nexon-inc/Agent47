from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from core.config import settings
from core.database.connection import get_supabase
import logging

logger = logging.getLogger(__name__)

from .models import Base

class JackieDatabase:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            core_db = await get_supabase()
            self.engine = core_db.engine
            self.session_factory = core_db.async_session_maker
            self._initialized = True
            
            logger.info("Jackie database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jackie database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        if not self._initialized:
            await self.initialize()
        
        return self.session_factory()
    
    async def create_tables(self):
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Jackie database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create Jackie database tables: {e}")
            raise
    
    async def close(self):
        if self.engine:
            await self.engine.dispose()
        self._initialized = False
        logger.info("Jackie database connections closed")

_jackie_db = None

async def get_jackie_database() -> JackieDatabase:
    global _jackie_db
    if _jackie_db is None:
        _jackie_db = JackieDatabase()
        await _jackie_db.initialize()
    return _jackie_db

async def init_jackie_database():
    db = await get_jackie_database()
    await db.create_tables()
    return db

# Async database session for FastAPI dependency injection
async def get_db():
    """Get database session for FastAPI dependency injection"""
    db = await get_jackie_database()
    async with db.session_factory() as session:
        yield session
