from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
from supabase import create_client, Client
from ..config import settings
from sqlalchemy.exc import ProgrammingError

logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self):
        self.client: Client = None
        self.engine = None
        self.async_session_maker = None
        # Backward-compat alias used by some agent modules
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Initialize Supabase client
            url = settings.supabase.supabase_url
            key = settings.supabase.supabase_service_role_key
            
            if not key:
                import os
                key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                if key:
                    logger.warning("Supabase key found in environment variables but not in settings.")

            # Clean key if present (remove whitespace/newlines which often cause 'Invalid API key')
            if url:
                url = url.strip()
            if key:
                key = key.strip()
                
            self.client = create_client(url, key)
            
            # Normalize URL to async driver if needed
            database_url = settings.supabase.supabase_db_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            # Initialize SQLAlchemy engine for direct database access
            # Use service role key in connection to bypass RLS policies
            # Parse database URL to add role if needed
            if "@" in database_url and "postgresql" in database_url:
                # Extract connection parts
                if "postgresql://" in database_url:
                    # Format: postgresql://user:password@host:port/dbname
                    # For admin operations, we need to use a role that bypasses RLS
                    # The service role key should be used via Supabase client, but for direct SQL
                    # we need to ensure we're connecting with proper credentials
                    pass  # Keep original URL for direct connection
            
            self.engine = create_async_engine(
                database_url,
                echo=settings.debug,
                poolclass=NullPool,
                pool_pre_ping=True,
                pool_recycle=600,  # Recycle connections every 10 minutes
                connect_args={
                    "command_timeout": 600,  # 10 minutes for long LLM requests
                    "server_settings": {
                        "statement_timeout": "600s",  # 10 minutes
                        "idle_in_transaction_session_timeout": "600s",  # 10 minutes
                        # Bypass RLS for admin operations - set role to service_role
                        "role": "service_role" if key else None
                    }
                }
            )
            
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            # Maintain backward compatibility for callers expecting `session_factory`
            self.session_factory = self.async_session_maker
            
            self._initialized = True
            logger.info("Supabase connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase connection: {e}")
            raise
    
    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Supabase connection closed")
    
    @asynccontextmanager
    async def get_session(self, bypass_rls: bool = False) -> AsyncGenerator[AsyncSession, None]:
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                # For admin operations, bypass RLS by setting the role
                if bypass_rls:
                    from sqlalchemy import text
                    try:
                        # Set role to service_role to bypass RLS policies
                        await session.execute(text("SET ROLE service_role"))
                        await session.commit()
                    except Exception as role_error:
                        # If service_role doesn't exist or we can't set it, try alternative
                        logger.warning(f"Could not set service_role, trying alternative: {role_error}")
                        try:
                            # Alternative: Disable RLS for this session (if we have superuser)
                            await session.execute(text("SET LOCAL row_security = off"))
                        except Exception:
                            # If that fails, continue anyway - might work with service role key
                            pass
                
                yield session
                # Only commit if no exception occurred
                try:
                    await session.commit()
                except Exception as commit_error:
                    await session.rollback()
                    # Check if it's a connection error
                    if "connection" in str(commit_error).lower() or "closed" in str(commit_error).lower():
                        logger.warning(f"Database connection error during commit, rolled back: {commit_error}")
                        # Don't re-raise connection errors - they're handled by rollback
                    else:
                        logger.error(f"Database commit error: {commit_error}")
                        raise
            except Exception as e:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
                logger.error(f"Database session error: {e}")
                raise
    
    async def create_tables(self):
        from .models import Base
        import asyncio
        from sqlalchemy import text
        
        if not self._initialized:
            await self.initialize()
        
        # Check if tables already exist to avoid unnecessary creation
        try:
            async with self.engine.begin() as conn:
                # Check if any core tables exist
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    );
                """))
                tables_exist = result.scalar()
                
                if tables_exist:
                    logger.info("Database tables already exist, checking for missing columns...")
                    # Check if website_url column exists in users table
                    try:
                        result = await conn.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = 'users'
                                AND column_name = 'website_url'
                            );
                        """))
                        column_exists = result.scalar()
                        
                        if not column_exists:
                            logger.info("Adding missing website_url column to users table...")
                            await conn.execute(text("""
                                ALTER TABLE users 
                                ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);
                            """))
                            logger.info("Successfully added website_url column to users table")
                    except Exception as col_error:
                        logger.warning(f"Could not check/add website_url column: {col_error}")
                    return
        except Exception as e:
            logger.warning(f"Could not check if tables exist: {e}")
        
        # Retry mechanism for table creation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.engine.begin() as conn:
                    # run_sync will execute the SQLAlchemy metadata create_all in a sync context
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created successfully")
                    return
            except ProgrammingError as e:
                # asyncpg/pgsql can raise ProgrammingError when an index or relation
                # already exists. The database may already have been initialized by a
                # previous run. Treat these 'already exists' errors as non-fatal so
                # the application can continue starting up.
                msg = str(e).lower()
                if "already exists" in msg or "duplicate" in msg:
                    logger.warning("Ignored ProgrammingError during create_tables: %s", e)
                    return
                else:
                    # Re-raise unknown programming errors
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Failed to create database tables (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    # If all retries failed, log the error but don't crash the application
                    logger.error("Database table creation failed after all retries. Application will continue but some features may not work.")
                    return
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def drop_tables(self):
        from .models import Base
        
        if not self._initialized:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
    
    async def health_check(self) -> tuple[bool, Optional[Exception]]:
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test Supabase client connection
            if self.client:
                # Try to access a simple table to test connection
                result = self.client.table('users').select('id').limit(1).execute()
                return True, None
            
            # Fallback to SQLAlchemy connection test
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True, None
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False, e
    
    def get_supabase_client(self) -> Client:
        """Get the Supabase client for API operations"""
        if not self._initialized:
            raise RuntimeError("Supabase not initialized. Call initialize() first.")
        return self.client

# Global Supabase manager instance
supabase_manager = SupabaseManager()

async def get_supabase() -> SupabaseManager:
    """Async accessor for the global Supabase manager (for async callers)."""
    return supabase_manager

def get_database() -> SupabaseManager:
    """Synchronous accessor for backward compatibility.

    Many modules in the codebase call `get_database()` or `get_supabase()` expecting a
    manager object synchronously. Provide a sync accessor that returns the global
    `supabase_manager`. The manager itself must be initialized at application startup
    by calling `init_supabase()` in the FastAPI lifespan.
    """
    return supabase_manager

async def init_supabase():
    await supabase_manager.initialize()
    await supabase_manager.create_tables()

async def close_supabase():
    await supabase_manager.close()

# Legacy aliases for backward compatibility
db_manager = supabase_manager
# `get_database` is the synchronous accessor (above)
init_database = init_supabase
close_database = close_supabase

# FastAPI dependency for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session"""
    async with supabase_manager.get_session() as session:
        yield session
