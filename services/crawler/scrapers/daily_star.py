import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from config import BANGLADESH_ENGLISH_NEWS_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
CRIME_KEYWORDS = [
    "murder", "killed", "robbery", "assault", "rape", "theft", "arrested", 
    "police", "stabbing", "shooting", "shoutout", "clash", "violence",
    "case", "laundering", "fraud", "scam", "accused", "cid", "rab", "db", "bgb",
    "fled", "detained", "seized", "illegal"
]
SELECTORS = BANGLADESH_ENGLISH_NEWS_SOURCES["selectors"]["The Daily Star"]

async def fetch_article_body(client: httpx.AsyncClient, url: str) -> Optional[Dict]:
    """Fetch and parse the article body from The Daily Star."""
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
        
        if body_div:
            return {
                "body": body_div.get_text(separator=" ", strip=True),
                "raw_html": resp.text
            }
    except Exception as e:
        logger.error(f"Error fetching article body from {url}: {e}")
    return None

async def scrape_daily_star() -> List[Dict]:
    """Scrape recent crime articles from The Daily Star via RSS."""
    articles = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        try:
            url = BANGLADESH_ENGLISH_NEWS_SOURCES["crime_sections"]["The Daily Star"]
            resp = await client.get(url)
            logger.info(f"Daily Star RSS fetch: {resp.status_code}, URL: {resp.url}")
            
            if resp.status_code != 200:
                resp = await client.get("https://www.thedailystar.net/rss.xml")
                logger.info(f"Daily Star Main RSS fetch: {resp.status_code}")

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("item")
            logger.info(f"Daily Star found {len(items)} items in RSS.")

            for item in items[:40]: 
                title_node = item.find("title")
                if not title_node: continue
                title = title_node.get_text(separator=" ", strip=True)
                
                link_node = item.find("link")
                if not link_node: continue
                link = link_node.get_text(strip=True)
                if link.startswith("/"):
                    link = "https://www.thedailystar.net" + link
                    
                pub_date = item.find("pubDate")
                title_lower = title.lower()
                
                # Check keywords
                is_potential_crime = any(kw in title_lower for kw in CRIME_KEYWORDS)
                is_dhaka = any(loc in title_lower for loc in ["dhaka", "mirpur", "gulshan", "banani", "uttara", "motijheel", "dhanmondi"])

                if not is_potential_crime and not is_dhaka:
                    continue

                result = await fetch_article_body(client, link)
                if result:
                    articles.append({
                        "url": link,
                        "headline": title,
                        "body": result["body"],
                        "published_at": pub_date.get_text(strip=True) if pub_date else None,
                        "source": "The Daily Star",
                        "raw_html": result["raw_html"]
                    })
        except Exception as e:
            logger.error(f"Daily Star scraper error: {e}")
            
    return articles

async def backfill_daily_star(days: int = 60) -> List[Dict]:
    """Backfill articles from The Daily Star by paginating the crime-justice section."""
    articles = []
    # Note: The Daily Star crime-justice section pagination
    base_url = "https://www.thedailystar.net/news/bangladesh/crime-justice"
    
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        page = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        still_within_range = True
        
        while still_within_range and page < 10: # Safety limit for pages
            url = f"{base_url}?page={page}"
            logger.info(f"Scraping Daily Star historical page: {url}")
            
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    break
                
                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for article links in the listing
                links = soup.select("h3 a") or soup.select("h4 a")
                if not links:
                    break
                
                page_articles_found = 0
                for link in links:
                    href = link['href']
                    if href.startswith("/"):
                        href = "https://www.thedailystar.net" + href
                    
                    # We might need to check the date on the listing or fetch article to see date
                    result = await fetch_article_body(client, href)
                    if result:
                        # Extract date from meta or body if possible, otherwise assume page sequence
                        # For now, we collect and let the pipeline filter by date if needed
                        articles.append({
                            "url": href,
                            "headline": link.get_text(strip=True),
                            "body": result["body"],
                            "source": "The Daily Star",
                            "raw_html": result["raw_html"],
                            "published_at": None # To be refined if we find date in HTML
                        })
                        page_articles_found += 1
                
                if page_articles_found == 0:
                    still_within_range = False
                    
            except Exception as e:
                logger.error(f"Error backfilling Daily Star page {page}: {e}")
                break
                
            page += 1
            await asyncio.sleep(1)
            
    return articles
