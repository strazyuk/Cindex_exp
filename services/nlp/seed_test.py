import boto3
import json
import os
import hashlib
from datetime import datetime

# LocalStack config
SQS_URL = "http://localhost:4566/000000000000/dhaka-crime-crawl-queue"
BUCKET = "dhaka-crime-raw-html"
AWS_CONFIG = {
    "endpoint_url": "http://localhost:4566",
    "region_name": "ap-southeast-1",
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test"
}

def seed_data():
    s3 = boto3.client("s3", **AWS_CONFIG)
    sqs = boto3.client("sqs", **AWS_CONFIG)

    url = "https://www.thedailystar.net/mock-crime-1"
    headline = "Man stabbed to death in Mirpur over land dispute"
    body = "A 40-year-old man was killed on Tuesday night when a group of attackers stabbed him in Mirpur's Pallabi area. Police said the incident occurred due to a long-standing land dispute."
    html = f"<html><body><h1>{headline}</h1><p>{body}</p></body></html>"
    
    file_hash = hashlib.md5(url.encode()).hexdigest()
    s3_key = f"articles/mock/{file_hash}.html"
    
    # Upload to S3
    print(f"Uploading mock article to S3: {s3_key}")
    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=html.encode())
    
    # Send to SQS
    message = {
        "url": url,
        "s3_key": s3_key,
        "source": "Mock Daily Star",
        "headline": headline
    }
    print(f"Sending message to SQS: {headline}")
    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(message))
    print("Seeding complete!")

if __name__ == "__main__":
    seed_data()
