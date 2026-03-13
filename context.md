# 🏙️ Dhaka Real-Time Crime Index — Project Context

Welcome to the **Dhaka Crime Index** project. This system is a production-grade safety analytics platform that scrapes, analyzes, and visualizes crime data across Dhaka, Bangladesh.

## 🚀 System Overview

The architecture has evolved from a local prototype to a robust, event-driven cloud system on **AWS**, managed via **Terraform (IaC)**.

```mermaid
graph TD
    A[Crawler (EC2/Docker)] -->|Raw HTML| B[(AWS S3)]
    A -->|Notify| C[AWS SQS Queue]
    C -->|Trigger| D[NLP Service (EC2/Docker)]
    D -->|Fetch HTML| B
    D -->|Fact Extraction| E[Groq API (Llama 3.3)]
    D -->|Geocode| F[OSM Nominatim]
    D -->|Save Events| G[(AWS RDS PostGIS)]
    H[Index Calculator] -->|Sync & Merge| G
    H -->|Scores| I[(Upstash Redis)]
    J[Nginx Gateway] -->|UI/API| K[React Max-Perf SPA]
```

## 🛠️ Infrastructure as Code (Terraform)

The entire environment is provisioned systematically using **Terraform** in the `us-east-1` region:

- **Networking**: Custom VPC with public and secondary subnets, isolated via specific Security Groups (Web SG vs. DB SG).
- **Compute**: **EC2 (t3.small)** instance serving as the microservices host, auto-bootstrapped with Docker and Docker Compose.
- **Data Layer**: **AWS RDS (PostgreSQL 16)** with the **PostGIS** extension for spatial analytics.
- **Messaging**: **AWS SQS** manages asynchronous handshakes between the Crawler and NLP services.
- **Storage**: **AWS S3** acts as the primary archival store for all scraped raw news HTML.
- **Security**: **IAM Roles** and Instance Profiles ensure fine-grained access to cloud resources; **SSM Parameter Store** manages encrypted secrets (Groq keys, DB passwords).

## 📊 Dual Index Methodology

The system calculates two distinct safety metrics:

1.  **30-Day Index (Recent Risk)**: Time-weighted snapshots using exponential decay to prioritize "live" news.
2.  **Cumulative Index (Historical Pattern)**: Blends live events with the **Bangladesh Crime Dataset (1100+ entries)**.
    - **Historical Base Weight**: Fixed weight of **0.1** (or **2.5** when emphasizing bedrock risk) to prevent historical data from inflating recent indicators while providing long-term patterns.

## 🧠 Data Integrity & Deduplication

- **Unified Table (`combined_events`)**: A physical merge of crawled data and historical records, re-synchronized during every index recalculation.
- **Compound Name Preservation**: Specific tracking for entities like **"Dhaka University"** or **"Old Dhaka"** to prevent spatial collision.
- **Spatial Normalization**: All area names are `LOWER(TRIM())` at the DB level; coordinates are resolved via Nominatim with fallback to historical centroids.

## ⚡ "Max Performance" Frontend

- **Atomic State (Zustand)**: Granular subscriptions to prevent unnecessary re-renders.
- **List Virtualization**: `react-window` handles thousands of neighborhood records at 60fps.
- **GPU Acceleration**: Hardware-accelerated map layers and glassmorphism for a premium UI feel.
- **Concurrent Mode**: React 18 optimizations for non-blocking data transitions.

---
*Last Updated: 2026-03-13 — Production AWS Infrastructure & Terraform Integration*
