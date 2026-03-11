from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_recent_events_by_area() -> dict:
    """Return dict of area → list of crime events (last 30 days)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT area, crime_type, severity, COALESCE(published_at, crawled_at) as event_date, 
                   victim_count, lat, lng
            FROM crime_events
            WHERE (published_at >= NOW() - INTERVAL '30 days' OR crawled_at >= NOW() - INTERVAL '30 days')
              AND area IS NOT NULL
            ORDER BY area, event_date DESC
        """))
        rows = result.mappings().all()

    area_map: dict = {}
    for row in rows:
        area = row["area"]
        if area not in area_map:
            area_map[area] = []
        # Convert row to dict and rename event_date back to published_at for the formula
        d = dict(row)
        d["published_at"] = d.pop("event_date")
        area_map[area].append(d)
    return area_map

async def upsert_area_index(area: str, index: float, count: int, lat: float, lng: float, thana: str = None):
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            INSERT INTO area_crime_index (area, crime_index, event_count_30d, lat, lng, thana, last_updated)
            VALUES (:area, :index, :count, :lat, :lng, :thana, NOW())
            ON CONFLICT (area) DO UPDATE SET
                crime_index = :index,
                event_count_30d = :count,
                lat = COALESCE(:lat, area_crime_index.lat),
                lng = COALESCE(:lng, area_crime_index.lng),
                thana = COALESCE(:thana, area_crime_index.thana),
                last_updated = NOW()
        """), {"area": area, "index": index, "count": count, "lat": lat, "lng": lng, "thana": thana})
        
        await session.execute(text("""
            INSERT INTO index_history (area, crime_index, recorded_at)
            VALUES (:area, :index, NOW())
        """), {"area": area, "index": index})
        await session.commit()
