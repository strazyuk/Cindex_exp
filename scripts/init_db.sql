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
    id              SERIAL PRIMARY KEY,
    area            VARCHAR(100) NOT NULL UNIQUE,
    thana           VARCHAR(100),
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    crime_index     DOUBLE PRECISION DEFAULT 0,
    event_count_30d INTEGER DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT NOW()
);

-- Index history
CREATE TABLE IF NOT EXISTS index_history (
    id          SERIAL PRIMARY KEY,
    area        VARCHAR(100),
    crime_index DOUBLE PRECISION,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crime_events_area ON crime_events(area);
CREATE INDEX IF NOT EXISTS idx_crime_events_published_at ON crime_events(published_at);
CREATE INDEX IF NOT EXISTS idx_area_index_area ON area_crime_index(area);
