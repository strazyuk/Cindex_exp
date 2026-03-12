import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from formula import compute_crime_index
from db import get_all_events_by_area, upsert_area_index
from redis_client import cache_area_index, get_all_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crime Index Calculator")

# Global state
_active_state = {
    "last_run_at": None,
    "next_run_at": None,
    "is_running": False
}
scheduler: AsyncIOScheduler | None = None

async def recalculate_all_indexes():
    """Recalculate dual crime indexes (30d and cumulative) and update DB/Cache."""
    if _active_state["is_running"]:
        logger.warning("Recalculation already in progress, skipping.")
        return
    
    _active_state["is_running"] = True
    _active_state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    
    logger.info("Recalculating crime indexes (Robust Combined Table)...")
    try:
        # 1. Sync the combined source of truth table
        from db import repopulate_combined_table
        await repopulate_combined_table()

        # 2. Fetch fresh events split into live-only and all
        all_area_events = await get_all_events_by_area()
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        for area, event_sets in all_area_events.items():
            live_events = event_sets.get("live", [])
            all_events  = event_sets.get("all", [])

            # 1. 30-day: only live events within the last 30 days
            recent_events = [
                e for e in live_events
                if e.get("published_at") and 
                   (e["published_at"] if e["published_at"].tzinfo else 
                    e["published_at"].replace(tzinfo=timezone.utc)) >= thirty_days_ago
            ]

            # 2. Cumulative: live events + all historical dataset rows
            idx_30d = compute_crime_index(recent_events)
            idx_cum = compute_crime_index(all_events)

            # 3. Extract coordinates — prefer live events, fall back to dataset rows
            lat   = next((e["lat"]   for e in all_events if e.get("lat")),   None)
            lng   = next((e["lng"]   for e in all_events if e.get("lng")),   None)
            thana = next((e["thana"] for e in live_events if e.get("thana")), None) or \
                    next((e["thana"] for e in all_events  if e.get("thana")), None)

            # 4. Persistence
            # Use .title() for the database key to match existing mixed-case records
            display_area = area.title()

            await upsert_area_index(
                display_area,
                idx_30d, len(recent_events),
                idx_cum, len(all_events),
                lat, lng, thana
            )
            await cache_area_index(
                display_area,
                idx_30d, len(recent_events),
                idx_cum, len(all_events),
                lat, lng
            )

            logger.info(
                f"Area '{display_area}': 30d={idx_30d} ({len(recent_events)} live evts), "
                f"Cum={idx_cum} ({len(all_events)} total evts, incl. historical)"
            )
            
    except Exception as e:
        logger.error(f"Error in recalculate_all_indexes: {e}", exc_info=True)
    finally:
        _active_state["is_running"] = False

@app.on_event("startup")
async def startup():
    global scheduler
    interval = int(os.getenv("RECALCULATE_INTERVAL_MINUTES", 15))
    scheduler = AsyncIOScheduler()
    job = scheduler.add_job(recalculate_all_indexes, "interval", minutes=interval, id="recalculate")
    scheduler.start()
    
    # Run once immediately on start
    asyncio.create_task(recalculate_all_indexes())

@app.on_event("shutdown")
async def shutdown():
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "index-calculator"}

@app.post("/recalculate", status_code=202)
async def trigger_recalculate(background_tasks: BackgroundTasks):
    """Manually trigger an immediate recalculation."""
    background_tasks.add_task(recalculate_all_indexes)
    return {"status": "recalculate_triggered"}

@app.get("/scheduler/status")
async def scheduler_status():
    """Return the current status of the aggregation scheduler."""
    job = scheduler.get_job("recalculate") if scheduler else None
    return {
        "last_run_at": _active_state["last_run_at"],
        "next_run_at": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "is_running": _active_state["is_running"],
        "interval_minutes": int(os.getenv("RECALCULATE_INTERVAL_MINUTES", 15)),
        "scheduler_running": scheduler.running if scheduler else False
    }

@app.get("/indexes")
async def get_indexes():
    """Return all current crime indexes (served to frontend)."""
    data = await get_all_indexes()
    return JSONResponse(content=data)

@app.get("/indexes/{area}")
async def get_area_index(area: str):
    from redis_client import get_redis
    r = await get_redis()
    val = await r.get(f"index:{area}")
    if not val:
        return JSONResponse(status_code=404, content={"error": "Area not found"})
    import json
    return JSONResponse(content=json.loads(val))
