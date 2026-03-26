import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

URL = "postgresql+asyncpg://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?ssl=require"

async def test():
    engine = create_async_engine(URL)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO area_crime_index (area, lat, lng, crime_index_30d, crime_index_cumulative, event_count_30d, event_count_cumulative)
            VALUES ('Dhaka', 23.8103, 90.4125, 45.5, 78.2, 10, 50)
            ON CONFLICT (area) DO UPDATE SET last_updated = NOW()
        """))
    print("MANUAL INSERT SUCCESS")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
