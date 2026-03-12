import asyncio
import logging
from scrapers.daily_star import scrape_daily_star, backfill_daily_star
from scrapers.dhaka_tribune import scrape_dhaka_tribune, backfill_dhaka_tribune
from scrapers.prothom_alo import scrape_prothom_alo, backfill_prothom_alo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scrapers():
    print("\n--- Testing Daily Star ---")
    ds = await scrape_daily_star()
    print(f"Ongoing: {len(ds)} articles")
    
    print("\n--- Testing Dhaka Tribune ---")
    dt = await scrape_dhaka_tribune()
    print(f"Ongoing: {len(dt)} articles")
    
    print("\n--- Testing Prothom Alo ---")
    pa = await scrape_prothom_alo()
    print(f"Ongoing: {len(pa)} articles")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
