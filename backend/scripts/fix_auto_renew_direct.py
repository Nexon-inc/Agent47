import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("Error: SUPABASE_DB_URL not found in .env")
    exit(1)

# Ensure it's a sync driver for this simple script
if db_url.startswith("postgresql+asyncpg"):
    db_url = db_url.replace("postgresql+asyncpg", "postgresql")
elif db_url.startswith("postgresql://"):
    pass
else:
    # Just try to force it to postgresql if it's something else
    db_url = db_url.split("://")[1]
    db_url = f"postgresql://{db_url}"

print(f"Connecting to database...")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Checking for 'auto_renew' column in 'subscriptions' table...")
        
        # Check if column exists
        check_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'subscriptions'
                AND column_name = 'auto_renew'
            );
        """)
        result = conn.execute(check_sql)
        column_exists = result.scalar()
        
        if not column_exists:
            print("Adding 'auto_renew' column to 'subscriptions' table...")
            alter_sql = text("ALTER TABLE subscriptions ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE;")
            conn.execute(alter_sql)
            conn.commit()
            print("Successfully added 'auto_renew' column.")
        else:
            print("'auto_renew' column already exists.")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Finished.")
