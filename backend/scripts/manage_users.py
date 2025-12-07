#!/usr/bin/env python3
"""
User Management Script for Agent47
This script helps manage users in the database for development purposes.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_database
from core.database.models import User, UserSelectedAgent
from sqlalchemy import select, delete, text
from core.config import settings

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
            print("Onboarding")
            print("-" * 100)
            print(f"Completed:          {bool(getattr(user, 'onboarding_completed', False))}")
            print(f"Completed At:       {user.onboarding_completed_at.isoformat() if getattr(user, 'onboarding_completed_at', None) else ''}")
            onboarding_data = getattr(user, 'onboarding_data', None) or {}
            # Remove deprecated keys if present
            if isinstance(onboarding_data, dict):
                for k in ["social", "tutorials", "workflow"]:
                    onboarding_data.pop(k, None)
            try:
                import json
                print("Data:")
                print(json.dumps(onboarding_data, indent=2, ensure_ascii=False))
            except Exception:
                print(f"Data:               {onboarding_data}")
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

async def delete_user_by_email(email: str):
    """Delete a user by email address"""
    db = get_database()
    
    async with db.get_session() as session:
        # Find the user
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with email '{email}' not found.")
            return False
        
        print(f"Found user: {user.username} ({user.email})")
        print(f"User ID: {user.id}")
        print(f"Created: {user.created_at}")
        
        # Delete the user
        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()
        
        print(f"✅ User '{email}' has been deleted successfully.")
        return True

async def delete_user_by_id(user_id: int):
    """Delete a user by ID"""
    db = get_database()
    
    async with db.get_session() as session:
        # Find the user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with ID '{user_id}' not found.")
            return False
        
        print(f"Found user: {user.username} ({user.email})")
        print(f"User ID: {user.id}")
        print(f"Created: {user.created_at}")
        
        # Delete the user
        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()
        
        print(f"✅ User ID '{user_id}' has been deleted successfully.")
        return True

async def clear_all_users():
    """Clear all users from the database (DANGEROUS!)"""
    db = get_database()
    
    async with db.get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users to delete.")
            return
        
        print(f"WARNING: This will delete ALL {len(users)} users from the database!")
        print("This action cannot be undone.")
        
        # Auto-confirm for non-interactive environments
        print("Auto-confirming deletion...")
        confirm = "DELETE ALL USERS"
        
        # Delete dependent rows referencing users to satisfy FK constraints
        # Note: extend this list if other FK constraints appear
        try:
            await session.execute(text("DELETE FROM user_selected_agents"))
        except Exception:
            # Table might not exist in some environments; ignore
            pass

        # Delete all users
        await session.execute(delete(User))
        await session.commit()
        
        print(f"SUCCESS: All {len(users)} users have been deleted.")

def print_help():
    """Print help information"""
    print("""
Agent47 User Management Script

Usage:
    python manage_users.py [command] [arguments]

Commands:
    list                    - List all users in the database
    delete-email <email>    - Delete user by email address
    delete-id <id>          - Delete user by ID
    clear-all               - Delete ALL users (DANGEROUS!)
    help                    - Show this help message

Examples:
    python manage_users.py list
    python manage_users.py delete-email john@example.com
    python manage_users.py delete-id 1
    python manage_users.py clear-all

Note: This script is for development purposes only.
    """)

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "list":
            await list_users()
        elif command == "delete-email":
            if len(sys.argv) < 3:
                print("Error: Email address required.")
                print("Usage: python manage_users.py delete-email <email>")
                return
            email = sys.argv[2]
            await delete_user_by_email(email)
        elif command == "delete-id":
            if len(sys.argv) < 3:
                print("Error: User ID required.")
                print("Usage: python manage_users.py delete-id <id>")
                return
            try:
                user_id = int(sys.argv[2])
                await delete_user_by_id(user_id)
            except ValueError:
                print("Error: User ID must be a number.")
                return
        elif command == "clear-all":
            await clear_all_users()
        elif command == "help":
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
