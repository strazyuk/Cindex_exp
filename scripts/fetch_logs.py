"""Write full Lambda logs to a file for inspection."""
import boto3

client = boto3.client('logs', region_name='us-east-1')

streams = client.describe_log_streams(
    logGroupName='/aws/lambda/dhaka-crime-index-calculator',
    orderBy='LastEventTime',
    descending=True,
    limit=1
)
stream_name = streams['logStreams'][0]['logStreamName']

events = client.get_log_events(
    logGroupName='/aws/lambda/dhaka-crime-index-calculator',
    logStreamName=stream_name,
    limit=100,
    startFromHead=True
)

with open('lambda_logs.txt', 'w') as f:
    for event in events['events']:
        f.write(event['message'])
        f.write('\n')

print(f"Wrote {len(events['events'])} log events to lambda_logs.txt")
