from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # postgresql+asyncpg://...
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def save_crime_event(data: dict):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO crime_events 
                    (source_url, source_name, published_at, headline, body_summary,
                     crime_type, severity, location_raw, thana, area,
                     lat, lng, victim_count, s3_key, processed)
                VALUES
                    (:source_url, :source_name, :published_at, :headline, :body_summary,
                     :crime_type, :severity, :location_raw, :thana, :area,
                     :lat, :lng, :victim_count, :s3_key, true)
                ON CONFLICT (source_url) DO NOTHING
            """),
            data
        )
        await session.commit()
