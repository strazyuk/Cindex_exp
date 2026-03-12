from bs4 import BeautifulSoup
import json

def extract_body_window(html: str, max_chars: int = 3000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    
    # Print first few paragraph tags to see what's in them
    for i, p in enumerate(paragraphs[:10]):
        print(f"P{i}: {p.get_text()[:100]}...")
        
    priority = " ".join(p.get_text() for p in paragraphs[:3])
    remaining = " ".join(p.get_text() for p in paragraphs[3:])
    
    full_text = priority + " " + remaining
    return full_text[:max_chars].strip()

if __name__ == "__main__":
    with open("/tmp/test_article_local.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    extracted = extract_body_window(html)
    print("\nEXTRACTED TEXT (First 500 chars):")
    print(extracted[:500])
    
    print(f"\nTotal length: {len(extracted)}")
