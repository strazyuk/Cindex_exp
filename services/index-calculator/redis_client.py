import redis.asyncio as redis
import json
import os

REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "redis://redis:6379")

async def get_redis():
    return await redis.from_url(REDIS_URL, decode_responses=True)

async def cache_area_index(area: str, index_value: float, event_count: int, lat: float, lng: float):
    r = await get_redis()
    data = {
        "area": area, 
        "index": index_value, 
        "event_count": event_count,
        "lat": lat,
        "lng": lng,
        "updated_at": str(os.getenv("TIMESTAMP", "")) # for debugging
    }
    await r.set(f"index:{area}", json.dumps(data), ex=3600)  # 1hr TTL
    await r.publish("index_updates", json.dumps(data))  # for future real-time features

async def get_all_indexes() -> list:
    r = await get_redis()
    keys = await r.keys("index:*")
    results = []
    for key in keys:
        val = await r.get(key)
        if val:
            results.append(json.loads(val))
    return results
