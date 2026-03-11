import boto3
import hashlib
import os
from datetime import datetime
from pathlib import Path

# Config
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # "s3" or "local"
LOCAL_STORAGE_DIR = Path(__file__).parent / "storage"
ENDPOINT = os.getenv("AWS_ENDPOINT_URL")
BUCKET = "dhaka-crime-raw-html"

# Ensure local storage exists if needed
if STORAGE_MODE == "local":
    LOCAL_STORAGE_DIR.mkdir(exist_ok=True)

s3 = None
if STORAGE_MODE == "s3":
    s3 = boto3.client("s3", endpoint_url=ENDPOINT)

import asyncio

async def save_raw_html(url: str, html: str) -> str:
    """Save raw HTML to either S3 or Local File System."""
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    file_hash = hashlib.md5(url.encode()).hexdigest()
    
    if STORAGE_MODE == "s3":
        key = f"articles/{timestamp}/{file_hash}.html"
        try:
            # Run sync boto3 in thread
            await asyncio.to_thread(
                s3.put_object,
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
    else:
        # Local storage mode
        dir_path = LOCAL_STORAGE_DIR / timestamp
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"{file_hash}.html"
        
        try:
            # Run sync file I/O in thread
            await asyncio.to_thread(file_path.write_text, html, encoding="utf-8")
            return str(file_path.absolute())
        except Exception as e:
            print(f"Local storage error: {e}")
            return ""
