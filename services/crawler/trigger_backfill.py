import httpx
import asyncio
import sys

async def trigger_backfill(days):
    async with httpx.AsyncClient() as client:
        try:
            url = f"http://localhost:8001/crawl/backfill?days={days}"
            print(f"Triggering backfill for {days} days at {url}")
            resp = await client.post(url, timeout=30)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    asyncio.run(trigger_backfill(days))
