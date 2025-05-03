import time
from newspaper import Article

def parse_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            "title": article.title,
            "text": article.text,
            "publish_date": article.publish_date,
            "url": url
        }
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

def rate_limit(seconds=1):
    time.sleep(seconds)
