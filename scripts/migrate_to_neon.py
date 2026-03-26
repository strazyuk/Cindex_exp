import asyncio
import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table, select, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# --- CONFIGURATION ---
SOURCE_URL = "postgresql+asyncpg://crime:crime@127.0.0.1:5432/crimedb"
# Neon URL from user (updated to asyncpg format)
DEST_URL = "postgresql+asyncpg://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?ssl=require"

TABLES_TO_MIGRATE = [
    "crime_events",
    "area_crime_index",
    "combined_events",
    "dataset"
]

async def init_neon_schema(dest_engine):
    print("Initializing schema on Neon...")
    schema_sql = """
    CREATE EXTENSION IF NOT EXISTS postgis;

    CREATE TABLE IF NOT EXISTS crime_events (
        id              SERIAL PRIMARY KEY,
        source_url      TEXT NOT NULL UNIQUE,
        source_name     VARCHAR(100),
        published_at    TIMESTAMP,
        crawled_at      TIMESTAMP DEFAULT NOW(),
        headline        TEXT,
        body_summary    TEXT,
        crime_type      VARCHAR(100),
        severity        INTEGER,
        location_raw    TEXT,
        thana           VARCHAR(100),
        area            VARCHAR(100),
        lat             DOUBLE PRECISION,
        lng             DOUBLE PRECISION,
        victim_count    INTEGER DEFAULT 0,
        s3_key          TEXT,
        processed       BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS area_crime_index (
        id                      SERIAL PRIMARY KEY,
        area                    VARCHAR(100) NOT NULL UNIQUE,
        thana                   VARCHAR(100),
        lat                     DOUBLE PRECISION,
        lng                     DOUBLE PRECISION,
        crime_index             DOUBLE PRECISION DEFAULT 0,
        crime_index_30d         DOUBLE PRECISION DEFAULT 0,
        crime_index_cumulative  DOUBLE PRECISION DEFAULT 0,
        event_count_30d         INTEGER DEFAULT 0,
        event_count_cumulative  INTEGER DEFAULT 0,
        last_updated            TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS combined_events (
        id           SERIAL PRIMARY KEY,
        source       VARCHAR(20)  NOT NULL,
        area         VARCHAR(200) NOT NULL,
        crime_type   VARCHAR(100),
        severity     INTEGER DEFAULT 5,
        event_date   TIMESTAMP,
        victim_count INTEGER DEFAULT 1,
        lat          DOUBLE PRECISION,
        lng          DOUBLE PRECISION,
        thana        VARCHAR(100),
        source_url   TEXT
    );

    CREATE TABLE IF NOT EXISTS dataset (
        id                      SERIAL PRIMARY KEY,
        incident_month          INTEGER,
        incident_week           INTEGER,
        incident_weekday        VARCHAR(20),
        weekend                 INTEGER,
        part_of_the_day         VARCHAR(20),
        latitude                DOUBLE PRECISION,
        longitude               DOUBLE PRECISION,
        incident_place          VARCHAR(100),
        incident_district       VARCHAR(100),
        incident_division       VARCHAR(100),
        max_temp                DOUBLE PRECISION,
        avg_temp                DOUBLE PRECISION,
        min_temp                DOUBLE PRECISION,
        weather_code            INTEGER,
        precip                  DOUBLE PRECISION,
        humidity                DOUBLE PRECISION,
        visibility              DOUBLE PRECISION,
        cloudcover              DOUBLE PRECISION,
        heatindex               DOUBLE PRECISION,
        season                  VARCHAR(20),
        household               INTEGER,
        male_population         INTEGER,
        female_population       INTEGER,
        total_population        INTEGER,
        gender_ration           DOUBLE PRECISION,
        average_household_size  DOUBLE PRECISION,
        density_per_kmsq        DOUBLE PRECISION,
        literacy_rate           DOUBLE PRECISION,
        religious_institution   INTEGER,
        playground              INTEGER,
        park                    INTEGER,
        police_station          INTEGER,
        cyber_cafe              INTEGER,
        school                  INTEGER,
        college                 INTEGER,
        cinema                  INTEGER,
        crime                   INTEGER DEFAULT 0
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_combined_events_live_dedup
        ON combined_events (source, source_url)
        WHERE source = 'live' AND source_url IS NOT NULL;
    """
    async with dest_engine.begin() as conn:
        for statement in schema_sql.split(";"):
            if statement.strip():
                await conn.execute(text(statement))
    print("Schema initialized.")

async def migrate_table(table_name, src_engine, dest_engine):
    print(f"Migrating table: {table_name}...")
    
    # Reflect tables
    metadata = MetaData()
    
    async with src_engine.connect() as src_conn:
        table = await src_conn.run_sync(lambda conn: Table(table_name, metadata, autoload_with=conn))
        result = await src_conn.execute(select(table))
        rows = [dict(row._mapping) for row in result.all()]
        print(f"Found {len(rows)} rows in {table_name}.")

    if not rows:
        return

    async with dest_engine.begin() as dest_conn:
        # Clear existing data to avoid conflicts on retry
        await dest_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        
        # Batch insert
        await dest_conn.execute(insert(table), rows)
        print(f"Successfully migrated {len(rows)} rows to {table_name}.")

async def main():
    src_engine = create_async_engine(SOURCE_URL)
    dest_engine = create_async_engine(DEST_URL)

    try:
        await init_neon_schema(dest_engine)
        for table in TABLES_TO_MIGRATE:
            await migrate_table(table, src_engine, dest_engine)
        print("\nMigration Completed Successfully!")
    finally:
        await src_engine.dispose()
        await dest_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
