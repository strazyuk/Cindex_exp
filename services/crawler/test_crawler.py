import asyncio
import os
from scrapers.daily_star import scrape_daily_star
from dotenv import load_dotenv

load_dotenv()

async def test_scraper():
    print("Testing Daily Star Scraper (English)...")
    articles = await scrape_daily_star()
    print(f"Found {len(articles)} articles.")
    
    for i, art in enumerate(articles[:3]):
        print(f"\n--- Article {i+1} ---")
        print(f"Headline: {art['headline']}")
        print(f"URL: {art['url']}")
        print(f"Body snippet: {art['body'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_scraper())
