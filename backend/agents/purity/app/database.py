import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings
from core.database.models import Base
from core.database.connection import get_supabase

logger = logging.getLogger(__name__)

class PurityDatabase:
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
            
            logger.info("Purity database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Purity database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session for Purity agent"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Initialize Purity's database tables"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Purity database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create Purity database tables: {e}")
            raise
    
    async def close(self):
        """Close Purity's database connections"""
        if self._initialized:
            await self.engine.dispose()
            self._initialized = False

# Global instance
_purity_db = None

async def get_purity_database() -> PurityDatabase:
    """Get Purity database instance"""
    global _purity_db
    if _purity_db is None:
        _purity_db = PurityDatabase()
        await _purity_db.initialize()
    return _purity_db

async def get_db():
    """Get database session for FastAPI dependency injection"""
    db = await get_purity_database()
    async with db.session_factory() as session:
        yield session

async def init_purity_database():
    """Initialize Purity database tables"""
    db = await get_purity_database()
    await db.create_tables()
    return db

async def close_purity_database():
    """Close Purity database connections"""
    global _purity_db
    if _purity_db:
        await _purity_db.close()
        _purity_db = None
