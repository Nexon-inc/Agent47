
import asyncio
import json
from sqlalchemy import text
from core.database import get_database
from core.config import get_settings

async def check_admin():
    db = get_database()
    settings = get_settings()
    email = settings.admin_default_email
    
    print(f"Checking admin user: {email}")
    
    async with db.get_session() as session:
        # Check users table
        result = await session.execute(
            text("SELECT id, email, tier FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()
        if not user:
            print("❌ User not found in 'users' table")
            return
        
        user_id = user[0]
        print(f"✅ User found: ID={user_id}, Tier={user[2]}")
        
        # Check admin_users table
        result = await session.execute(
            text("SELECT user_id, email, permissions, is_active FROM admin_users WHERE email = :email"),
            {"email": email}
        )
        admin = result.fetchone()
        if not admin:
            print("❌ User not found in 'admin_users' table")
            
            # Try finding by user_id
            result = await session.execute(
                text("SELECT user_id, email, permissions, is_active FROM admin_users WHERE user_id = :user_id"),
                {"user_id": str(user_id)}
            )
            admin = result.fetchone()
            if admin:
                print(f"⚠️ User found in 'admin_users' by user_id but not email: {admin[1]}")
            else:
                return

        print(f"✅ Admin record found: UserID={admin[0]}, Email={admin[1]}, Active={admin[3]}")
        print(f"Permissions: {admin[2]}")
        
        try:
            perms = admin[2]
            if isinstance(perms, str):
                perms = json.loads(perms)
            print(f"Parsed Permissions: {perms}")
            if "super_admin" in perms:
                print("🌟 User HAS 'super_admin' permission")
            else:
                print("⚠️ User MISSING 'super_admin' permission")
        except Exception as e:
            print(f"❌ Failed to parse permissions: {e}")

if __name__ == "__main__":
    asyncio.run(check_admin())
