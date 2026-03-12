import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from config import BANGLADESH_ENGLISH_NEWS_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SELECTORS = BANGLADESH_ENGLISH_NEWS_SOURCES["selectors"]["Prothom Alo"]

async def fetch_article_body(client: httpx.AsyncClient, url: str) -> Optional[Dict]:
    """Fetch and parse the article body from Prothom Alo."""
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

async def scrape_prothom_alo() -> List[Dict]:
    """Scrape recent crime articles from Prothom Alo crime section."""
    articles = []
    url = BANGLADESH_ENGLISH_NEWS_SOURCES["crime_sections"]["Prothom Alo"]
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch Prothom Alo crime section: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, "html.parser")
            # Prothom Alo usually has articles in a specific container
            links = soup.find_all("a", href=True)
            article_urls = set()
            for link in links:
                href = link['href']
                # More robust link matching
                if "/bangladesh/" in href and any(char.isdigit() for char in href):
                    if href.startswith("/"):
                        href = "https://en.prothomalo.com" + href
                    article_urls.add(href)
            
            logger.info(f"Found {len(article_urls)} potential articles in Prothom Alo crime section.")
            
            for art_url in list(article_urls)[:15]:
                result = await fetch_article_body(client, art_url)
                if result:
                    articles.append({
                        "url": art_url,
                        "source": "Prothom Alo",
                        "body": result["body"],
                        "headline": result["headline"],
                        "raw_html": result["raw_html"],
                        "published_at": datetime.now().isoformat()
                    })
        except Exception as e:
            logger.error(f"Prothom Alo scraper error: {e}")
            
    return articles

async def backfill_prothom_alo(days: int = 60) -> List[Dict]:
    """Backfill articles from Prothom Alo using daily sitemaps."""
    articles = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            sitemap_url = f"https://en.prothomalo.com/sitemap/sitemap-daily-{date_str}.xml"
            
            try:
                resp = await client.get(sitemap_url)
                if resp.status_code == 200:
                    logger.info(f"Processing Prothom Alo sitemap: {sitemap_url}")
                    soup = BeautifulSoup(resp.text, "html.parser")
                    urls = [loc.text for loc in soup.find_all("loc")]
                    
                    # Filter for bangladesh articles
                    crime_urls = [u for u in urls if "/bangladesh/" in u]
                    logger.info(f"Found {len(crime_urls)} articles for {date_str}")
                    
                    for u in crime_urls:
                        result = await fetch_article_body(client, u)
                        if result:
                            articles.append({
                                "url": u,
                                "source": "Prothom Alo",
                                "body": result["body"],
                                "headline": result["headline"],
                                "raw_html": result["raw_html"],
                                "published_at": f"{date_str}T00:00:00Z"
                            })
                elif resp.status_code == 404:
                    logger.debug(f"Sitemap not yet available for {date_str}")
                else:
                    logger.warning(f"Sitemap fetch failed for {date_str}: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error processing sitemap {sitemap_url}: {e}")
            
            current_date += timedelta(days=1)
            await asyncio.sleep(0.5)
            
    return articles
