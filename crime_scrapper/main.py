import pandas as pd
import os
from allScrappers.dailystar import get_dailystar_articles
from allScrappers.bdnews24 import get_bdnews24_articles

def run_all_scrapers():
    all_data = []

    print("Scraping Daily Star...")
    all_data.extend(get_dailystar_articles(pages=3))

    print("Scraping BDNews24...")
    all_data.extend(get_bdnews24_articles(pages=2))

    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=["url"], inplace=True)

    # ✅ Ensure 'data' folder exists
    os.makedirs("data", exist_ok=True)

    df.to_csv("data/all_crime_news.csv", index=False)
    print(f"Saved {len(df)} articles to data/all_crime_news.csv")

if __name__ == "__main__":
    run_all_scrapers()
