import os
import json
import time
import random
import logging
from groq import Groq
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "crime_extract.txt"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def analyze_article(headline: str, body: str, max_retries: int = 3) -> dict | None:
    """Send article to Groq (Llama 3.3 70B) for crime extraction with retry logic."""
    if not PROMPT_PATH.exists():
        logger.error(f"Prompt file not found at {PROMPT_PATH}")
        return None
        
    prompt_template = PROMPT_PATH.read_text()
    user_message = f"Headline: {headline}\n\nBody: {body}"
    
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=300
            )
            content = chat_completion.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Retrying in {wait:.1f}s... (Attempt {attempt+1})")
                time.sleep(wait)
                continue
            logger.error(f"Groq API error for {headline[:30]}: {e}")
            break
            
    return None
