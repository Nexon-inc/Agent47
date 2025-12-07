#!/usr/bin/env python3
"""
Script to manually verify users for development purposes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_database
from core.database.models import User
from sqlalchemy import select, update

async def verify_all_users():
    """Verify all users in the database"""
    db = get_database()
    async with db.get_session() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Found {len(users)} users in database")
        
        if len(users) == 0:
            print("No users found to verify")
            return
        
        # Verify all users
        await session.execute(
            update(User).values(is_verified=True)
        )
        await session.commit()
        
        print("✅ All users have been verified successfully!")
        
        # Show updated status
        result = await session.execute(select(User))
        users = result.scalars().all()
        for user in users:
            print(f"User: {user.email}, Verified: {user.is_verified}, Active: {user.is_active}")

async def verify_user_by_email(email: str):
    """Verify a specific user by email"""
    db = get_database()
    async with db.get_session() as session:
        # Find user by email
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found")
            return
        
        # Verify the user
        await session.execute(
            update(User).where(User.email == email).values(is_verified=True)
        )
        await session.commit()
        
        print(f"✅ User {email} has been verified successfully!")

def print_help():
    """Print help information"""
    print("""
User Verification Script

Usage:
    python scripts/verify_users.py [command] [email]

Commands:
    all     - Verify all users in the database
    user    - Verify a specific user by email
    help    - Show this help message

Examples:
    python scripts/verify_users.py all
    python scripts/verify_users.py user john@example.com
    """)

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "all":
            await verify_all_users()
        elif command == "user":
            if len(sys.argv) < 3:
                print("❌ Please provide an email address")
                print("Usage: python scripts/verify_users.py user <email>")
                return
            email = sys.argv[2]
            await verify_user_by_email(email)
        elif command == "help":
            print_help()
        else:
            print(f"❌ Unknown command: {command}")
            print_help()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
