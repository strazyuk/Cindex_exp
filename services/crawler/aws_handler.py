import asyncio
import logging
from scheduler import run_crawl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    AWS Lambda handler for the Crawler service.
    Triggered by an EventBridge cron rule (e.g., every 1 hour).
    """
    logger.info(f"Crawler Lambda triggered. Event: {event}")
    try:
        # run_crawl() handles scraping Daily Star, parsing, and pushing to SQS/S3.
        asyncio.run(run_crawl())
        return {
            "statusCode": 200,
            "body": "Crawl completed successfully."
        }
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        return {
            "statusCode": 500,
            "body": f"Crawl failed: {str(e)}"
        }
