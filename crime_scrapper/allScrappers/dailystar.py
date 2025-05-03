from bs4 import BeautifulSoup
import requests
from utils import parse_article, rate_limit

BASE = "https://www.thedailystar.net/news/bangladesh/crime-justice?page={}"

def get_dailystar_articles(pages=3):
    all_articles = []
    seen_urls = set()
    
    for page in range(pages):
        url = BASE.format(page)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        links = set(
            "https://www.thedailystar.net" + tag['href']
            for tag in soup.find_all("a", href=True)
            if "/news/bangladesh/crime-justice" in tag['href']
        )
        
        for link in links - seen_urls:
            seen_urls.add(link)
            article = parse_article(link)
            if article:
                all_articles.append(article)
                rate_limit(1)
    
    return all_articles
