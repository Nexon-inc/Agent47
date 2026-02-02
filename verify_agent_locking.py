
import asyncio
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, delete, select
from core.database.models import User, UserSelectedAgent, UserTier
from core.config import get_settings

# Mock setup
settings = get_settings()
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def verify_locking_logic():
    async with AsyncSessionLocal() as db:
        print("Setting up test data...")
        # 1. Create or get test user (Pro Tier)
        result = await db.execute(text("SELECT id FROM users WHERE email = 'test_pro_locking@example.com'"))
        user_id = result.scalar()
        
        if not user_id:
            from uuid import uuid4
            user_id = str(uuid4())
            await db.execute(
                text("INSERT INTO users (id, email, full_name, tier, hashed_password) VALUES (:id, :email, :name, :tier, :pass)"),
                {"id": user_id, "email": "test_pro_locking@example.com", "name": "Test User", "tier": "pro", "pass": "hashed"}
            )
            await db.commit()
            print(f"Created test user {user_id}")
        else:
            # Ensure tier is pro
            await db.execute(text("UPDATE users SET tier = 'pro' WHERE id = :id"), {"id": user_id})
            await db.execute(delete(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
            await db.commit()
            print(f"Reset test user {user_id}")

        # 2. Simulate User having ONE locked agent (selected 10 days ago)
        agent1_id = "aria"
        ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
        
        db.add(UserSelectedAgent(
            user_id=user_id,
            agent_key=agent1_id,
            status="active",
            locked=True,
            created_at=ten_days_ago,
            updated_at=ten_days_ago
        ))
        await db.commit()
        print(f"Added locked agent {agent1_id} (created 10 days ago)")

        # 3. Simulate Request: ADD a new agent (clara) while keeping aria.
        # This emulates the 'save_selected_agents' logic we just wrote, but calling the logic directly isn't easy 
        # without mocking the Request object and dependencies. 
        # Instead, I will call the endpoint handler logic implementation? 
        # No, better to use `httpx` against the running server if possible, OR just simulate the logic with DB queries 
        # to ensure I didn't break SQL syntax, but the logic itself is Python.
        
        # Let's verify the logic via unit-test style here.
        # Logic: 
        # fetch existing rows -> verify all locked ones are in new list -> delete all -> re-insert (preserving old timestamps)
        
        # New selection: ['aria', 'clara']
        new_selection = ["aria", "clara"]
        
        print("\n--- Test 1: Add 'clara' keeping 'aria' (Valid) ---")
        
        # Fetch current
        result = await db.execute(select(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
        existing = result.scalars().all()
        
        locked_map = {row.agent_key: row for row in existing if row.locked}
        
        # Validate missing
        if any(k not in new_selection for k in locked_map):
            print("❌ Test 1 Failed: Logic should allow this, but check failed locally?")
        else:
            print("✅ Validation Passed: All locked agents present.")
            
        # Simulate Save
        # Delete 
        await db.execute(delete(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
        
        # Re-insert
        now_utc = datetime.now(timezone.utc)
        for key in new_selection:
            if key in locked_map:
                orig = locked_map[key]
                # Check timestamp preservation
                db.add(UserSelectedAgent(
                    user_id=user_id,
                    agent_key=key,
                    status=orig.status,
                    locked=True,
                    created_at=orig.created_at, # KEY CHECK
                    updated_at=now_utc
                ))
            else:
                db.add(UserSelectedAgent(
                    user_id=user_id,
                    agent_key=key,
                    status="active",
                    locked=True, # Pro tier locks new ones
                    created_at=now_utc,
                    updated_at=now_utc
                ))
        await db.commit()
        
        # Verify DB state
        result = await db.execute(select(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
        rows = result.scalars().all()
        row_map = {r.agent_key: r for r in rows}
        
        if len(rows) != 2:
            print(f"❌ Test 1 Failed: Expected 2 agents, found {len(rows)}")
        elif "aria" not in row_map or "clara" not in row_map:
             print("❌ Test 1 Failed: Missing agents")
        else:
            aria = row_map["aria"]
            # Check aria timestamp - should be ~10 days old, not new
            age = datetime.now(timezone.utc) - aria.created_at.replace(tzinfo=timezone.utc)
            if age.days != 10:
                print(f"❌ Test 1 Failed: Timestamp reset! Age is {age}")
            else:
                print("✅ Test 1 Passed: Agents updated, locked agent timestamp preserved.")

        # --- Test 2: Remove 'aria' (Invalid) ---
        print("\n--- Test 2: Remove 'aria' (Invalid) ---")
        try_selection = ["clara", "eric"] # Dropping aria
        
        # Fetch current (now has aria and clara)
        result = await db.execute(select(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
        existing = result.scalars().all()
        locked_map = {row.agent_key: row for row in existing if row.locked} # Aria locked (10 days old), Clara locked (new)
        
        missing = [k for k in locked_map if k not in try_selection]
        if missing:
            print(f"✅ Test 2 Passed: correctly identified missing locked agents: {missing}")
        else:
            print(f"❌ Test 2 Failed: Should have flagged missing agents but didn't.")

        # Cleanup
        await db.execute(delete(UserSelectedAgent).where(UserSelectedAgent.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        print("\nCleanup complete.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_locking_logic())
