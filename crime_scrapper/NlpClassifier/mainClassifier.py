import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Load dataset
df = pd.read_csv("data/all_crime_news.csv")
print(f"Loaded {len(df)} articles.")

# Basic crime keywords (can be extended)
crime_labels = {
    "murder": ["murder", "homicide", "killed", "stabbed", "shot"],
    "robbery": ["robbery", "stolen", "thief", "snatching", "loot"],
    "sexual_violence": ["rape", "harassment", "molested"],
    "drugs": ["drugs", "narcotics", " yaba", "smuggling"],
    "accident": ["accident", "crash", "collision", "road"],
}

stop_words = set(stopwords.words("english"))

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = word_tokenize(text)
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return " ".join(words)

# Preprocess
df['clean_text'] = df['text'].fillna("").apply(preprocess)

# Heuristic Labeling using keyword matching
def label_crime(text):
    for label, keywords in crime_labels.items():
        for keyword in keywords:
            if keyword in text:
                return label
    return "general"

df['label'] = df['clean_text'].apply(label_crime)

# Save labeled data
df.to_csv("data/labeled_crime_news.csv", index=False)
print("[✓] Saved labeled data to labeled_crime_news.csv")

# Optional: Train a classifier
X = df['clean_text']
y = df['label']

vectorizer = TfidfVectorizer(max_features=1000)
X_vec = vectorizer.fit_transform(X)

model = MultinomialNB()
model.fit(X_vec, y)

print("[✓] Classifier trained. Top 5 predictions on sample:")
print(model.predict(X_vec[:5]))
