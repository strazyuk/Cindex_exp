import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from formula import compute_crime_index
from db import get_recent_events_by_area, upsert_area_index
from redis_client import cache_area_index, get_all_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crime Index Calculator")

async def recalculate_all_indexes():
    logger.info("Recalculating crime indexes...")
    try:
        area_events = await get_recent_events_by_area()

        for area, events in area_events.items():
            index = compute_crime_index(events)
            
            # Extract coords and thana if available
            lat = next((e["lat"] for e in events if e.get("lat")), None)
            lng = next((e["lng"] for e in events if e.get("lng")), None)
            thana = next((e["thana"] for e in events if e.get("thana")), None)
            
            await upsert_area_index(area, index, len(events), lat, lng, thana)
            await cache_area_index(area, index, len(events), lat, lng)
            logger.info(f"Area '{area}': index={index}, events={len(events)}")
            
    except Exception as e:
        logger.error(f"Error in recalculate_all_indexes: {e}")

@app.on_event("startup")
async def startup():
    scheduler = AsyncIOScheduler()
    # Recalculate every 15 minutes
    scheduler.add_job(recalculate_all_indexes, "interval", minutes=15)
    scheduler.start()
    # Run once immediately on start
    asyncio.create_task(recalculate_all_indexes())

@app.get("/health")
async def health():
    return {"status": "ok", "service": "index-calculator"}

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
