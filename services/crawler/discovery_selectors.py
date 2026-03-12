import httpx
from bs4 import BeautifulSoup

urls = [
    "https://en.prothomalo.com/bangladesh/4mrgpp013m",
    "https://www.thedailystar.net/news/arrest-drive-10000" # fallback to an old one to see structure
]

headers = {"User-Agent": "Mozilla/5.0"}

for url in urls:
    print(f"\nAnalyzing: {url}")
    try:
        resp = httpx.get(url, headers=headers, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for the largest text block
        potential_tags = soup.find_all(['div', 'article'])
        for tag in potential_tags:
            classes = tag.get('class', [])
            text_len = len(tag.get_text())
            if text_len > 500:
                print(f"Tag: {tag.name}, Classes: {classes}, Text Length: {text_len}")
    except Exception as e:
        print(f"Error: {e}")
