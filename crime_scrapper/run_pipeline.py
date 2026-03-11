from allScrappers.dailystar import get_dailystar_articles
from NlpClassifier.predictor import CrimePredictor

predictor = CrimePredictor()
articles = get_dailystar_articles()

for article in articles:
    category = predictor.predict(article["title"])
    print(f"[{category.upper()}] {article['title']}")
