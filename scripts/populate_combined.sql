-- scripts/populate_combined.sql
--
-- Populates the combined_events table from both sources.
-- Safe to re-run: ON CONFLICT clauses skip duplicates.
-- Run this after init_db.sql and after ingest_csv.py has been executed.

-- 1. Historical data from the Bangladesh Crime Dataset
--    - area: full compound name kept (e.g. 'dhaka university' != 'dhaka')
--    - event_date: NULL (no date in dataset, formula applies max decay)
--    - victim_count: 1 per row (each row is one recorded incident)
--    - crime mapped to crime_type (murder, robbery, etc.)
INSERT INTO combined_events (source, area, crime_type, severity, event_date, victim_count, lat, lng, thana)
SELECT
    'historical',
    LOWER(TRIM(incident_place)),
    LOWER(TRIM(crime)),
    5,
    NULL,
    1,
    latitude,
    longitude,
    LOWER(TRIM(incident_district))
FROM dataset
WHERE incident_place IS NOT NULL
  AND LOWER(TRIM(incident_district)) = 'dhaka';

-- 2. Live events from crawler/NLP pipeline
--    - source_url used for deduplication via partial unique index
INSERT INTO combined_events (source, area, crime_type, severity, event_date, victim_count, lat, lng, thana, source_url)
SELECT
    'live',
    LOWER(TRIM(area)),
    LOWER(TRIM(crime_type)),
    severity,
    COALESCE(published_at, crawled_at),
    COALESCE(victim_count, 0),
    lat,
    lng,
    LOWER(TRIM(thana)),
    source_url
FROM crime_events
WHERE area IS NOT NULL
ON CONFLICT (source, source_url) WHERE source = 'live' AND source_url IS NOT NULL DO NOTHING;

-- Confirm counts
SELECT source, COUNT(*) FROM combined_events GROUP BY source ORDER BY source;
