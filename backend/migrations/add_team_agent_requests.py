"""
Database migration to add team_agent_requests and team_chat_messages tables
Run this script to create the tables for team-agent communication
"""

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

async def create_team_agent_requests_table():
    """Create the team_agent_requests table"""
    
    # Get database URL
    database_url = settings.supabase.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Create team_agent_requests table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS team_agent_requests (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                team_member_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                agent_key VARCHAR(50) NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                request_data JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'pending',
                output_data JSONB DEFAULT '{}',
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                processed_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE
            );
            """
            
            await conn.execute(text(create_table_sql))
            logger.info("Created team_agent_requests table")
            
            # Create indexes
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_team_agent_requests_team_id ON team_agent_requests(team_id);",
                "CREATE INDEX IF NOT EXISTS idx_team_agent_requests_team_member_id ON team_agent_requests(team_member_id);",
                "CREATE INDEX IF NOT EXISTS idx_team_agent_requests_agent_key ON team_agent_requests(agent_key);",
                "CREATE INDEX IF NOT EXISTS idx_team_agent_requests_status ON team_agent_requests(status);",
                "CREATE INDEX IF NOT EXISTS idx_team_agent_requests_created_at ON team_agent_requests(created_at);"
            ]
            
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            logger.info("Created indexes for team_agent_requests table")
            
    except Exception as e:
        logger.error(f"Failed to create team_agent_requests table: {e}")
        raise
    finally:
        await engine.dispose()

async def create_team_chat_messages_table():
    """Create the team_chat_messages table for Discord-style chat"""
    
    # Get database URL
    database_url = settings.supabase.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Create team_chat_messages table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS team_chat_messages (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                agent_key VARCHAR(50),
                message_type VARCHAR(20) DEFAULT 'text',
                content TEXT NOT NULL,
                audio_url TEXT,
                file_url TEXT,
                file_name VARCHAR(255),
                file_size INTEGER,
                metadata JSONB DEFAULT '{}',
                reply_to_message_id INTEGER REFERENCES team_chat_messages(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                deleted_at TIMESTAMP WITH TIME ZONE
            );
            """
            
            await conn.execute(text(create_table_sql))
            logger.info("Created team_chat_messages table")
            
            # Create indexes
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_team_chat_messages_team_id ON team_chat_messages(team_id);",
                "CREATE INDEX IF NOT EXISTS idx_team_chat_messages_user_id ON team_chat_messages(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_team_chat_messages_agent_key ON team_chat_messages(agent_key);",
                "CREATE INDEX IF NOT EXISTS idx_team_chat_messages_created_at ON team_chat_messages(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_team_chat_messages_reply_to ON team_chat_messages(reply_to_message_id);"
            ]
            
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            logger.info("Created indexes for team_chat_messages table")
            
    except Exception as e:
        logger.error(f"Failed to create team_chat_messages table: {e}")
        raise
    finally:
        await engine.dispose()

async def create_geo_targeted_campaigns_table():
    """Create the geo_targeted_campaigns table for location-based campaigns"""
    
    # Get database URL
    database_url = settings.supabase.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Create geo_targeted_campaigns table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS geo_targeted_campaigns (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                campaign_name VARCHAR(255) NOT NULL,
                target_locations TEXT NOT NULL,
                campaign_type VARCHAR(50) DEFAULT 'outreach',
                agent_key VARCHAR(50),
                total_businesses INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE
            );
            """
            
            await conn.execute(text(create_table_sql))
            logger.info("Created geo_targeted_campaigns table")
            
            # Create indexes
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_geo_targeted_campaigns_user_id ON geo_targeted_campaigns(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_geo_targeted_campaigns_status ON geo_targeted_campaigns(status);",
                "CREATE INDEX IF NOT EXISTS idx_geo_targeted_campaigns_created_at ON geo_targeted_campaigns(created_at);"
            ]
            
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            logger.info("Created indexes for geo_targeted_campaigns table")
            
    except Exception as e:
        logger.error(f"Failed to create geo_targeted_campaigns table: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """Main migration function"""
    print("🚀 Starting Team Agent Requests Migration")
    print("=" * 50)
    
    try:
        # Create team_agent_requests table
        await create_team_agent_requests_table()
        print("✅ team_agent_requests table created successfully")
        
        # Create team_chat_messages table
        await create_team_chat_messages_table()
        print("✅ team_chat_messages table created successfully")
        
        # Create geo_targeted_campaigns table
        await create_geo_targeted_campaigns_table()
        print("✅ geo_targeted_campaigns table created successfully")
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("✅ Team agent communication and geo-targeting tables are ready")
        
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

