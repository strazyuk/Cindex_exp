import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
CRIME_KEYWORDS = [
    "murder", "killed", "robbery", "assault", "rape", "theft", "arrested", 
    "police", "stabbing", "shooting", "shoutout", "clash", "violence",
    "case", "laundering", "fraud", "scam", "accused", "cid", "rab", "db", "bgb",
    "fled", "detained", "seized", "illegal"
]

async def scrape_daily_star() -> List[Dict]:
    """Scrape crime-related articles from The Daily Star English version."""
    articles = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get("https://www.thedailystar.net/crime/rss.xml")
            logger.info(f"Daily Star RSS fetch: {resp.status_code}, URL: {resp.url}")
            
            if resp.status_code != 200:
                resp = await client.get("https://www.thedailystar.net/rss.xml")
                logger.info(f"Daily Star Main RSS fetch: {resp.status_code}")

            soup = BeautifulSoup(resp.text, "xml")
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
                    logger.debug(f"Skipping article (no match): {title[:50]}")
                    continue

                logger.info(f"Processing candidate: {title[:50]}")
                try:
                    art_resp = await client.get(link)
                    art_soup = BeautifulSoup(art_resp.text, "html.parser")
                    body_div = art_soup.find("div", class_="field-items") or \
                               art_soup.find("div", class_="node-content") or \
                               art_soup.find("article") or \
                               art_soup.find("div", class_="pb-20")
                    
                    body = body_div.get_text(separator=" ", strip=True) if body_div else ""
                    raw_html = art_resp.text
                except Exception as e:
                    logger.error(f"Error fetching article body from {link}: {e}")
                    body = ""
                    raw_html = ""

                if body:
                    articles.append({
                        "url": link,
                        "headline": title,
                        "body": body,
                        "published_at": pub_date.get_text(strip=True) if pub_date else None,
                        "source": "The Daily Star",
                        "raw_html": raw_html
                    })
                    logger.info(f"Successfully scraped: {title[:50]}")
        except Exception as e:
            logger.error(f"Daily Star scraper error: {e}")
            
    return articles
