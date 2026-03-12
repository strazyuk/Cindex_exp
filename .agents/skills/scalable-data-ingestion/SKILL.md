---
name: Scalable Data Ingestion
description: Professional-grade pipeline strategies for high-concurrency crawling, deduplication, and PostgreSQL performance.
---

# Scalable Data Ingestion Skill

Strategies for robust and high-volume data collection in the Dhaka Crime Index.

## 🕸️ High-Concurrency Crawling
- **Rate Limiting**: Use a rotating user-agent and adaptive delays to respect news site `robots.txt` while maintaining speed.
- **Failover**: Ensure the crawler stores raw HTML in S3/LocalStack immediately upon retrieval, before any processing occurs.
- **Deduplication**: Implement a Bloom filter or simple URL hashing in Redis to prevent re-crawling the same article within a 24-hour window.

## 💾 PostgreSQL High-Volume Ingest
- **Batching**: Use `COPY` or `INSERT ... ON CONFLICT` with batches of 100-500 rows instead of individual commits.
- **Indexing Strategy**: Drop or disable non-essential indexes during massive data imports (e.g., initial CSV ingestion) and rebuild them afterward.
- **Maintenance**: Periodically run `VACUUM ANALYZE` on the `combined_events` table to maintain query planner accuracy.

## 🔄 Live Sync Pattern
- **Atomic Operations**: When rebuilding the `combined_events` table, perform the deletion and insertion within a single SQL transaction to prevent frontend data gaps.
- **State Management**: Use a `sync_status` table to track the last successful crawl timestamp and error counts for monitoring.
