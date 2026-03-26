import asyncio
import asyncpg

async def check_areas():
    url = "postgresql://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch("SELECT area, COUNT(*) FROM public.combined_events GROUP BY area ORDER BY COUNT(*) DESC LIMIT 20")
        print("TOP AREAS IN COMBINED_EVENTS:")
        for r in rows:
            print(f"- {r['area']}: {r['count']}")
            
        rows = await conn.fetch("SELECT area, COUNT(*) FROM public.area_crime_index GROUP BY area")
        print("\nAREAS IN AREA_CRIME_INDEX:")
        for r in rows:
            print(f"- {r['area']}: {r['count']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_areas())
