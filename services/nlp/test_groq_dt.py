import asyncio
import os
import json
import sys
from groq_analyzer import analyze_article

async def test_single(url, headline, body):
    print(f"Testing URL: {url}")
    print(f"Headline: {headline}")
    result = await analyze_article(headline, body)
    print("Groq Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    # Article from Dhaka Tribune: https://www.dhakatribune.com/bangladesh/dhaka/405102/four-arrested-for-robbing-passengers-on-highway
    headline = "Four arrested for robbing passengers on highway"
    body = "Rab-10 arrested four people from Dhaka's Savar for their alleged involvement in robbing passengers on the highway. Savar is a thana in Greater Dhaka."
    asyncio.run(test_single("https://www.dhakatribune.com/bangladesh/dhaka/405102/four-arrested-for-robbing-passengers-on-highway", headline, body))
