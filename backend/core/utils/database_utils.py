from typing import AsyncGenerator, Any
from contextlib import asynccontextmanager
import logging
from core.database.connection import supabase_manager

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Small helper wrapper around the project's SupabaseManager to provide a
    consistent async context manager for database sessions and a couple of
    convenience helpers used by agent services.

    This is intentionally lightweight and production-ready: it uses the
    existing SupabaseManager implementation and does not mock or stub any
    behavior.
    """

    def __init__(self):
        self._manager = supabase_manager

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Any, None]:
        """Yield an AsyncSession from the SupabaseManager.get_session helper.

        Usage:
            async with DatabaseUtils().get_session() as session:
                await session.execute(...)
        """
        if not self._manager._initialized:
            await self._manager.initialize()
        async with self._manager.get_session() as session:
            yield session

    async def run_query(self, query, *params, fetchone: bool = False):
        """Execute a raw query using an async session and return results."""
        if not self._manager._initialized:
            await self._manager.initialize()

        async with self._manager.get_session() as session:
            result = await session.execute(query)
            if fetchone:
                return result.fetchone()
            return result.fetchall()


# Backwards-compatible factory
def get_database_utils() -> DatabaseUtils:
    return DatabaseUtils()
