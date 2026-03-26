import asyncio
import logging
from sqs_consumer import process_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    AWS Lambda handler for the NLP service.
    Triggered natively by Amazon SQS. AWS handles polling and deleting messages automatically.
    """
    records = event.get('Records', [])
    logger.info(f"NLP Lambda triggered directly by SQS with {len(records)} records.")
    
    tasks = []
    for record in records:
        # AWS Lambda SQS event returns the payload in a lowercase "body" key.
        # Our existing process_message expects an uppercase "Body" key from boto3.
        msg = {"Body": record.get("body")}
        tasks.append(process_message(msg))
    
    if tasks:
        # Run all asyncio tasks for processing the messages
        asyncio.run(asyncio.gather(*tasks))
    
    return {"statusCode": 200, "body": f"Successfully processed {len(records)} messages."}
