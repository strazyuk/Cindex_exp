from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers.daily_star import scrape_daily_star
# from scrapers.bdnews24 import scrape_bdnews24
from storage_client import save_raw_html
from sqs_client import publish_article_job
import logging
import asyncio

logger = logging.getLogger(__name__)
seen_urls: set = set()

async def run_crawl():
    """Main crawl orchestration."""
    logger.info("Starting crawl job...")
    
    # Run scrapers
    results = await asyncio.gather(
        scrape_daily_star(),
        # scrape_bdnews24(),
    )
    
    all_articles = [art for sublist in results for art in sublist]
    
    logger.info(f"Found {len(all_articles)} articles in total.")
    
    for article in all_articles:
        try:
            url = article["url"]
            if url in seen_urls:
                continue
            
            # Save raw HTML (S3 or Local)
            storage_ref = await save_raw_html(url, article.get("raw_html", ""))
            
            if storage_ref:
                # Push to SQS
                await publish_article_job(
                    url=url,
                    storage_ref=storage_ref,
                    source=article["source"],
                    headline=article["headline"]
                )
                seen_urls.add(url)
                logger.info(f"Published job: {article['headline'][:50]}...")
                
        except Exception as e:
            logger.error(f"Error in scraper loop for {article.get('url', 'unknown')}: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run every 30 minutes
    scheduler.add_job(run_crawl, "interval", minutes=1440, id="crawl_job")
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler
