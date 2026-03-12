-- scripts/init_db.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- Raw crime events extracted by NLP
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

-- Aggregated index per zone
CREATE TABLE IF NOT EXISTS area_crime_index (
    id                      SERIAL PRIMARY KEY,
    area                    VARCHAR(100) NOT NULL UNIQUE,
    thana                   VARCHAR(100),
    lat                     DOUBLE PRECISION,
    lng                     DOUBLE PRECISION,
    crime_index             DOUBLE PRECISION DEFAULT 0,   -- alias for 30-day index
    crime_index_30d         DOUBLE PRECISION DEFAULT 0,   -- 30-day rolling index
    crime_index_cumulative  DOUBLE PRECISION DEFAULT 0,   -- all-time index (live + historical)
    event_count_30d         INTEGER DEFAULT 0,
    event_count_cumulative  INTEGER DEFAULT 0,            -- live + historical event count
    last_updated            TIMESTAMP DEFAULT NOW()
);

-- Index history
CREATE TABLE IF NOT EXISTS index_history (
    id          SERIAL PRIMARY KEY,
    area        VARCHAR(100),
    crime_index DOUBLE PRECISION,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Historical Bangladesh Crime Dataset
-- Ingested via ingest_csv.py; used for cumulative index calculation
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

CREATE INDEX IF NOT EXISTS idx_crime_events_area ON crime_events(area);
CREATE INDEX IF NOT EXISTS idx_crime_events_published_at ON crime_events(published_at);
CREATE INDEX IF NOT EXISTS idx_area_index_area ON area_crime_index(area);
CREATE INDEX IF NOT EXISTS idx_dataset_place ON dataset(incident_place);
CREATE INDEX IF NOT EXISTS idx_dataset_district ON dataset(incident_district);

-- Unified event store: merges crime_events + dataset into one normalized table.
-- area is always lowercase + trimmed. Compound names (e.g. 'dhaka university')
-- are preserved as-is to prevent collision with simple names like 'dhaka'.
DROP TABLE IF EXISTS combined_events;
CREATE TABLE combined_events (
    id           SERIAL PRIMARY KEY,
    source       VARCHAR(20)  NOT NULL,   -- 'live' or 'historical'
    area         VARCHAR(200) NOT NULL,   -- lowercase trimmed full compound name
    crime_type   VARCHAR(100),
    severity     INTEGER DEFAULT 5,
    event_date   TIMESTAMP,              -- NULL for historical rows (no date)
    victim_count INTEGER DEFAULT 1,
    lat          DOUBLE PRECISION,
    lng          DOUBLE PRECISION,
    thana        VARCHAR(100),
    source_url   TEXT                     -- dedup key for live events
);

-- Partial unique index: only prevents duplicates for live events that have a URL.
CREATE UNIQUE INDEX IF NOT EXISTS idx_combined_events_live_dedup
    ON combined_events (source, source_url)
    WHERE source = 'live' AND source_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_combined_events_area       ON combined_events(area);
CREATE INDEX IF NOT EXISTS idx_combined_events_event_date ON combined_events(event_date);
CREATE INDEX IF NOT EXISTS idx_combined_events_source     ON combined_events(source);
