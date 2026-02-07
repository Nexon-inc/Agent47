"""Add start_date and end_date to subscriptions table

This migration adds the missing start_date and end_date columns to the subscriptions table.
These columns are required by the Subscription model but were missing from the database schema.

Run this migration with: python backend/migrations/add_subscription_dates.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)
os.chdir(backend_path)

from sqlalchemy import text
from database.database import async_engine


async def run_migration():
    """Add start_date and end_date columns to subscriptions table"""
    
    async with async_engine.begin() as conn:
        print("🔍 Checking if columns exist...")
        
        # Check if columns already exist
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions' 
            AND column_name IN ('start_date', 'end_date')
        """))
        
        existing_columns = {row[0] for row in result}
        
        if 'start_date' in existing_columns and 'end_date' in existing_columns:
            print("✅ Columns already exist. No migration needed.")
            return
        
        print("📝 Adding missing columns to subscriptions table...")
        
        # Add start_date column if it doesn't exist
        if 'start_date' not in existing_columns:
            await conn.execute(text("""
                ALTER TABLE subscriptions 
                ADD COLUMN start_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            """))
            print("✅ Added start_date column")
        
        # Add end_date column if it doesn't exist
        if 'end_date' not in existing_columns:
            await conn.execute(text("""
                ALTER TABLE subscriptions 
                ADD COLUMN end_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '30 days')
            """))
            print("✅ Added end_date column")
        
        # Update existing rows to have proper end dates based on created_at
        await conn.execute(text("""
            UPDATE subscriptions 
            SET 
                start_date = created_at,
                end_date = created_at + INTERVAL '30 days'
            WHERE start_date = created_at
        """))
        print("✅ Updated existing subscription dates")
        
        print("🎉 Migration completed successfully!")


async def rollback_migration():
    """Remove start_date and end_date columns from subscriptions table"""
    
    async with async_engine.begin() as conn:
        print("🔄 Rolling back migration...")
        
        # Drop columns if they exist
        await conn.execute(text("""
            ALTER TABLE subscriptions 
            DROP COLUMN IF EXISTS start_date,
            DROP COLUMN IF EXISTS end_date
        """))
        
        print("✅ Rollback completed successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Subscription dates migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())
