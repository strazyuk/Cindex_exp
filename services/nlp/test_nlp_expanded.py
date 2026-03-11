import asyncio
import os
import json
from groq_analyzer import analyze_article
from dotenv import load_dotenv

load_dotenv()

async def run_test(title, headline, body):
    print(f"\n>>> Testing: {title}")
    result = await analyze_article(headline, body)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("FAILED: No result")

async def main():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found.")
        return

    # Case 1: Clear Crime in Dhaka
    await run_test("Crime in Dhaka (Mirpur)", 
                  "Police arrest 3 over robbery in Mirpur", 
                  "Dhaka Metropolitan Police (DMP) arrested three individuals in connection with a daring daylight robbery in Mirpur Section 10.")

    # Case 2: Crime OUTSIDE Dhaka (should have is_crime: false based on rules)
    await run_test("Crime outside Dhaka (Chittagong)", 
                  "Bank heist in Chittagong", 
                  "A group of armed men looted a bank in the Agrabad area of Chittagong city yesterday.")

    # Case 3: Not a crime (Regular news)
    await run_test("Non-crime news", 
                  "Dhaka Metro Rail to run till midnight", 
                  "The authorities have decided to extend the operational hours of the Dhaka Metro Rail service starting next week.")

if __name__ == "__main__":
    asyncio.run(main())
