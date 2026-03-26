import asyncio
import logging
import os
import sys

# Ensure an event loop is available at import time for global dependencies
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy import text
from formula import compute_crime_index
from db import (
    get_all_events_by_area, upsert_area_index, get_all_area_indexes,
    repopulate_combined_table, get_area_index_from_db,
    get_session_factory
)
# from redis_client import cache_area_index, get_all_indexes # REMOVED REDIS
from mangum import Mangum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crime Index Calculator API")

async def recalculate_all_indexes():
    """Recalculate dual crime indexes (30d and cumulative) and update DB."""
    logger.info("Recalculating crime indexes (Robust Combined Table)...")
    try:
        from db import repopulate_combined_table
        await repopulate_combined_table()

        all_area_events = await get_all_events_by_area()
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        for area, event_sets in all_area_events.items():
            logger.info(f"Processing area: {area}")
            live_events = event_sets.get("live", [])
            all_events  = event_sets.get("all", [])

            recent_events = [
                e for e in live_events
                if e.get("published_at") and 
                   (e["published_at"] if e["published_at"].tzinfo else 
                    e["published_at"].replace(tzinfo=timezone.utc)) >= thirty_days_ago
            ]

            idx_30d = compute_crime_index(recent_events)
            idx_cum = compute_crime_index(all_events, emphasize_history=True)

            lat   = next((e["lat"]   for e in all_events if e.get("lat")),   None)
            lng   = next((e["lng"]   for e in all_events if e.get("lng")),   None)
            thana = next((e["thana"] for e in live_events if e.get("thana")), None) or \
                    next((e["thana"] for e in all_events  if e.get("thana")), None)

            display_area = area.title()

            await upsert_area_index(
                display_area,
                idx_30d, len(recent_events),
                idx_cum, len(all_events),
                lat, lng, thana
            )
            
            logger.info(
                f"Completed area '{display_area}': 30d={idx_30d} ({len(recent_events)} evts), "
                f"Cum={idx_cum} ({len(all_events)} evts)"
            )
        
        logger.info(f"Recalculation finished for {len(all_area_events)} areas.")
            
    except Exception as e:
        logger.error(f"Error in recalculate_all_indexes: {e}", exc_info=True)


@app.get("/diag")
async def diagnostic():
    """Diagnostic route to check table visibility from Lambda."""
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            # List tables
            res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [r[0] for r in res.all()]
            
            # Check current search path
            res = await session.execute(text("SHOW search_path"))
            path = res.scalar()
            
            return {
                "tables": tables,
                "search_path": path,
                "db_url_masked": os.getenv("DATABASE_URL").split("@")[-1] if os.getenv("DATABASE_URL") else None
            }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Dhaka Crime Index API is alive!", "endpoints": ["/health", "/indexes"]}

@app.get("/health")
async def health():
    db_status = "unknown"
    count = -1
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM public.area_crime_index"))
            count = result.scalar()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Health check DB failure: {e}")

    return {
        "status": "ok", 
        "service": "index-calculator", 
        "database": db_status,
        "record_count": count,
        "mode": "database-only"
    }

@app.get("/indexes")
async def get_indexes():
    """Return all current crime indexes directly from DB."""
    import traceback
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            # Use a single-line query to avoid PgBouncer/Supabase pooler parsing issues
            sql = "SELECT area, crime_index, event_count_30d, crime_index_30d, crime_index_cumulative, event_count_cumulative, lat, lng, thana, last_updated FROM public.area_crime_index"
            result = await session.execute(text(sql))
            rows = result.mappings().all()
            data = [
                {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in dict(row).items()}
                for row in rows
            ]
        logger.info(f"Retrieved {len(data)} area indexes from DB.")
        return data
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"INDEXES FAILED: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb[-500:]})

@app.get("/indexes/{area}")
async def get_area_index(area: str):
    """Return specific area index directly from DB."""
    data = await get_area_index_from_db(area)
    if not data:
        return JSONResponse(status_code=404, content={"error": "Area not found"})
    return JSONResponse(content=data)

# --- AWS Lambda Entry Points ---

def handler(event, context):
    """Hybrid handler for API Gateway and EventBridge."""
    print(f"DEBUG_START: Event received: {event}")

    # Manually manage event loop to avoid 'no current event loop' in Lambda
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.info("No event loop found in thread, creating new one.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 1. Handle EventBridge Cron
    # Check for direct 'action' key or a nested one if wrapped
    if event.get("action") == "cron" or event.get("detail", {}).get("action") == "cron":
        logger.info("Routing to cron_handler...")
        try:
            # Note: asyncio.run creates its own loop, which is fine for Cron as it's separate from API
            asyncio.run(recalculate_all_indexes())
            return {"statusCode": 200, "body": "Recalculation successful"}
        except Exception as e:
            logger.error(f"Cron execution failed: {e}", exc_info=True)
            return {"statusCode": 500, "body": str(e)}

    # 2. Handle API Gateway HTTP (via Mangum)
    try:
        # Initialize Mangum inside the handler to be loop-safe
        _mangum_handler = Mangum(app, lifespan="off")
        return _mangum_handler(event, context)
    except Exception as e:
        print(f"DEBUG_ERROR: Mangum failed: {e}")
        # Manually return a valid Lambda response if Mangum crashes
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Mangum handler failed", "details": "' + str(e) + '"}'
        }
