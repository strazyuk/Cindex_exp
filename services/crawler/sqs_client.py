import boto3
import json
import os

ENDPOINT = os.getenv("AWS_ENDPOINT_URL")
sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "ap-southeast-1"), endpoint_url=ENDPOINT)
QUEUE_URL = os.getenv("SQS_CRAWL_QUEUE_URL")

import asyncio

async def publish_article_job(url: str, storage_ref: str, source: str, headline: str):
    """Push a parsed article job to SQS for the NLP service."""
    message = {
        "url": url,
        "s3_key": storage_ref,  # Labelled s3_key so NLP service remains compatible
        "source": source,
        "headline": headline,
    }
    if not QUEUE_URL:
        print(f"SQS_CRAWL_QUEUE_URL not set. Message not sent: {headline}")
        return
        
    try:
        # Run sync boto3 in thread
        await asyncio.to_thread(
            sqs.send_message,
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
    except Exception as e:
        print(f"SQS publish error: {e}")
