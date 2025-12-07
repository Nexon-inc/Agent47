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

async def verify_and_create_enums():
    """Verify and create enum types in the database"""
    engine = create_async_engine(settings.supabase.database_url.replace("postgresql://", "postgresql+asyncpg://", 1))
    
    try:
        async with engine.begin() as conn:
            # Check if enums exist
            result = await conn.execute(text("""
                SELECT typname FROM pg_type 
                WHERE typname IN ('integrationtype', 'integrationstatus', 'credentialstatus', 'platformtype', 'platformstatus')
            """))
            existing_enums = [row[0] for row in result.fetchall()]
            logger.info(f"Existing enums: {existing_enums}")
            
            # Create missing enums
            enum_commands = [
                # IntegrationType enum
                """
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integrationtype') THEN
                        CREATE TYPE integrationtype AS ENUM (
                            'marketing', 'analytics', 'crm', 'content', 'design', 
                            'productivity', 'finance', 'research', 'automation'
                        );
                    END IF;
                END $$;
                """,
                
                # IntegrationStatus enum
                """
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integrationstatus') THEN
                        CREATE TYPE integrationstatus AS ENUM (
                            'active', 'inactive', 'suspended', 'maintenance', 'deprecated'
                        );
                    END IF;
                END $$;
                """,
                
                # CredentialStatus enum
                """
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'credentialstatus') THEN
                        CREATE TYPE credentialstatus AS ENUM (
                            'valid', 'expired', 'invalid', 'revoked'
                        );
                    END IF;
                END $$;
                """,
                
                # PlatformType enum
                """
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platformtype') THEN
                        CREATE TYPE platformtype AS ENUM (
                            'SOCIAL_MEDIA', 'E_COMMERCE', 'ANALYTICS', 'CRM', 'EMAIL', 'CHAT'
                        );
                    END IF;
                END $$;
                """,
                
                # PlatformStatus enum
                """
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platformstatus') THEN
                        CREATE TYPE platformstatus AS ENUM (
                            'ACTIVE', 'INACTIVE', 'SUSPENDED', 'MAINTENANCE', 'DEPRECATED'
                        );
                    END IF;
                END $$;
                """,
            ]
            
            for command in enum_commands:
                try:
                    await conn.execute(text(command))
                    logger.info(f"Executed enum creation command")
                except Exception as e:
                    logger.warning(f"Enum creation failed: {e}")
                    continue
            
            # Verify enums were created
            result = await conn.execute(text("""
                SELECT typname FROM pg_type 
                WHERE typname IN ('integrationtype', 'integrationstatus', 'credentialstatus', 'platformtype', 'platformstatus')
            """))
            final_enums = [row[0] for row in result.fetchall()]
            logger.info(f"Final enums: {final_enums}")
            
            logger.info("✅ Enum verification and creation completed")
            
    except Exception as e:
        logger.error(f"Failed to verify/create enum types: {e}")
        raise

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Enum Verification and Creation")
    logger.info("==================================================")
    try:
        await verify_and_create_enums()
        logger.info("\n==================================================")
        logger.info("🎉 Enum verification completed successfully!")
    except Exception as e:
        logger.error(f"💥 Enum verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
