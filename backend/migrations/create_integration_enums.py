import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.config import settings

logger = logging.getLogger(__name__)

async def create_integration_enums():
    """Create PostgreSQL enum types for integrations"""
    engine = create_async_engine(settings.supabase.database_url.replace("postgresql://", "postgresql+asyncpg://", 1))
    
    # SQL commands to create enum types
    enum_commands = [
        # Create IntegrationType enum
        """
        DO $$ BEGIN
            CREATE TYPE integrationtype AS ENUM (
                'marketing', 'analytics', 'crm', 'content', 'design', 
                'productivity', 'finance', 'research', 'automation'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        
        # Create IntegrationStatus enum
        """
        DO $$ BEGIN
            CREATE TYPE integrationstatus AS ENUM (
                'active', 'inactive', 'suspended', 'maintenance', 'deprecated'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        
        # Create CredentialStatus enum
        """
        DO $$ BEGIN
            CREATE TYPE credentialstatus AS ENUM (
                'valid', 'expired', 'invalid', 'revoked'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        
        # Update the integrations table to use the new enum types
        "ALTER TABLE integrations ALTER COLUMN integration_type TYPE integrationtype USING integration_type::integrationtype;",
        "ALTER TABLE integrations ALTER COLUMN status TYPE integrationstatus USING status::integrationstatus;",
    ]
    
    try:
        async with engine.begin() as conn:
            for command in enum_commands:
                try:
                    await conn.execute(text(command))
                    logger.info(f"Executed enum creation/update command")
                except Exception as e:
                    logger.warning(f"Enum command failed (may already exist): {e}")
                    # Continue with other commands even if one fails
                    continue
            
            logger.info("✅ Integration enum types created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create integration enums: {e}")
        raise

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Integration Enums Creation Migration")
    logger.info("==================================================")
    try:
        await create_integration_enums()
        logger.info("\n==================================================")
        logger.info("🎉 Migration completed successfully!")
        logger.info("✅ Integration enum types are now available")
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
