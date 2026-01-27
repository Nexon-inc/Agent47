
import asyncio
import os
import sys
from sqlalchemy import text, create_engine
import json

# Try to get DB URL from env or setting
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://agent47:agent47@localhost:5432/agent47")

def check_admin():
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    with engine.connect() as conn:
        print(f"Checking for admin email...")
        # Get default email from settings if possible, or just look for ANY admin
        result = conn.execute(text("SELECT user_id, email, permissions, is_active FROM admin_users"))
        admins = result.fetchall()
        
        if not admins:
            print("❌ NO admins found in 'admin_users' table!")
            return
            
        print(f"Found {len(admins)} admin(s):")
        for admin in admins:
            print(f"  - UserID: {admin[0]}, Email: {admin[1]}, Active: {admin[3]}")
            print(f"    Permissions: {admin[2]} (Type: {type(admin[2])})")
            
        # Check users table for the same IDs
        ids = [a[0] for a in admins]
        if ids:
            # Handle potential int vs str IDs
            id_placeholder = ",".join([f"'{i}'" for i in ids])
            result = conn.execute(text(f"SELECT id, email, tier FROM users WHERE id::text IN ({id_placeholder})"))
            users = result.fetchall()
            print(f"Found {len(users)} matching user(s) in 'users' table:")
            for user in users:
                print(f"  - ID: {user[0]}, Email: {user[1]}, Tier: {user[2]}")

if __name__ == "__main__":
    check_admin()
