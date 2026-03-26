import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
_engine = None
_AsyncSessionLocal = None

def get_engine():
    global _engine, _AsyncSessionLocal
    if _engine is None:
        # Note: AWS Lambda non-VPC environments sometimes struggle with IPv6.
        # Use Supabase Pooler (port 6543) if you see [Errno 99].
        _engine = create_async_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=1,
            max_overflow=0
        )
        _AsyncSessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _AsyncSessionLocal

async def save_crime_event(data: dict):
    session_factory = get_engine()
    async with session_factory() as session:
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
