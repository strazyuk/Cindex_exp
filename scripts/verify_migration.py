import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# --- CONFIGURATION ---
SUPABASE_DB_URL = "postgresql+asyncpg://postgres:db498709@db.zyoddyuiqyfaxzuiikoo.supabase.co:5432/postgres"

async def verify_counts():
    engine = create_async_engine(SUPABASE_DB_URL)
    tables = ["crime_events", "area_crime_index", "combined_events", "dataset", "index_history"]
    
    print("📊 Verification Results (Supabase):")
    async with engine.connect() as conn:
        for table in tables:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  - {table}: {count} records")
            except Exception as e:
                print(f"  - {table}: ❌ Error (does not exist?)")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_counts())
