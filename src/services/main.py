"""
Athena — Services Tier 1: FastAPI Core (FOSS Backend)

Provides REST endpoints using FastAPI for ingesting frames and managing state.
Replaces the AWS Lambda functions in the previous architecture.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
import uvicorn

from src.config import get_settings
from src.common.schemas import Incident, GeoLocation

# Create main app
app = FastAPI(
    title="Athena AI Urban Intelligence",
    description="FOSS Local Self-Hosted Backend API",
    version="1.0.0",
)

logger = logging.getLogger(__name__)
settings = get_settings()

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting Athena Services...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Connected to Postgres at: {settings.db_host}")
    logger.info(f"Connected to Redis at: {settings.redis_url}")

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic service health check."""
    return {"status": "ok", "environment": settings.environment.value}

@app.post("/api/v1/ingest/frame", status_code=status.HTTP_202_ACCEPTED)
async def ingest_frame(camera_id: str, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Accepts a video frame from an edge node via RTSP extractor.
    In a true local architecture, this writes to Redis to be processed by celery/rq workers.
    """
    # Placeholder: Enqueue the frame location to Redis for processing
    # background_tasks.add_task(process_frame_pipeline, camera_id)
    return {"status": "accepted", "camera_id": camera_id}

@app.post("/api/v1/incidents/report", response_model=Incident)
async def report_incident(incident: Incident) -> Incident:
    """
    Manually report an incident. 
    Usually triggered by the background ML detector workers.
    """
    # Write to local PostgreSQL here
    logger.info(f"Incident reported: {incident.type.value} at cam {incident.camera_id}")
    return incident

def run_server() -> None:
    """Entry point to run the Uvicorn ASGI server locally."""
    uvicorn.run(
        "src.services.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "dev"
    )

if __name__ == "__main__":
    run_server()
