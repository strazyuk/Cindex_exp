import asyncio
import asyncpg

async def check_parity():
    url = "postgresql://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
    conn = await asyncpg.connect(url)
    try:
        tables = ['crime_events', 'area_crime_index', 'combined_events', 'dataset']
        for t in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM public.{t}")
            print(f"TABLE {t}: {count} records")
            
        # Sample check
        sample = await conn.fetch(f"SELECT area, crime_type FROM public.crime_events LIMIT 5")
        print("\nSAMPLE CRIME EVENTS:")
        for s in sample:
            print(f"- {s['area']}: {s['crime_type']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_parity())
