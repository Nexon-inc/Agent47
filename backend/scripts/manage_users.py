#!/usr/bin/env python3
"""
User Management Script for Agent47
This script helps manage users in the database for development purposes.
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_database, supabase_manager
from core.database.models import User, UserSelectedAgent
from sqlalchemy import select, delete, text
from core.config import settings

def apply_overrides(args):
    """Apply CLI overrides to settings"""
    if args.url:
        settings.supabase.supabase_url = args.url
    if args.key:
        settings.supabase.supabase_service_role_key = args.key
    if args.db_url:
        settings.supabase.supabase_db_url = args.db_url
    
    # Re-initialize database manager if overrides were provided
    if args.url or args.key or args.db_url:
        print("Applying manual credential overrides...")
        # Reset initialized flag to force re-initialization with new settings
        supabase_manager._initialized = False

async def list_users():
    """List all users in the database"""
    db = get_database()
    
    async with db.get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"\nFound {len(users)} users:\n")
        for idx, user in enumerate(users, start=1):
            print("=" * 100)
            print(f"User #{idx}")
            print("-" * 100)
            print(f"ID:                 {user.id}")
            print(f"Email:              {user.email or ''}")
            print(f"Username:           {user.username or ''}")
            print(f"Full Name:          {user.full_name or ''}")
            print(f"Tier:               {(user.tier.value if getattr(user, 'tier', None) else 'free' if user.tier is None else str(user.tier))}")
            print(f"Active:             {bool(user.is_active)}    Verified: {bool(user.is_verified)}")
            print(f"Created At:         {user.created_at.isoformat() if user.created_at else ''}")
            print(f"Updated At:         {user.updated_at.isoformat() if user.updated_at else ''}")
            print(f"Last Login:         {user.last_login.isoformat() if user.last_login else ''}")
            print()
            
            # Onboarding details
            onboarding_data = getattr(user, 'onboarding_data', None) or {}
            print(f"Onboarding Data: {json.dumps(onboarding_data, indent=2)}")
            print()
            
            # Preferences
            print("Preferences")
            print("-" * 100)
            prefs = getattr(user, 'preferences', None) or {}
            try:
                import json
                print(json.dumps(prefs, indent=2, ensure_ascii=False))
            except Exception:
                print(prefs)
            print()
            
            # Selected Agents
            print("Selected Agents")
            print("-" * 100)
            try:
                agents_result = await session.execute(
                    select(UserSelectedAgent).where(UserSelectedAgent.user_id == user.id)
                )
                agents = agents_result.scalars().all()
                if agents:
                    for agent in agents:
                        print(f"  • {agent.agent_key} - Status: {agent.status} (Locked: {agent.locked}, Automation: {agent.automation_enabled})")
                        if agent.created_at:
                            print(f"    Created: {agent.created_at.isoformat()}")
                else:
                    print("  No agents selected")
            except Exception as e:
                print(f"  Error fetching agents: {e}")
            print()

async def inspect_all():
    """Inspect users in both Supabase Auth and Local Database"""
    db = get_database()
    await db.initialize()
    client = db.get_supabase_client()
    
    print("\n" + "=" * 50)
    print("INSPECTING USERS (Supabase vs Local DB)")
    print("=" * 50)
    
    # 1. Get Supabase Auth Users
    supabase_users = []
    try:
        auth_response = client.auth.admin.list_users()
        supabase_users = auth_response.users
        print(f"Supabase Auth users count: {len(supabase_users)}")
    except Exception as e:
        print(f"Error listing Supabase Auth users: {e}")
        print("Note: Service Role Key is required for this.")
    
    # 2. Get Local DB Users
    db_users = []
    async with db.get_session() as session:
        result = await session.execute(select(User))
        db_users = result.scalars().all()
        print(f"Local Database users count: {len(db_users)}")
    
    # 3. Compare
    supabase_emails = {u.email for u in supabase_users}
    db_emails = {u.email for u in db_users}
    
    print("\n--- SYNC STATUS ---")
    
    # Check for users in Supabase but not in DB (The common source of registration conflicts)
    sync_errors = supabase_emails - db_emails
    if sync_errors:
        print(f"⚠️ FOUND {len(sync_errors)} sync errors (Exists in Supabase Auth but NOT in Local DB):")
        for email in sync_errors:
            # Find the user in supabase_users list to get details
            s_user = next(u for u in supabase_users if u.email == email)
            print(f"  - {email} (Supabase ID: {s_user.id}, Created: {s_user.created_at})")
    else:
        print("✅ No sync errors found (All Supabase users exist in Local DB).")

    # Check for users in DB but not in Supabase (Less common but possible)
    reverse_sync_errors = db_emails - supabase_emails
    if reverse_sync_errors:
        print(f"⚠️ FOUND {len(reverse_sync_errors)} users in DB but NOT in Supabase Auth:")
        for email in reverse_sync_errors:
            print(f"  - {email}")

    print("\n" + "=" * 50)

async def delete_user(email: str):
    """Delete a user from both DB and Supabase Auth"""
    db = get_database()
    await db.initialize()
    client = db.get_supabase_client()
    
    print(f"\nAttempting to delete user: {email}")
    
    # 1. Delete from Local DB
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Delete selections first
            await session.execute(delete(UserSelectedAgent).where(UserSelectedAgent.user_id == user.id))
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
            print(f"✅ Deleted from Local Database.")
        else:
            print(f"ℹ️ User not found in Local Database.")
            
    # 2. Delete from Supabase Auth
    try:
        auth_response = client.auth.admin.list_users()
        s_user = next((u for u in auth_response.users if u.email == email), None)
        if s_user:
            client.auth.admin.delete_user(s_user.id)
            print(f"✅ Deleted from Supabase Auth (Admin ID: {s_user.id}).")
        else:
            print(f"ℹ️ User not found in Supabase Auth.")
    except Exception as e:
        print(f"❌ Error deleting from Supabase Auth: {e}")

async def clear_all():
    """Clear ALL users from both DB and Supabase Auth (DANGEROUS!)"""
    db = get_database()
    await db.initialize()
    client = db.get_supabase_client()
    
    print("\n" + "!" * 50)
    print("CLEARING ALL USERS - DANGEROUS!")
    print("!" * 50)
    
    # 1. Clear Local DB
    async with db.get_session() as session:
        await session.execute(delete(UserSelectedAgent))
        await session.execute(delete(User))
        await session.commit()
        print("✅ Cleared Local Database.")
        
    # 2. Clear Supabase Auth
    try:
        auth_response = client.auth.admin.list_users()
        count = 0
        for u in auth_response.users:
            client.auth.admin.delete_user(u.id)
            count += 1
        print(f"✅ Deleted {count} users from Supabase Auth.")
    except Exception as e:
        print(f"❌ Error clearing Supabase Auth: {e}")

def get_parser():
    parser = argparse.ArgumentParser(description="Agent47 User Management & Debug Tool")
    parser.add_argument("command", choices=["list", "inspect-all", "delete-email", "clear-all"], help="Command to run")
    parser.add_argument("--email", help="Email for delete-email command")
    parser.add_argument("--url", help="Override SUPABASE_URL")
    parser.add_argument("--key", help="Override SUPABASE_SERVICE_ROLE_KEY")
    parser.add_argument("--db-url", help="Override SUPABASE_DB_URL")
    return parser

async def main():
    parser = get_parser()
    args = parser.parse_args()
    
    apply_overrides(args)
    
    try:
        if args.command == "list":
            await list_users()
        elif args.command == "inspect-all":
            await inspect_all()
        elif args.command == "delete-email":
            if not args.email:
                print("❌ --email is required for delete-email command")
                return
            await delete_user(args.email)
        elif args.command == "clear-all":
            await clear_all()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
