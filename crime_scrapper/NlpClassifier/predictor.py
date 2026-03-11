# predictor.py
import re
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words("english"))

crime_labels = {
    "murder": ["murder", "homicide", "killed", "stabbed", "shot"],
    "robbery": ["robbery", "stolen", "thief", "snatching", "loot"],
    "sexual_violence": ["rape", "harassment", "molested"],
    "drugs": ["drugs", "narcotics", " yaba", "smuggling"],
    "accident": ["accident", "crash", "collision", "road"],
}

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = word_tokenize(text)
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return " ".join(words)

class CrimePredictor:
    def __init__(self):
        self.vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
        self.model = joblib.load("models/naive_bayes_model.pkl")

    def predict(self, raw_text):
        clean = preprocess(raw_text)
        vec = self.vectorizer.transform([clean])
        return self.model.predict(vec)[0]
