# 🏙️ Dhaka Real-Time Crime Index — Refined Implementation Guide

> **Stack:** FastAPI · Docker · Groq (Llama 3.3 70B) · AWS EC2 / S3 / SQS / RDS / ECR / CloudFront · Upstash Redis · React · Leaflet.js

---

## 📁 Table of Contents

1. [Project Structure](#1-project-structure)
2. [Database Schema](#2-database-schema)
3. [Service 1 — Crawler & Parser](#3-service-1--crawler--parser)
4. [Service 2 — NLP / LLM Analysis (Groq)](#4-service-2--nlp--llm-analysis)
5. [Service 3 — Crime Index Calculator](#5-service-3--crime-index-calculator)
6. [Service 4 — React Frontend](#6-service-4--react-frontend)
7. [Infrastructure — Nginx](#7-infrastructure--nginx)
8. [Docker Compose](#8-docker-compose)
9. [AWS Setup Scripts](#9-aws-setup-scripts)
10. [GitHub Actions CI/CD](#10-github-actions-cicd)
11. [Environment Variables & Secrets](#11-environment-variables--secrets)

---

## 1. Project Structure

```
dhaka-crime-index/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── .gitignore
├── services/
│   ├── crawler/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── scrapers/
│   │   │   ├── __init__.py
│   │   │   ├── daily_star.py     # English
│   │   │   ├── bdnews24.py      # English
│   │   │   ├── dhaka_tribune.py # English
│   │   │   └── prothomalo.py    # English (EN subsite)
│   │   ├── s3_client.py
│   │   ├── sqs_client.py
│   │   ├── scheduler.py
│   │   └── requirements.txt
│   ├── nlp/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── sqs_consumer.py
│   │   ├── groq_analyzer.py    # Replaced Claude
│   │   ├── geocoder.py
│   │   ├── db.py
│   │   ├── prompts/
│   │   │   └── crime_extract.txt
│   │   └── requirements.txt
│   ├── index-calculator/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── formula.py
│   │   ├── db.py
│   │   ├── redis_client.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── Dockerfile
│       ├── package.json
│       ├── nginx-frontend.conf
│       ├── public/
│       └── src/
│           ├── App.jsx
│           ├── components/
│           │   ├── CrimeMap.jsx
│           │   ├── IndexPanel.jsx
│           └── hooks/
│               └── useCrimeData.js
├── infrastructure/
│   ├── nginx/
│   │   └── nginx.conf
│   ├── aws/
│   │   ├── setup-s3.sh
│   │   ├── setup-sqs.sh
│   │   ├── setup-rds.sh
│   │   └── setup-ssm.sh
├── scripts/
│   └── init_db.sql
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## 2. Database Schema

```sql
-- scripts/init_db.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- Raw crime events extracted by NLP
CREATE TABLE crime_events (
    id              SERIAL PRIMARY KEY,
    source_url      TEXT NOT NULL UNIQUE,  -- UNIQUE prevents duplicate processing
    source_name     VARCHAR(100),
    published_at    TIMESTAMP,
    crawled_at      TIMESTAMP DEFAULT NOW(),
    headline        TEXT,
    body_summary    TEXT,
    crime_type      VARCHAR(100),   -- murder, robbery, assault, etc.
    severity        INTEGER,        -- 1-10
    location_raw    TEXT,
    thana           VARCHAR(100),
    area            VARCHAR(100),
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    victim_count    INTEGER DEFAULT 0,
    s3_key          TEXT,
    processed       BOOLEAN DEFAULT FALSE
);

-- Aggregated index per zone
CREATE TABLE area_crime_index (
    id              SERIAL PRIMARY KEY,
    area            VARCHAR(100) NOT NULL UNIQUE,
    thana           VARCHAR(100),
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    crime_index     DOUBLE PRECISION DEFAULT 0,
    event_count_30d INTEGER DEFAULT 0,
    last_updated    TIMESTAMP DEFAULT NOW()
);

-- Index history
CREATE TABLE index_history (
    id          SERIAL PRIMARY KEY,
    area        VARCHAR(100),
    crime_index DOUBLE PRECISION,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crime_events_area ON crime_events(area);
CREATE INDEX idx_crime_events_published_at ON crime_events(published_at);
CREATE INDEX idx_area_index_area ON area_crime_index(area);
```

---

## 3. Service 1 — Crawler & Parser

### `services/crawler/requirements.txt`
```
fastapi==0.111.0
uvicorn==0.30.0
httpx==0.27.0
beautifulsoup4==4.12.3
lxml==5.2.2
boto3==1.34.0
apscheduler==3.10.4
python-dotenv==1.0.1
feedparser==6.0.11
```

### `services/crawler/scrapers/daily_star.py` (English)
```python
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DhakaCrimeBot/1.0)"}
CRIME_KEYWORDS = ["murder", "killed", "robbery", "assault", "rape", "theft", "arrested", "police"]

async def scrape_daily_star() -> List[Dict]:
    articles = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        # English Crime Section
        resp = await client.get("https://www.thedailystar.net/crime/rss.xml")
        soup = BeautifulSoup(resp.text, "lxml-xml")
        items = soup.find_all("item")

        for item in items[:20]:
            title = item.find("title").get_text(strip=True)
            link = item.find("link").get_text(strip=True)
            pub_date = item.find("pubDate")
            
            if not any(kw in title.lower() for kw in CRIME_KEYWORDS):
                continue

            try:
                art_resp = await client.get(link)
                art_soup = BeautifulSoup(art_resp.text, "lxml")
                body_div = art_soup.find("div", class_="field-items") or art_soup.find("article")
                body = body_div.get_text(separator=" ", strip=True) if body_div else ""
            except Exception:
                body = ""

            articles.append({
                "url": link,
                "headline": title,
                "body": body,
                "published_at": pub_date.get_text(strip=True) if pub_date else None,
                "source": "The Daily Star",
                "raw_html": art_resp.text if body else ""
            })
    return articles
```

---

## 4. Service 2 — NLP / LLM Analysis (Groq)

### `services/nlp/requirements.txt`
```
fastapi==0.111.0
uvicorn==0.30.0
boto3==1.34.0
groq==0.9.0
httpx==0.27.0
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.30
python-dotenv==1.0.1
```

### `services/nlp/groq_analyzer.py`
```python
import os
import json
from groq import Groq
from pathlib import Path

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
PROMPT_TEMPLATE = Path("prompts/crime_extract.txt").read_text()

async def analyze_article(headline: str, body: str) -> dict | None:
    """Send article to Groq (Llama 3.3 70B) for crime extraction."""
    user_message = f"Headline: {headline}\n\nArticle Body:\n{body[:4000]}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": PROMPT_TEMPLATE},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
```

---

## 6. Service 4 — React Frontend

### `services/frontend/package.json`
```json
{
  "name": "dhaka-crime-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "leaflet": "^1.9.4",
    "leaflet.heat": "^0.2.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### `services/frontend/nginx-frontend.conf`
```nginx
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 8. Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  # Infrastructure
  db:
    image: postgis/postgis:16-3.4-alpine
    environment:
      POSTGRES_USER: crime
      POSTGRES_PASSWORD: crime
      POSTGRES_DB: crimedb
    volumes:
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Services
  crawler:
    build: ./services/crawler
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - SQS_CRAWL_QUEUE_URL=${SQS_CRAWL_QUEUE_URL}
    depends_on:
      - db

  nlp:
    build: ./services/nlp
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - DATABASE_URL=postgresql+asyncpg://crime:crime@db:5432/crimedb
      - SQS_CRAWL_QUEUE_URL=${SQS_CRAWL_QUEUE_URL}
    depends_on:
      - db

  index-calculator:
    build: ./services/index-calculator
    environment:
      - DATABASE_URL=postgresql+asyncpg://crime:crime@db:5432/crimedb
      - UPSTASH_REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./services/frontend
    environment:
      - REACT_APP_API_URL=http://localhost

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - index-calculator
```

---

## 🚀 Verification Plan

### Automated Tests
- `pytest services/index-calculator/tests/test_formula.py` - Verify index math.
- `pytest services/nlp/tests/test_groq.py` - Verify Groq JSON parsing.

### Manual Verification
1. **Scraper Check**: Run `python crawler/scrapers/daily_star.py` manually to see printed JSON.
2. **End-to-End**: Trigger `POST /api/crawler/trigger` and observe logs in `nlp` container.
3. **UI Check**: Verify map circles change color when `area_crime_index` is manually updated in SQL.