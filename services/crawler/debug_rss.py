import httpx
from bs4 import BeautifulSoup
import asyncio

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DhakaCrimeBot/1.0)"}

async def debug_scrapers():
    print("--- Debugging Daily Star RSS ---")
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Check the URL we used
        url = "https://www.thedailystar.net/crime/rss.xml"
        resp = await client.get(url)
        print(f"Status for {url}: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        soup = BeautifulSoup(resp.text, "xml") # Standard XML parser
        items = soup.find_all("item")
        print(f"Found {len(items)} items in RSS.")
        
        for item in items[:10]:
            title = item.find("title").get_text()
            print(f" - Headline: {title}")
            
        # Check main RSS if crime is empty
        if not items:
            print("\n--- Checking Main RSS ---")
            resp = await client.get("https://www.thedailystar.net/rss.xml")
            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")
            print(f"Items in Main RSS: {len(items)}")
            for item in items[:5]:
                print(f" - {item.find('title').get_text()}")

if __name__ == "__main__":
    asyncio.run(debug_scrapers())
