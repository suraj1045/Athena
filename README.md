# 🏛️ Athena — Open Source Urban Intelligence Platform
> AI-powered, privacy-first computer vision for inclusive and fluid cities.

**Athena** is a real-time smart city platform designed to run directly on existing CCTV networks. This repository is built as a **100% Free and Open-Source Software (FOSS)** stack, utilizing local resources and local models to completely eliminate cloud computing costs.

---

## 🏗 System Architecture (FOSS Stack)

Athena uses a modern, open-source tech stack to achieve enterprise-grade scale tracking and anomaly detection locally:

1. **Ingestion:** `cv2` and Fast-API backend accepting RTSP video streams.
2. **AI / ML Layer:**
   - **YOLOv8** running locally via PyTorch (`ultralytics`) for real-time vehicle and pedestrian anomaly detection.
   - **EasyOCR** for free, local License Plate Recognition (ANPR).
3. **Core Services:**
   - **FastAPI** provides the REST backbone for managing state and routing data.
   - **Redis** handles inter-service event messaging and task queuing.
4. **Data Layer:**
   - **PostgreSQL** (with PostGIS) handles fast geospatial queries for proximity and alerts.
   - **MinIO** provides a local S3-compatible object storage layer for archiving flagged video frames.
5. **Dashboard Layer:**
   - **React / Vite** + Mapbox / Leaflet JS for local Command Center displays.
   - **React Native** for field officer alerts.

---

## 💡 Free Alternatives for Prototype

This repository was specifically tailored to be completely free to run during prototyping and incubation. The following premium cloud services were swapped for open-source alternatives:

| Enterprise Cloud (Paid)         | Athena FOSS Alternative (100% Free) |
|---------------------------------|--------------------------------------|
| **Kinesis Video Streams**       | Direct OpenCV (`cv2`) / HTTP streams |
| **SageMaker Real-Time**         | Local PyTorch (`ultralytics` YOLOv8) |
| **Amazon Rekognition**          | `EasyOCR` (Local LPR)                |
| **AWS Lambda**                  | Local `FastAPI` Server               |
| **Amazon DynamoDB**             | PostgreSQL via Docker                |
| **Amazon SNS / SQS**            | Redis Pub/Sub via Docker             |
| **Amazon S3**                   | MinIO Server via Docker              |
| **Google Maps API**             | OpenStreetMap (`nominatim`)          |

All infrastructure definitions (Terraform) and AWS-specific modules (Boto3) were completely removed to guarantee zero unexpected cloud costs.

---

## 🚀 Quick Start (Local Development)

Because this is a FOSS repo, you can run the entire infrastructure via Docker Desktop! Ensure you have `docker` and `docker-compose` installed.

### 1. Setup Environment
```bash
cp .env.example .env
```
Modify local variables if necessary, but defaults work out-of-the-box.

### 2. Start Infrastructure
Start the local PostgreSQL, Redis, and MinIO servers:
```bash
docker-compose up -d
```

### 3. Install Backend & AI
We recommend using Python 3.11 with `venv`.
```bash
python3.11 -m venv .venv
source .venv/bin/activate

# Install core Fast-API and DB dependencies
make install

# Install PyTorch, YOLO, and EasyOCR
make install-ml
```

### 4. Run the Engine
Run the FastAPI backend which drives the ingestion and local tracking logic:
```bash
uvicorn src.services.main:app --host 0.0.0.0 --port 8000 --reload
```
View the swagger docs locally at: `http://localhost:8000/docs`.

---

## 🛡️ Privacy by Design

Because Athena is designed to be self-hosted, **data never leaves your private network**.
All ML inference happens locally. Hard drives belong to your infrastructure.
There are zero external callbacks to commercial AI APIs.

---

## 🤝 Contributing

Per `Agent.md`, no logic changes are accepted without Tier 1 tests.
```bash
make lint
make typecheck
make test
```
