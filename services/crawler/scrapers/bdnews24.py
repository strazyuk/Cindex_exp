import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DhakaCrimeBot/1.0)"}
CRIME_KEYWORDS = [
    "murder", "killed", "robbery", "assault", "rape", "theft", "arrested", 
    "police", "stabbing", "shooting", "shoutout", "clash", "violence",
    "case", "laundering", "fraud", "scam", "accused", "cid", "rab", "db", "bgb",
    "fled", "detained", "seized", "illegal"
]

async def scrape_bdnews24() -> List[Dict]:
    """Scrape crime-related articles from BDNews24 English crime section."""
    articles = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        try:
            # English Crime Section
            resp = await client.get("https://bdnews24.com/crime")
            soup = BeautifulSoup(resp.text, "lxml")
            
            # BDNews24 usually has headlines in h3 or similar tags
            links = soup.select("h3 a") or soup.select(".media-heading a")
            
            for tag in links[:20]:
                title = tag.get_text(strip=True)
                href = tag.get("href", "")
                url = href if href.startswith("http") else f"https://bdnews24.com{href}"

                if not any(kw in title.lower() for kw in CRIME_KEYWORDS):
                    continue

                try:
                    art_resp = await client.get(url)
                    art_soup = BeautifulSoup(art_resp.text, "lxml")
                    body_div = art_soup.find("div", class_="article-body") or \
                               art_soup.find("div", class_="content") or \
                               art_soup.find("article")
                    
                    body = body_div.get_text(separator=" ", strip=True) if body_div else ""
                    raw_html = art_resp.text
                except Exception as e:
                    logger.error(f"Error fetching BDNews24 article from {url}: {e}")
                    body = ""
                    raw_html = ""

                if body:
                    articles.append({
                        "url": url,
                        "headline": title,
                        "body": body,
                        "published_at": None, # BDNews24 usually requires more parsing for date
                        "source": "BD News 24",
                        "raw_html": raw_html
                    })
        except Exception as e:
            logger.error(f"BDNews24 scraper error: {e}")
            
    return articles
