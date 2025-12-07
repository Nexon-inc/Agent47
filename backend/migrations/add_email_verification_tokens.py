"""
Database migration to add email_verification_tokens table
Run this script to create the email verification tokens table in the database
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

async def create_email_verification_tokens_table():
    """Create the email_verification_tokens table"""
    
    # Get database URL
    database_url = settings.supabase.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Create email_verification_tokens table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
            
            await conn.execute(text(create_table_sql))
            logger.info("Created email_verification_tokens table")
            
            # Create indexes for better performance
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);",
                "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_email ON email_verification_tokens(email);",
                "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires_at ON email_verification_tokens(expires_at);",
                "CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_used ON email_verification_tokens(used);"
            ]
            
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            logger.info("Created indexes for email_verification_tokens table")
            
            # Add comments to table (execute separately)
            comments = [
                "COMMENT ON TABLE email_verification_tokens IS 'Stores email verification tokens for Gmail API email verification'",
                "COMMENT ON COLUMN email_verification_tokens.token IS 'SHA256 hash of the verification token (not the plain token)'",
                "COMMENT ON COLUMN email_verification_tokens.expires_at IS 'Token expiration timestamp'",
                "COMMENT ON COLUMN email_verification_tokens.used IS 'Whether the token has been used for verification'"
            ]
            
            for comment in comments:
                await conn.execute(text(comment))
            logger.info("Added table and column comments")
            
    except Exception as e:
        logger.error(f"Failed to create email_verification_tokens table: {e}")
        raise
    finally:
        await engine.dispose()

async def cleanup_expired_tokens():
    """Clean up expired verification tokens"""
    
    # Get database URL
    database_url = settings.supabase.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Delete expired tokens
            cleanup_sql = """
            DELETE FROM email_verification_tokens 
            WHERE expires_at < NOW();
            """
            
            result = await conn.execute(text(cleanup_sql))
            deleted_count = result.rowcount
            
            logger.info(f"Cleaned up {deleted_count} expired verification tokens")
            
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        raise
    finally:
        await engine.dispose()

async def main():
    """Main migration function"""
    print("🚀 Starting Email Verification Tokens Migration")
    print("=" * 50)
    
    try:
        # Create the table
        await create_email_verification_tokens_table()
        print("✅ Email verification tokens table created successfully")
        
        # Clean up any existing expired tokens
        await cleanup_expired_tokens()
        print("✅ Cleaned up expired tokens")
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("✅ Email verification tokens table is ready")
        
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
