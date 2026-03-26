import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, MetaData, Table, select
from sqlalchemy.dialects.postgresql import insert

# --- CONFIGURATION ---
LOCAL_DB_URL = "postgresql+asyncpg://crime:crime@localhost:5432/crimedb"
SUPABASE_DB_URL = "postgresql+asyncpg://postgres.zyoddyuiqyfaxzuiikoo:db498709@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

TABLES_TO_MIGRATE = [
    "crime_events",
    "area_crime_index",
    "combined_events",
    "dataset",
    "index_history"
]

async def migrate_table(local_engine, supabase_engine, table_name):
    print(f"Migrating table: {table_name}...")
    
    async with local_engine.connect() as local_conn:
        # Reflect table schema
        metadata = MetaData()
        table = await local_conn.run_sync(lambda conn: Table(table_name, metadata, autoload_with=conn))
        
        # Fetch all records
        result = await local_conn.execute(select(table))
        rows = [dict(row._mapping) for row in result]
        
    if not rows:
        print(f"  No records found in {table_name}. Skipping.")
        return

    print(f"  Found {len(rows)} records. Inserting into Supabase...")
    
    async with supabase_engine.begin() as supabase_conn:
        # We use 'ON CONFLICT DO NOTHING' to prevent errors on re-run
        # Note: This requires the table to have a primary key or unique constraint
        # Most of our tables have IDs or unique URLs.
        
        # For combined_events, we handle the unique constraint on (source, source_url)
        stmt = insert(table).values(rows)
        if table_name == "crime_events":
            stmt = stmt.on_conflict_do_update(
                index_elements=["source_url"],
                set_={k: v for k, v in stmt.excluded.items() if k != "id"}
            )
        elif table_name == "area_crime_index":
            stmt = stmt.on_conflict_do_update(
                index_elements=["area"],
                set_={k: v for k, v in stmt.excluded.items() if k != "id"}
            )
        elif table_name == "combined_events":
            # combined_events unique index is idx_combined_events_live_dedup (source, source_url)
            # But SQLAlchemy on_conflict_do_nothing doesn't easily support partial indexes
            # So we'll try simple insert and let the DB handle it if possible, 
            # or just do nothing on conflict.
            stmt = stmt.on_conflict_do_nothing()
        else:
            stmt = stmt.on_conflict_do_nothing()
            
        await supabase_conn.execute(stmt)
        print(f"  Successfully migrated {table_name}.")

async def main():
    print("🚀 Starting Data Migration: Local -> Supabase")
    
    local_engine = create_async_engine(LOCAL_DB_URL)
    supabase_engine = create_async_engine(SUPABASE_DB_URL)
    
    try:
        for table_name in TABLES_TO_MIGRATE:
            try:
                await migrate_table(local_engine, supabase_engine, table_name)
            except Exception as e:
                print(f"❌ Error migrating {table_name}: {e}")
                
        print("\n✅ Migration Finished!")
    finally:
        await local_engine.dispose()
        await supabase_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
