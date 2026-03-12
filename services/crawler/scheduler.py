from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers.daily_star import scrape_daily_star, backfill_daily_star
from scrapers.dhaka_tribune import scrape_dhaka_tribune, backfill_dhaka_tribune
from scrapers.prothom_alo import scrape_prothom_alo, backfill_prothom_alo
from storage_client import save_raw_html
from sqs_client import publish_article_job
import logging
import asyncio
from typing import List, Dict

logger = logging.getLogger(__name__)
seen_urls: set = set()

async def process_articles(all_articles: List[Dict]):
    """Process a list of articles: save and publish."""
    logger.info(f"Processing {len(all_articles)} articles...")
    count = 0
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
                    headline=article.get("headline", "No Headline")
                )
                seen_urls.add(url)
                count += 1
                if count % 10 == 0:
                    logger.info(f"Processed {count} articles...")
                
        except Exception as e:
            logger.error(f"Error processing article {article.get('url', 'unknown')}: {e}")
    logger.info(f"Finished processing. Added {count} new articles.")

async def run_crawl():
    """Main crawl orchestration for ongoing news."""
    logger.info("Starting ongoing crawl job...")
    
    results = await asyncio.gather(
        scrape_daily_star(),
        # scrape_dhaka_tribune(),
        # scrape_prothom_alo(),
        return_exceptions=True
    )
    
    all_articles = []
    for res in results:
        if isinstance(res, list):
            all_articles.extend(res)
        else:
            logger.error(f"Scraper task failed: {res}")
    
    await process_articles(all_articles)

async def run_backfill(days: int = 60):
    """Deep crawl for historical data."""
    logger.info(f"Starting {days}-day backfill job...")
    
    results = await asyncio.gather(
        backfill_daily_star(days),
        # backfill_dhaka_tribune(days),
        # backfill_prothom_alo(days),
        return_exceptions=True
    )
    
    all_articles = []
    for res in results:
        if isinstance(res, list):
            all_articles.extend(res)
        else:
            logger.error(f"Backfill task failed: {res}")
            
    await process_articles(all_articles)

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Ongoing crawl every 24 hours (as per existing 1440 minutes setting)
    scheduler.add_job(run_crawl, "interval", minutes=1440, id="crawl_job")
    
    # We could trigger backfill here once on startup if needed
    # scheduler.add_job(run_backfill, args=[60], id="backfill_job")
    
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler
