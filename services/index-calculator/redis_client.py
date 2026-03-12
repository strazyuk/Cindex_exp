import redis.asyncio as redis
import json
import os

REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "redis://redis:6379")

# Hardcoded coordinate fallback for well-known Dhaka areas
# Used when NLP geocoding hasn't populated lat/lng yet
DHAKA_COORDS: dict = {
    "Dhaka": (23.8103, 90.4125),
    "Mirpur": (23.8223, 90.3654),
    "Dhanmondi": (23.7461, 90.3742),
    "Gulshan": (23.7925, 90.4078),
    "Gulshan-2": (23.7957, 90.4150),
    "Mohammadpur": (23.7616, 90.3589),
    "Shahbagh": (23.7389, 90.3964),
    "Pallabi": (23.8337, 90.3614),
    "Uttara": (23.8759, 90.3795),
    "Tejgaon": (23.7654, 90.3956),
    "Shyampur": (23.7091, 90.4273),
    "Jatrabari": (23.7184, 90.4340),
    "Kamalapur": (23.7261, 90.4183),
    "Motijheel": (23.7327, 90.4180),
    "Paltan": (23.7353, 90.4133),
    "Gulistan": (23.7244, 90.4135),
    "Chankharpul": (23.7166, 90.4076),
    "Sayedabad": (23.7080, 90.4259),
    "Old Dhaka": (23.7104, 90.4074),
    "Dhaka University": (23.7282, 90.3938),
    "Tejgaon Industrial Area": (23.7710, 90.3935),
    "Rampura": (23.7561, 90.4284),
    "Khilgaon": (23.7444, 90.4284),
    "Badda": (23.7831, 90.4284),
    "Banani": (23.7937, 90.4022),
    "Baridhara": (23.8043, 90.4264),
}

async def get_redis():
    return await redis.from_url(REDIS_URL, decode_responses=True)

async def cache_area_index(
    area: str, 
    idx_30d: float, 
    count_30d: int, 
    idx_cum: float, 
    count_cum: int, 
    lat: float, 
    lng: float
):
    """Cache both 30-day and cumulative indices in Redis."""
    r = await get_redis()
    # Apply coordinate fallback if geocoding returned null
    if not lat or not lng:
        fallback = DHAKA_COORDS.get(area)
        if fallback:
            lat, lng = fallback

    data = {
        "area": area,
        "crime_index": idx_30d,             # legacy/default field for map
        "crime_index_30d": idx_30d,
        "crime_index_cumulative": idx_cum,
        "event_count_30d": count_30d,
        "event_count_cumulative": count_cum,
        "lat": lat,
        "lng": lng,
        "last_updated": ""
    }
    await r.set(f"index:{area}", json.dumps(data), ex=3600)  # 1hr TTL
    await r.publish("index_updates", json.dumps(data))

async def get_all_indexes() -> list:
    r = await get_redis()
    keys = await r.keys("index:*")
    results = []
    for key in keys:
        val = await r.get(key)
        if val:
            results.append(json.loads(val))
    return results
