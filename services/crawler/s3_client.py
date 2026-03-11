import boto3
import hashlib
import os
from datetime import datetime

ENDPOINT = os.getenv("AWS_ENDPOINT_URL")  # Set for LocalStack, None for real AWS
s3 = boto3.client("s3", endpoint_url=ENDPOINT)
BUCKET = "dhaka-crime-raw-html"

def upload_raw_html(url: str, html: str) -> str:
    """Upload raw HTML to S3, return the S3 key."""
    # Key format: articles/YYYY/MM/DD/hash.html
    key = f"articles/{datetime.utcnow().strftime('%Y/%m/%d')}/{hashlib.md5(url.encode()).hexdigest()}.html"
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=html.encode("utf-8"),
            ContentType="text/html",
            Metadata={"source_url": url}
        )
        return key
    except Exception as e:
        print(f"S3 upload error: {e}")
        return ""
