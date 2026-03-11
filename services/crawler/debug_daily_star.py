import httpx
from bs4 import BeautifulSoup
import asyncio

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
CRIME_KEYWORDS = [
    "murder", "killed", "robbery", "assault", "rape", "theft", "arrested", 
    "police", "stabbing", "shooting", "shoutout", "clash", "violence",
    "case", "laundering", "fraud", "scam", "accused", "cid", "rab", "db", "bgb",
    "fled", "detained", "seized", "illegal"
]

async def test_daily_star():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        url = "https://www.thedailystar.net/crime/rss.xml"
        print(f"Fetching: {url}")
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Final URL: {resp.url}")
        
        # Use html.parser for less dependencies
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("item")
        print(f"Found {len(items)} items.")
        
        for item in items[:10]:
            title_node = item.find("title")
            title = title_node.get_text(separator=" ", strip=True) if title_node else "NO TITLE"
            
            link_node = item.find("link")
            link = link_node.get_text(strip=True) if link_node else "NO LINK"
            
            is_potential_crime = any(kw in title.lower() for kw in CRIME_KEYWORDS)
            print(f" - Title: {title[:50]}... | Match: {is_potential_crime}")

if __name__ == "__main__":
    asyncio.run(test_daily_star())
