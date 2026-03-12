import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from config import BANGLADESH_ENGLISH_NEWS_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SELECTORS = BANGLADESH_ENGLISH_NEWS_SOURCES["selectors"]["Dhaka Tribune"]

async def fetch_article_body(client: httpx.AsyncClient, url: str) -> Optional[Dict]:
    """Fetch and parse the article body from Dhaka Tribune."""
    try:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        body_div = None
        for selector in SELECTORS["body"]:
            body_div = soup.select_one(selector)
            if body_div:
                break
        
        headline = ""
        h1 = soup.find("h1")
        if h1:
            headline = h1.get_text(strip=True)
            
        if body_div:
            return {
                "body": body_div.get_text(separator=" ", strip=True),
                "headline": headline,
                "raw_html": resp.text
            }
    except Exception as e:
        logger.error(f"Error fetching article body from {url}: {e}")
    return None

async def scrape_dhaka_tribune() -> List[Dict]:
    """Scrape recent crime articles from Dhaka Tribune crime section."""
    articles = []
    url = BANGLADESH_ENGLISH_NEWS_SOURCES["crime_sections"]["Dhaka Tribune"]
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch Dhaka Tribune crime section: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, "html.parser")
            # Dhaka Tribune crime section articles are usually within a list or grid
            # Let's target links that look like articles
            links = soup.find_all("a", href=True)
            article_urls = set()
            for link in links:
                href = link['href']
                if "/bangladesh/" in href and any(char.isdigit() for char in href):
                    if href.startswith("/"):
                        href = "https://www.dhakatribune.com" + href
                    article_urls.add(href)
            
            logger.info(f"Found {len(article_urls)} potential articles in Dhaka Tribune crime section.")
            
            for art_url in list(article_urls)[:20]: # Limit for ongoing scrape
                result = await fetch_article_body(client, art_url)
                if result:
                    articles.append({
                        "url": art_url,
                        "source": "Dhaka Tribune",
                        "body": result["body"],
                        "headline": result["headline"],
                        "raw_html": result["raw_html"],
                        "published_at": datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Dhaka Tribune scraper error: {e}")
            
    return articles

async def backfill_dhaka_tribune(days: int = 60) -> List[Dict]:
    """Backfill articles from Dhaka Tribune using monthly sitemaps."""
    articles = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Collect unique months
    months = set()
    curr = start_date
    while curr <= end_date:
        months.add(curr.strftime("%Y-%m"))
        curr += timedelta(days=20)
    months.add(end_date.strftime("%Y-%m"))
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for month_str in sorted(list(months)):
            sitemap_url = f"https://www.dhakatribune.com/{month_str}-01.xml"
            logger.info(f"Checking Dhaka Tribune sitemap: {sitemap_url}")
            
            try:
                resp = await client.get(sitemap_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    urls = [loc.text for loc in soup.find_all("loc")]
                    
                    # Filter for bangladesh articles
                    crime_urls = [u for u in urls if "/bangladesh/" in u]
                    logger.info(f"Found {len(crime_urls)} articles for {month_str}")
                    
                    for u in crime_urls:
                        result = await fetch_article_body(client, u)
                        if result:
                            articles.append({
                                "url": u,
                                "source": "Dhaka Tribune",
                                "body": result["body"],
                                "headline": result["headline"],
                                "raw_html": result["raw_html"],
                                "published_at": f"{month_str}-01T00:00:00Z"
                            })
                else:
                    logger.warning(f"Sitemap not found for {month_str}: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error processing sitemap {sitemap_url}: {e}")
            
            await asyncio.sleep(0.5)
            
    return articles
