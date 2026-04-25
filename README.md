# Dhaka Real-Time Crime Index (Cindex)

> [!IMPORTANT]
> **Experimental Work in Progress.** This repository is part of an ongoing development effort and is not yet ready for intended production.

## Overview

Cindex is a high-performance safety analytics platform designed to monitor, analyze, and visualize crime data across Dhaka, Bangladesh. The system leverages an event-driven architecture to transform raw news feeds into actionable geospatial insights using Large Language Models (LLMs) and spatial analytics.

## System Architecture

The platform is built on an asynchronous, containerized microservices architecture:

- **Crawler Service**: Periodically scrapes major Bangladeshi news outlets (Daily Star, BDNews24, Dhaka Tribune, Prothom Alo) for crime-related reports.
- **NLP Service**: Processes raw HTML using **Groq (Llama 3.3 70B)** to extract structured facts (crime type, severity, location, victims) and geocodes them via OpenStreetMap/Nominatim.
- **Index Calculator**: Computes a dynamic crime index per area using a dual-methodology (30-day exponential decay vs. cumulative historical patterns).
- **Frontend**: A performance-optimized React SPA featuring Leaflet-based geospatial visualizations and real-time risk dashboards.

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | FastAPI (Python), Groq (LLM), PostGIS |
| **Frontend** | React 18, Zustand, Leaflet.js, TailwindCSS |
| **Infrastructure** | AWS (EC2, S3, SQS, RDS), Terraform, Docker, Nginx |
| **Cache/Bus** | Upstash Redis, AWS SQS |

## Key Features

- **Automated Extraction**: Zero-shot crime fact extraction using Llama 3.3.
- **Geospatial Intelligence**: PostGIS-powered spatial indexing and neighborhood-level risk mapping.
- **Dual-Index Methodology**: Balanced risk assessment combining recent 30-day volatility with historical crime trends.
- **Infrastructure as Code**: Fully reproducible AWS environment via Terraform.
- **High-Performance UI**: GPU-accelerated map layers and virtualized data lists for seamless exploration.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- AWS CLI (configured for S3/SQS/RDS access)
- Groq API Key

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/strazyuk/Cindex_exp.git
   cd Cindex_exp
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY and AWS credentials
   ```

3. Spin up the stack:
   ```bash
   docker-compose up --build
   ```

## Repository Structure

```text
├── infrastructure/    # Terraform IaC and Nginx configurations
├── services/
│   ├── crawler/       # News scraping engine
│   ├── nlp/           # LLM extraction and geocoding
│   ├── index-calculator/ # Risk score computation
│   └── frontend/      # React geospatial dashboard
├── scripts/           # Database migration and utility scripts
└── docker-compose.yml # Local orchestration
```

## Disclaimer

The data extracted and indices generated are based on automated analysis of public news reports. They should be used for informational purposes only and do not constitute official crime statistics.

---
© 2026 Experimental Crime Index Project.
