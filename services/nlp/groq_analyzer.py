import os
import json
from groq import Groq
from pathlib import Path

# Use local path if prompts dir is in the same folder as this file
PROMPT_PATH = Path(__file__).parent / "prompts" / "crime_extract.txt"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def analyze_article(headline: str, body: str) -> dict | None:
    """Send article to Groq (Llama 3.3 70B) for crime extraction."""
    if not PROMPT_PATH.exists():
        print(f"Prompt file not found at {PROMPT_PATH}")
        return None
        
    prompt_template = PROMPT_PATH.read_text()
    user_message = f"Headline: {headline}\n\nArticle Body:\n{body[:4000]}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = chat_completion.choices[0].message.content
        print(f"Groq extracted: {content}")
        return json.loads(content)
    except Exception as e:
        print(f"Groq API error for {headline[:30]}: {e}")
        return None
