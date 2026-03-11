import asyncio
import os
from groq_analyzer import analyze_article
from dotenv import load_dotenv

load_dotenv()

async def manual_test():
    headline = "Young man killed in Mirpur robbery"
    body = """
    A 25-year-old man was killed by robbers in the Shah Ali area of Mirpur, Dhaka early today. 
    The incident occurred around 3:00 am when a group of 5-6 robbers entered his house. 
    Police from the local thana arrived shortly after.
    """
    
    print("Testing Groq Analyzer...")
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in environment.")
        return

    result = await analyze_article(headline, body)
    if result:
        print("\n--- Extraction Result ---")
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Extraction failed.")

if __name__ == "__main__":
    asyncio.run(manual_test())
