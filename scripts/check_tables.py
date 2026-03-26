import asyncio
import asyncpg

URL = "postgresql://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def test():
    try:
        conn = await asyncpg.connect(URL)
        # List all tables in public schema
        rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print("Tables in public schema:")
        for r in rows:
            print(f"- {r['table_name']}")
        
        # Check if area_crime_index exists specifically
        exists = await conn.fetchval("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'area_crime_index')")
        print(f"\n'area_crime_index' exists: {exists}")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
