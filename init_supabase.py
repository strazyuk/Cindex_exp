import asyncio
import asyncpg
import sys

async def run_init():
    conn_str = "postgresql://postgres:db498709@db.zyoddyuiqyfaxzuiikoo.supabase.co:5432/postgres"
    print(f"Connecting to Supabase...")
    try:
        conn = await asyncpg.connect(conn_str)
        with open("scripts/init_db.sql", "r") as f:
            sql = f.read()
            
        print("Executing init_db.sql...")
        await conn.execute(sql)
        print("Successfully initialized Supabase database tables!")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_init())
