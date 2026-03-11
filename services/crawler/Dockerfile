FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for build
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure storage directory exists
RUN mkdir -p storage

ENV PORT=8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
