import asyncio
import logging
from core.database.connection import supabase_manager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    logger.info("Starting manual database migration...")
    
    try:
        await supabase_manager.initialize()
        
        async with supabase_manager.engine.begin() as conn:
            logger.info("Checking for 'auto_renew' column in 'subscriptions' table...")
            
            # Check if column exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'subscriptions'
                    AND column_name = 'auto_renew'
                );
            """))
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("Adding 'auto_renew' column to 'subscriptions' table...")
                await conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE;
                """))
                logger.info("Successfully added 'auto_renew' column.")
            else:
                logger.info("'auto_renew' column already exists.")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        await supabase_manager.close()
        logger.info("Migration script finished.")

if __name__ == "__main__":
    asyncio.run(run_migration())
