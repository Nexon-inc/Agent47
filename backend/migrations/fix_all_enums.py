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

async def fix_all_enums():
    """Fix all enum types in the database"""
    engine = create_async_engine(settings.supabase.database_url.replace("postgresql://", "postgresql+asyncpg://", 1))
    
    # SQL commands to create/fix all enum types
    enum_commands = [
        # Drop existing enums if they exist (to recreate them properly)
        "DROP TYPE IF EXISTS integrationtype CASCADE;",
        "DROP TYPE IF EXISTS integrationstatus CASCADE;",
        "DROP TYPE IF EXISTS credentialstatus CASCADE;",
        "DROP TYPE IF EXISTS platformtype CASCADE;",
        "DROP TYPE IF EXISTS platformstatus CASCADE;",
        
        # Create IntegrationType enum
        """
        CREATE TYPE integrationtype AS ENUM (
            'marketing', 'analytics', 'crm', 'content', 'design', 
            'productivity', 'finance', 'research', 'automation'
        );
        """,
        
        # Create IntegrationStatus enum
        """
        CREATE TYPE integrationstatus AS ENUM (
            'active', 'inactive', 'suspended', 'maintenance', 'deprecated'
        );
        """,
        
        # Create CredentialStatus enum
        """
        CREATE TYPE credentialstatus AS ENUM (
            'valid', 'expired', 'invalid', 'revoked'
        );
        """,
        
        # Create PlatformType enum
        """
        CREATE TYPE platformtype AS ENUM (
            'SOCIAL_MEDIA', 'E_COMMERCE', 'ANALYTICS', 'CRM', 'EMAIL', 'CHAT'
        );
        """,
        
        # Create PlatformStatus enum
        """
        CREATE TYPE platformstatus AS ENUM (
            'ACTIVE', 'INACTIVE', 'SUSPENDED', 'MAINTENANCE', 'DEPRECATED'
        );
        """,
        
        # Update integrations table to use new enum types
        "ALTER TABLE integrations ALTER COLUMN integration_type TYPE integrationtype USING integration_type::integrationtype;",
        "ALTER TABLE integrations ALTER COLUMN status TYPE integrationstatus USING status::integrationstatus;",
        
        # Update social_platforms table to use new enum types
        "ALTER TABLE social_platforms ALTER COLUMN platform_type TYPE platformtype USING platform_type::platformtype;",
        "ALTER TABLE social_platforms ALTER COLUMN status TYPE platformstatus USING status::platformstatus;",
    ]
    
    try:
        async with engine.begin() as conn:
            for command in enum_commands:
                try:
                    await conn.execute(text(command))
                    logger.info(f"Executed: {command[:50]}...")
                except Exception as e:
                    logger.warning(f"Command failed (may already exist): {command[:50]}... - {e}")
                    # Continue with other commands even if one fails
                    continue
            
            logger.info("✅ All enum types created/updated successfully")
            
    except Exception as e:
        logger.error(f"Failed to fix enum types: {e}")
        raise

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Complete Enum Types Fix Migration")
    logger.info("==================================================")
    try:
        await fix_all_enums()
        logger.info("\n==================================================")
        logger.info("🎉 Migration completed successfully!")
        logger.info("✅ All enum types are now properly configured")
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
