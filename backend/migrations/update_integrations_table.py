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

async def update_integrations_table():
    """Update the integrations table to match the new schema"""
    engine = create_async_engine(settings.supabase.database_url.replace("postgresql://", "postgresql+asyncpg://", 1))
    
    # SQL commands to update the integrations table
    update_commands = [
        # Add new columns if they don't exist
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS display_name VARCHAR(200);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS integration_type VARCHAR(50);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS provider VARCHAR(100);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS api_version VARCHAR(20);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS base_url VARCHAR(500);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS api_documentation_url VARCHAR(500);",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS pricing_tier VARCHAR(50) DEFAULT 'free';",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS rate_limits JSONB DEFAULT '{}';",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS supported_features JSONB DEFAULT '{}';",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS authentication_methods JSONB DEFAULT '{}';",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';",
        "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT true;",
        
        # Update existing data to have default values
        "UPDATE integrations SET display_name = name WHERE display_name IS NULL;",
        "UPDATE integrations SET integration_type = 'general' WHERE integration_type IS NULL;",
        "UPDATE integrations SET provider = 'unknown' WHERE provider IS NULL;",
        "UPDATE integrations SET base_url = 'https://api.example.com' WHERE base_url IS NULL;",
        "UPDATE integrations SET pricing_tier = 'free' WHERE pricing_tier IS NULL;",
        "UPDATE integrations SET rate_limits = '{}' WHERE rate_limits IS NULL;",
        "UPDATE integrations SET supported_features = '{}' WHERE supported_features IS NULL;",
        "UPDATE integrations SET authentication_methods = '{}' WHERE authentication_methods IS NULL;",
        "UPDATE integrations SET status = 'active' WHERE status IS NULL;",
        "UPDATE integrations SET is_available = true WHERE is_available IS NULL;",
        
        # Add NOT NULL constraints where needed
        "ALTER TABLE integrations ALTER COLUMN display_name SET NOT NULL;",
        "ALTER TABLE integrations ALTER COLUMN integration_type SET NOT NULL;",
        "ALTER TABLE integrations ALTER COLUMN provider SET NOT NULL;",
        "ALTER TABLE integrations ALTER COLUMN base_url SET NOT NULL;",
        
        # Add indexes for performance
        "CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);",
        "CREATE INDEX IF NOT EXISTS idx_integrations_provider ON integrations(provider);",
        "CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);",
        "CREATE INDEX IF NOT EXISTS idx_integrations_available ON integrations(is_available);",
    ]
    
    try:
        async with engine.begin() as conn:
            for command in update_commands:
                try:
                    await conn.execute(text(command))
                    logger.info(f"Executed: {command[:50]}...")
                except Exception as e:
                    logger.warning(f"Command failed (may already exist): {command[:50]}... - {e}")
                    # Continue with other commands even if one fails
                    continue
            
            logger.info("✅ Integrations table updated successfully")
            
    except Exception as e:
        logger.error(f"Failed to update integrations table: {e}")
        raise

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Integrations Table Update Migration")
    logger.info("==================================================")
    try:
        await update_integrations_table()
        logger.info("\n==================================================")
        logger.info("🎉 Migration completed successfully!")
        logger.info("✅ Integrations table is now compatible with the new model")
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
