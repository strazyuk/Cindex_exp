from fastapi import FastAPI
from scheduler import start_scheduler, run_crawl
import logging
import uvicorn
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dhaka Crime Crawler Service")
scheduler = None

@app.on_event("startup")
async def startup_event():
    global scheduler
    logger.info("Initializing Crawler Service...")
    scheduler = start_scheduler()
    # Trigger an initial crawl in the background
    import asyncio
    asyncio.create_task(run_crawl())

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler:
        scheduler.shutdown()
    logger.info("Crawler Service shutdown.")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "crawler"}

@app.post("/crawl/trigger")
async def trigger_crawl():
    """Manually trigger a crawl job."""
    from scheduler import run_crawl
    import asyncio
    asyncio.create_task(run_crawl())
    return {"status": "crawl_triggered"}

@app.post("/crawl/backfill")
async def trigger_backfill(days: int = 7):
    """Manually trigger a backfill job."""
    from scheduler import run_backfill
    import asyncio
    asyncio.create_task(run_backfill(days=days))
    return {"status": "backfill_triggered", "days": days}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
