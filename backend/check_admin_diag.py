
import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from core.database import get_database
from core.database.models import User
from sqlalchemy import select, text
from core.config import settings

async def check_admin():
    db = get_database()
    print(f"Checking for admin user: {settings.admin_default_email}")
    
    async with db.get_session() as session:
        # Check User table
        result = await session.execute(select(User).where(User.email == settings.admin_default_email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Found user in 'users' table:")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Tier: {user.tier}")
            print(f"  Has Hashed Password: {bool(user.hashed_password)}")
        else:
            print(f"User NOT found in 'users' table")
            
        # Check admin_users table
        try:
            result = await session.execute(text("SELECT * FROM admin_users WHERE email = :email"), {"email": settings.admin_default_email})
            admin_row = result.fetchone()
            if admin_row:
                print(f"Found user in 'admin_users' table:")
                print(f"  Row: {admin_row}")
            else:
                print(f"User NOT found in 'admin_users' table")
        except Exception as e:
            print(f"Error checking 'admin_users' table: {e}")

if __name__ == "__main__":
    asyncio.run(check_admin())
