import httpx
from typing import Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

async def geocode_location(area: str, thana: str) -> Tuple[float, float] | None:
    """Convert area/thana name to lat/lng using OpenStreetMap Nominatim."""
    query = f"{area}, {thana}, Dhaka, Bangladesh"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "bd"
    }
    headers = {
        "User-Agent": "DhakaCrimeIndex/1.0 (contact: asira@example.com)",
        "Referer": "https://github.com/strazyuk/Cindex_exp"
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"Geocoder Nominatim Error: {resp.status_code} - {resp.text[:100]}")
                return None
                
            results = resp.json()
            if results and isinstance(results, list) and len(results) > 0:
                return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as e:
            print(f"Geocode exception for '{query}': {e}")
    return None
