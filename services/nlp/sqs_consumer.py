import boto3
import json
import asyncio
import os
import logging
import hashlib
import httpx
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
INDEX_CALCULATOR_URL = os.getenv("INDEX_CALCULATOR_URL", "http://index-calculator:8003")

CRIME_KEYWORDS = [
    "murder", "killed", "arrested", "rape", "robbery", "assault",
    "stabbed", "shot", "detained", "case filed", "accused", "theft",
    "fraud", "scam", "jail", "police", "cid", "rab", "pbi", "crime",
    "stabbing", "shooting", "smuggling", "illegal", "drug", "yaba"
]

processed_hashes = set()

def get_content_hash(title: str, body: str) -> str:
    return hashlib.md5(f"{title}{body[:200]}".encode()).hexdigest()

def is_likely_crime(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CRIME_KEYWORDS)

def extract_body_window(html: str, max_chars: int = 3000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    
    # Prioritize first 3 paragraphs (lede, who/what/where)
    priority = " ".join(p.get_text() for p in paragraphs[:3])
    remaining = " ".join(p.get_text() for p in paragraphs[3:])
    
    full_text = priority + " " + remaining
    return full_text[:max_chars].strip()

async def notify_index_calculator():
    """Fire-and-forget: trigger recalculation after a new event is saved."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{INDEX_CALCULATOR_URL}/recalculate")
            if resp.status_code == 202:
                logger.info("Index recalculation triggered via NLP.")
            else:
                logger.warning(f"Index calculator returned {resp.status_code}")
    except Exception as e:
        logger.warning(f"Could not notify index-calculator: {e}")

async def process_message(msg: dict):
    try:
        data = json.loads(msg["Body"])
        url = data["url"]
        s3_key = data["s3_key"]
        source = data["source"]
        headline = data["headline"]
        published_at = data.get("published_at")

        # 1. Fetch raw content from S3
        def get_s3_data():
            try:
                obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
                return obj["Body"].read().decode("utf-8")
            except s3.exceptions.NoSuchKey:
                logger.warning(f"S3 Key missing: {s3_key}")
                return None

        raw_html = await asyncio.to_thread(get_s3_data)
        if not raw_html:
            return

        # 2. Smart window extraction
        body_text = extract_body_window(raw_html)
        
        # 3. Early Keyword Filter
        if not is_likely_crime(headline + " " + body_text):
            logger.info(f"Skipped non-crime article: {url}")
            return

        # 4. Deduplication
        content_hash = get_content_hash(headline, body_text)
        if content_hash in processed_hashes:
            logger.info(f"Duplicate article, skipping: {url}")
            return
        processed_hashes.add(content_hash)

        # 5. Analyze with Groq
        logger.info(f"Analyzing article: {headline}")
        analysis = await analyze_article(headline, body_text)
        logger.debug(f"DEBUG - Extracted Body Window: {body_text[:200]}...")
        logger.info(f"DEBUG - Groq Analysis for {headline}: {json.dumps(analysis)}")
        
        if not analysis or not analysis.get("is_crime"):
            logger.info(f"Article not crime or analysis failed: {url}")
            return

        # 6. Geocode
        location = analysis.get("location", {})
        area = location.get("area", "")
        thana = location.get("thana", "")
        coords = await geocode_location(area, thana)
        lat, lng = coords if coords else (None, None)

        # 7. Save to DB
        crime_data = {
            "source_url": url,
            "source_name": source,
            "published_at": published_at,
            "headline": headline,
            "body_summary": analysis.get("summary", ""),
            "crime_type": analysis.get("crime_type", ""),
            "severity": analysis.get("severity", 5),
            "location_raw": f"{area}, {thana}",
            "thana": thana,
            "area": area,
            "lat": lat,
            "lng": lng,
            "victim_count": analysis.get("victim_count", 0),
            "s3_key": s3_key
        }
        await save_crime_event(crime_data)
        logger.info(f"Processed and saved: {headline}")

        # 8. Notify Index Calculator
        await notify_index_calculator()

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

async def poll_queue():
    """Continuously poll SQS for new crawl jobs."""
    if not QUEUE_URL:
        logger.error("SQS_CRAWL_QUEUE_URL not set.")
        return

    logger.info(f"NLP service polling SQS: {QUEUE_URL}")
    while True:
        try:
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
