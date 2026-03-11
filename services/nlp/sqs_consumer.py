import boto3
import json
import asyncio
import os
import logging
from groq_analyzer import analyze_article
from geocoder import geocode_location
from db import save_crime_event
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# boto3 clients with LocalStack support
ENDPOINT = os.getenv("AWS_ENDPOINT_URL")
sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "ap-southeast-1"), endpoint_url=ENDPOINT)
s3 = boto3.client("s3", endpoint_url=ENDPOINT)

QUEUE_URL = os.getenv("SQS_CRAWL_QUEUE_URL")
BUCKET = "dhaka-crime-raw-html"

async def process_message(msg: dict):
    try:
        body = json.loads(msg["Body"])
        url = body["url"]
        s3_key = body["s3_key"]
        source = body["source"]
        headline = body["headline"]

        # Fetch raw HTML from    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch raw content from S3
            def get_s3_data():
                try:
                    obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
                    return obj["Body"].read().decode("utf-8")
                except s3.exceptions.NoSuchKey:
                    logger.warning(f"S3 Key missing: {s3_key}. Might be from an old run.")
                    return None

            raw_html = await asyncio.to_thread(get_s3_data)
            if not raw_html:
                logger.warning(f"Skipping processing for {url} due to missing S3 content.")
                return

            # Strip HTML tags
            soup = BeautifulSoup(raw_html, "html.parser")
            body_text = soup.get_text(separator=" ", strip=True)

            # Analyze with Groq
            analysis = await analyze_article(headline, body_text)
            if not analysis or not analysis.get("is_crime"):
                logger.info(f"Article not crime or analysis failed: {url}")
                return

            # Geocode
            coords = await geocode_location(analysis.get("area", ""), analysis.get("thana", ""))
            lat, lng = coords if coords else (None, None)

            # Save to DB
            crime_data = {
                "source_url": url,
                "source_name": source,
                "published_at": None, # Should extract from original RSS if possible
                "headline": headline,
                "body_summary": analysis.get("summary", ""),
                "crime_type": analysis.get("crime_type", ""),
                "severity": analysis.get("severity", 5),
                "location_raw": analysis.get("location_raw", ""),
                "thana": analysis.get("thana", ""),
                "area": analysis.get("area", ""),
                "lat": lat,
                "lng": lng,
                "victim_count": analysis.get("victim_count", 0),
                "s3_key": s3_key
            }
            await save_crime_event(crime_data)
            logger.info(f"Processed and saved: {headline}")

        except Exception as e:
            logger.error(f"Error processing message {url}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error parsing message body or general processing error: {e}")

async def poll_queue():
    """Continuously poll SQS for new crawl jobs."""
    if not QUEUE_URL:
        logger.error("SQS_CRAWL_QUEUE_URL not set. Consumer idle.")
        return

    logger.info(f"NLP service polling SQS: {QUEUE_URL}")
    while True:
        try:
            # Run sync boto3 in thread
            response = await asyncio.to_thread(
                sqs.receive_message,
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=10
            )
            messages = response.get("Messages", [])
            for msg in messages:
                await process_message(msg)
                await asyncio.to_thread(
                    sqs.delete_message,
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        except Exception as e:
            logger.error(f"SQS poll error: {e}")
            await asyncio.sleep(5)
