import asyncio
import logging
import sys
from fastapi import FastAPI

# Force logging to stdout immediately
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.info("NLP Service entry point reached")

from sqs_consumer import poll_queue
app = FastAPI(title="NLP Analysis Service")

@app.on_event("startup")
async def startup():
    # Start the SQS consumer in the background
    asyncio.create_task(poll_queue())

@app.get("/health")
async def health():
    return {"status": "ok", "service": "nlp"}
