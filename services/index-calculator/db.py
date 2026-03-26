from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
_engine = None
_AsyncSessionLocal = None


def get_session_factory():
    """Create a fresh engine/session factory for every request to avoid loop-sharing issues."""
    # Mask password for safe logging
    safe_url = DATABASE_URL.replace(DATABASE_URL.split(":")[2].split("@")[0], "********") if ":" in DATABASE_URL else DATABASE_URL
    print(f"DEBUG: Initializing session with URL: {safe_url}")
    
    # Use NullPool + Dynamic creation to be totally safe in warm Lambda containers
    engine = create_async_engine(
        DATABASE_URL.strip(), # Ensure no leading/trailing whitespace
        poolclass=NullPool,
        # Mandatory for PgBouncer/Supabase Pooler on port 6543 (Transaction Mode)
        connect_args={
            "statement_cache_size": 0,
            "command_timeout": 20
        }
    )
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def repopulate_combined_table():
    """
    Freshly merge data from crime_events and dataset into combined_events.
    Ensures that compound names (like 'dhaka university') are preserved as single units.
    Limits historical data to 'dhaka' only.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        # 1. Truncate the table for a fresh start
        await session.execute(text("TRUNCATE public.combined_events RESTART IDENTITY;"))

        # 2. Insert historical data (Dhaka only)
        await session.execute(text("""
            INSERT INTO public.combined_events (source, area, crime_type, severity, event_date, victim_count, lat, lng, thana)
            SELECT
                'historical' AS source,
                LOWER(TRIM(incident_place::TEXT))::VARCHAR(200) AS area,
                LOWER(TRIM(crime::TEXT))::VARCHAR(100) AS crime_type,
                5::INTEGER AS severity,
                NULL::TIMESTAMP AS event_date,
                1::INTEGER AS victim_count,
                latitude::DOUBLE PRECISION AS lat,
                longitude::DOUBLE PRECISION AS lng,
                LOWER(TRIM(incident_district::TEXT))::VARCHAR(100) AS thana
            FROM public.dataset
            WHERE incident_place IS NOT NULL;
        """))

        # 3. Insert live data from crime_events
        await session.execute(text("""
            INSERT INTO public.combined_events (source, area, crime_type, severity, event_date, victim_count, lat, lng, thana, source_url)
            SELECT
                'live' AS source,
                LOWER(TRIM(area))::VARCHAR(200) AS area,
                LOWER(TRIM(crime_type))::VARCHAR(100) AS crime_type,
                severity::INTEGER AS severity,
                COALESCE(published_at, crawled_at)::TIMESTAMP AS event_date,
                COALESCE(victim_count, 1)::INTEGER AS victim_count,
                lat::DOUBLE PRECISION AS lat,
                lng::DOUBLE PRECISION AS lng,
                LOWER(TRIM(thana))::VARCHAR(100) AS thana,
                source_url
            FROM public.crime_events
            WHERE area IS NOT NULL;
        """))

        await session.commit()


async def get_all_events_by_area() -> dict:
    """
    Query the combined_events table (unified source of truth) and return:
      area -> { 'live': [...], 'all': [...] }
    - 'live': live crawler events only (for 30-day index)
    - 'all':  live + historical (for cumulative index)
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(text("""
            SELECT
                area,
                source,
                crime_type,
                severity,
                event_date,
                victim_count,
                lat,
                lng,
                thana
            FROM public.combined_events
            ORDER BY area, event_date DESC NULLS LAST
        """))
        rows = result.mappings().all()

    area_map: dict = {}

    for row in rows:
        area = row["area"]
        if area not in area_map:
            area_map[area] = {"live": [], "all": []}

        event = {
            "crime_type":   row["crime_type"],
            "severity":     row["severity"],
            "published_at": row["event_date"],
            "victim_count": row["victim_count"],
            "lat":          row["lat"],
            "lng":          row["lng"],
            "thana":        row["thana"],
        }

        area_map[area]["all"].append(event)
        if row["source"] == "live":
            area_map[area]["live"].append(event)

    return area_map


async def upsert_area_index(
    area: str,
    idx_30d: float,
    count_30d: int,
    idx_cum: float,
    count_cum: int,
    lat: float,
    lng: float,
    thana: str = None
):
    """Update both 30-day and cumulative indices in the database."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(text("""
            INSERT INTO public.area_crime_index (
                area, crime_index, event_count_30d,
                crime_index_30d, crime_index_cumulative, event_count_cumulative,
                lat, lng, thana, last_updated
            )
            VALUES (
                :area, :idx_30d, :count_30d,
                :idx_30d, :idx_cum, :count_cum,
                :lat, :lng, :thana, NOW()
            )
            ON CONFLICT (area) DO UPDATE SET
                crime_index            = :idx_30d,
                event_count_30d        = :count_30d,
                crime_index_30d        = :idx_30d,
                crime_index_cumulative = :idx_cum,
                event_count_cumulative = :count_cum,
                lat                    = COALESCE(:lat, area_crime_index.lat),
                lng                    = COALESCE(:lng, area_crime_index.lng),
                thana                  = COALESCE(:thana, area_crime_index.thana),
                last_updated           = NOW()
        """), {
            "area": area,
            "idx_30d": idx_30d, "count_30d": count_30d,
            "idx_cum":  idx_cum,  "count_cum":  count_cum,
            "lat": lat, "lng": lng, "thana": thana
        })

        # Log 30-day score to history
        await session.execute(text("""
            INSERT INTO public.index_history (area, crime_index, recorded_at)
            VALUES (:area, :idx_30d, NOW())
        """), {"area": area, "idx_30d": idx_30d})

        await session.commit()


async def get_all_area_indexes() -> list:
    """Fetch all calculated indices directly from the database (No Redis)."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("""
                SELECT
                    area,
                    crime_index,
                    event_count_30d,
                    crime_index_30d,
                    crime_index_cumulative,
                    event_count_cumulative,
                    lat,
                    lng,
                    thana,
                    last_updated
                FROM public.area_crime_index
            """))
            rows = result.mappings().all()
            # Convert to plain dicts, coercing datetime to string for JSON
            return [
                {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in dict(row).items()}
                for row in rows
            ]
    except Exception as e:
        print(f"CRITICAL ERROR in get_all_area_indexes: {str(e)}")
        traceback.print_exc()
        raise e


async def get_area_index_from_db(area: str) -> dict:
    """Fetch a specific area index directly from the database."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(text("""
            SELECT
                area,
                crime_index,
                event_count_30d,
                crime_index_30d,
                crime_index_cumulative,
                event_count_cumulative,
                lat,
                lng,
                thana,
                last_updated
            FROM public.area_crime_index
            WHERE LOWER(area) = LOWER(:area)
        """), {"area": area})
        row = result.mappings().first()
        if not row:
            return None
        return {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in dict(row).items()}
