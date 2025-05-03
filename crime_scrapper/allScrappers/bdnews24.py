from bs4 import BeautifulSoup
import requests
from utils import parse_article, rate_limit

BASE = "https://bdnews24.com/crime?page={}"

def get_bdnews24_articles(pages=2):
    all_articles = []
    for page in range(1, pages+1):
        url = BASE.format(page)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for tag in soup.find_all("a", href=True):
            href = tag['href']
            if href.startswith("https://bdnews24.com/crime/"):
                article = parse_article(href)
                if article:
                    all_articles.append(article)
                    rate_limit(1)
    return all_articles
