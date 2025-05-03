import pandas as pd
from allScrappers.dailystar import get_dailystar_articles
from allScrappers.bdnews24 import get_bdnews24_articles
# from scrapers.prothomalo import get_prothomalo_articles
# from scrapers.jugantor import get_jugantor_articles

def run_all_scrapers():
    all_data = []

    print("Scraping Daily Star...")
    all_data.extend(get_dailystar_articles(pages=3))

    print("Scraping BDNews24...")
    all_data.extend(get_bdnews24_articles(pages=2))

    # Add other scrapers here

    df = pd.DataFrame(all_data)
    df.drop_duplicates(subset=["url"], inplace=True)
    df.to_csv("all_crime_news.csv", index=False)
    print(f"Saved {len(df)} articles to all_crime_news.csv")

if __name__ == "__main__":
    run_all_scrapers()
