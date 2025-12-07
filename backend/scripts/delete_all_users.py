#!/usr/bin/env python3
"""
Comprehensive User Deletion Script for Agent47
This script deletes all users and their related data from the database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_database
from core.database.models import (
    User, Task, UserSelectedAgent, TeamInvite, InboxMessage, 
    UserAnalytics, UserPlatformToken, PlatformAuditLog
)
from sqlalchemy import select, delete
from core.config import settings

async def delete_all_user_data():
    """Delete all users and their related data from the database"""
    db = get_database()
    
    async with db.get_session() as session:
        print("🗑️  Starting comprehensive user data cleanup...")
        
        # Count existing data
        user_count = await session.execute(select(User))
        users = user_count.scalars().all()
        
        if not users:
            print("✅ No users found in the database. Nothing to delete.")
            return
        
        print(f"📊 Found {len(users)} users to delete")
        
        # Delete related data first (to avoid foreign key constraints)
        print("🧹 Cleaning up related data...")
        
        # Delete user selected agents
        await session.execute(delete(UserSelectedAgent))
        print("   ✅ Deleted user selected agents")
        
        # Delete team invites
        await session.execute(delete(TeamInvite))
        print("   ✅ Deleted team invites")
        
        # Delete inbox messages
        await session.execute(delete(InboxMessage))
        print("   ✅ Deleted inbox messages")
        
        # Delete user analytics
        await session.execute(delete(UserAnalytics))
        print("   ✅ Deleted user analytics")
        
        # Delete user platform tokens
        await session.execute(delete(UserPlatformToken))
        print("   ✅ Deleted user platform tokens")
        
        # Delete platform audit logs
        await session.execute(delete(PlatformAuditLog))
        print("   ✅ Deleted platform audit logs")
        
        # Delete tasks
        await session.execute(delete(Task))
        print("   ✅ Deleted tasks")
        
        # Finally, delete all users
        print("👥 Deleting all users...")
        await session.execute(delete(User))
        
        # Commit all changes
        await session.commit()
        
        print(f"🎉 SUCCESS: All {len(users)} users and their related data have been deleted!")
        print("✨ Database is now clean and ready for fresh testing.")

async def list_user_data():
    """List all user-related data in the database"""
    db = get_database()
    
    async with db.get_session() as session:
        print("📊 Current user data in database:")
        print("-" * 50)
        
        # Count users
        user_count = await session.execute(select(User))
        users = user_count.scalars().all()
        print(f"👥 Users: {len(users)}")
        
        # Count user selected agents
        agent_count = await session.execute(select(UserSelectedAgent))
        agents = agent_count.scalars().all()
        print(f"🤖 User Selected Agents: {len(agents)}")
        
        # Count team invites
        invite_count = await session.execute(select(TeamInvite))
        invites = invite_count.scalars().all()
        print(f"👥 Team Invites: {len(invites)}")
        
        # Count inbox messages
        message_count = await session.execute(select(InboxMessage))
        messages = message_count.scalars().all()
        print(f"📧 Inbox Messages: {len(messages)}")
        
        # Count user analytics
        analytics_count = await session.execute(select(UserAnalytics))
        analytics = analytics_count.scalars().all()
        print(f"📈 User Analytics: {len(analytics)}")
        
        # Count user platform tokens
        token_count = await session.execute(select(UserPlatformToken))
        tokens = token_count.scalars().all()
        print(f"🔑 User Platform Tokens: {len(tokens)}")
        
        # Count platform audit logs
        audit_count = await session.execute(select(PlatformAuditLog))
        audits = audit_count.scalars().all()
        print(f"📝 Platform Audit Logs: {len(audits)}")
        
        # Count tasks
        task_count = await session.execute(select(Task))
        tasks = task_count.scalars().all()
        print(f"📋 Tasks: {len(tasks)}")
        
        print("-" * 50)
        total_items = len(users) + len(agents) + len(invites) + len(messages) + len(analytics) + len(tokens) + len(audits) + len(tasks)
        print(f"📊 Total items: {total_items}")

def print_help():
    """Print help information"""
    print("""
🗑️  Agent47 Comprehensive User Deletion Script

Usage:
    python delete_all_users.py [command]

Commands:
    list        - List all user-related data in the database
    delete      - Delete ALL users and their related data (DANGEROUS!)
    help        - Show this help message

Examples:
    python delete_all_users.py list
    python delete_all_users.py delete

⚠️  WARNING: The 'delete' command will permanently remove ALL user data!
    This includes:
    - All users
    - User selected agents
    - Team invites
    - Inbox messages
    - User analytics
    - User platform tokens
    - Platform audit logs
    - Tasks

    This action cannot be undone!

Note: This script is for development/testing purposes only.
    """)

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "list":
            await list_user_data()
        elif command == "delete":
            print("⚠️  WARNING: This will delete ALL user data from the database!")
            print("This action cannot be undone.")
            print("Auto-confirming deletion...")
            await delete_all_user_data()
        elif command == "help":
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
