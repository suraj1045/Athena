"""
Athena — FastAPI Application (MVP)

Complete REST + WebSocket API for the Athena hackathon prototype.

Endpoints:
  POST   /api/v1/ingest/frame                   — receive camera frame, run pipeline
  POST   /api/v1/vehicles/critical               — add vehicle to watchlist
  GET    /api/v1/vehicles/critical               — list active watchlist
  PATCH  /api/v1/vehicles/critical/{id}/deactivate — remove from watchlist
  POST   /api/v1/violations/vehicle              — add violation vehicle
  GET    /api/v1/violations/vehicle              — list violation vehicles
  PUT    /api/v1/officers/{id}/location          — update officer GPS
  GET    /api/v1/incidents                       — list incidents
  POST   /api/v1/incidents/{id}/clear            — mark incident cleared
  GET    /api/v1/alerts                          — list intercept alerts
  POST   /api/v1/alerts/{id}/acknowledge         — officer acknowledges alert
  WS     /ws/officer/{officer_id}               — officer app real-time feed
  WS     /ws/control/{client_id}               — control dashboard real-time feed
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config import get_settings
from src.database.models import (
    CriticalVehicleRecord,
    IncidentRecord,
    InterceptAlertRecord,
    OfficerLocationRecord,
    TrackingSightingRecord,
    VehicleTrackingRecord,
    ViolationVehicleRecord,
)
from src.database.session import Base, SessionLocal, engine, get_db
from src.services.pipeline import frame_pipeline
from src.services.reid_service import reid_service
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
settings = get_settings()

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Athena Urban Intelligence — MVP API",
    description="Hackathon prototype: real-time incident detection, vehicle tracking, and proximity alerts.",
    version="1.0.0",
)


@app.on_event("startup")
async def startup() -> None:
    # Create all tables (no migrations for hackathon)
    Base.metadata.create_all(bind=engine)
    # Give WebSocket manager access to the running event loop
    ws_manager.set_event_loop(asyncio.get_event_loop())
    logger.info("Athena MVP started — DB tables ready, WebSocket loop captured.")


# ── Request / Response models ─────────────────────────────────────────────────

class RegisterCriticalVehicleRequest(BaseModel):
    license_plate: str
    make: str
    model: str
    case_type: str          # KIDNAPPING | HIT_AND_RUN | STOLEN
    case_number: str
    priority: str = "HIGH"  # HIGH | CRITICAL
    registered_by: str


class AddViolationVehicleRequest(BaseModel):
    license_plate: str
    violation_type: str     # EXPIRED_PERMIT | UNPAID_FINE | SUSPENDED_REGISTRATION
    description: str
    severity: str = "LOW"


class UpdateOfficerLocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    heading: float = Field(default=0.0, ge=0.0, lt=360.0)
    speed_mps: float = Field(default=0.0, ge=0.0)
    on_duty: bool = True


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health() -> Dict[str, str]:
    return {"status": "ok", "environment": settings.environment.value}


# ── Frame Ingestion ───────────────────────────────────────────────────────────

@app.post("/api/v1/ingest/frame", status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def ingest_frame(
    camera_id: str,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    file: UploadFile = File(...),
) -> Dict[str, str]:
    """
    Accepts a JPEG frame from an edge camera.
    Runs YOLO + ANPR pipeline in a background thread.
    """
    frame_bytes = await file.read()
    background_tasks.add_task(
        frame_pipeline.process, frame_bytes, camera_id, latitude, longitude
    )
    return {"status": "accepted", "camera_id": camera_id}


# ── Critical Vehicle Watchlist ────────────────────────────────────────────────

@app.post("/api/v1/vehicles/critical", status_code=status.HTTP_201_CREATED, tags=["Watchlist"])
def register_critical_vehicle(
    req: RegisterCriticalVehicleRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Register a vehicle on the critical tracking watchlist."""
    record = CriticalVehicleRecord(
        license_plate=req.license_plate.upper(),
        make=req.make,
        model=req.model,
        case_type=req.case_type,
        case_number=req.case_number,
        priority=req.priority,
        registered_by=req.registered_by,
        status="ACTIVE",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Critical vehicle registered: {record.license_plate} ({record.case_type})")
    return {"id": record.id, "license_plate": record.license_plate, "status": record.status}


@app.get("/api/v1/vehicles/critical", tags=["Watchlist"])
def list_critical_vehicles(
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all active entries from the critical vehicle watchlist."""
    records = (
        db.query(CriticalVehicleRecord)
        .filter(CriticalVehicleRecord.status == "ACTIVE")
        .order_by(CriticalVehicleRecord.registered_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "license_plate": r.license_plate,
            "make": r.make,
            "model": r.model,
            "case_type": r.case_type,
            "case_number": r.case_number,
            "priority": r.priority,
            "registered_at": r.registered_at.isoformat() if r.registered_at else None,
            "registered_by": r.registered_by,
            "sightings_count": len(r.sightings),
        }
        for r in records
    ]


@app.patch("/api/v1/vehicles/critical/{vehicle_id}/deactivate", tags=["Watchlist"])
def deactivate_critical_vehicle(
    vehicle_id: str, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Remove a vehicle from active tracking."""
    record = db.query(CriticalVehicleRecord).filter_by(id=vehicle_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    record.status = "RESOLVED"
    db.commit()
    return {"id": vehicle_id, "status": "RESOLVED"}


# ── Violation Vehicles ────────────────────────────────────────────────────────

@app.post("/api/v1/violations/vehicle", status_code=status.HTTP_201_CREATED, tags=["Violations"])
def add_violation_vehicle(
    req: AddViolationVehicleRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Add a vehicle to the violation database (triggers proximity alerts when detected)."""
    existing = (
        db.query(ViolationVehicleRecord)
        .filter_by(license_plate=req.license_plate.upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Vehicle already in violation DB")
    record = ViolationVehicleRecord(
        license_plate=req.license_plate.upper(),
        violation_type=req.violation_type,
        description=req.description,
        severity=req.severity,
    )
    db.add(record)
    db.commit()
    return {"id": record.id, "license_plate": record.license_plate}


@app.get("/api/v1/violations/vehicle", tags=["Violations"])
def list_violation_vehicles(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    records = db.query(ViolationVehicleRecord).all()
    return [
        {
            "id": r.id,
            "license_plate": r.license_plate,
            "violation_type": r.violation_type,
            "description": r.description,
            "severity": r.severity,
        }
        for r in records
    ]


# ── Officer Location ──────────────────────────────────────────────────────────

@app.put("/api/v1/officers/{officer_id}/location", tags=["Officers"])
def update_officer_location(
    officer_id: str,
    req: UpdateOfficerLocationRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Upsert an officer's GPS location, heading, and duty status.
    Called frequently by the Officer App (every 5-10 seconds).
    """
    record = db.query(OfficerLocationRecord).filter_by(officer_id=officer_id).first()
    if record is None:
        record = OfficerLocationRecord(officer_id=officer_id)
        db.add(record)
    record.latitude = req.latitude
    record.longitude = req.longitude
    record.heading = req.heading
    record.speed_mps = req.speed_mps
    record.on_duty = req.on_duty
    record.last_updated = datetime.now(tz=timezone.utc)
    db.commit()

    ws_manager.broadcast_to_control_sync({
        "type": "OFFICER_LOCATION_UPDATE",
        "officer_id": officer_id,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "heading": req.heading,
        "speed_mps": req.speed_mps,
        "on_duty": req.on_duty,
        "last_updated": record.last_updated.isoformat(),
    })

    return {"officer_id": officer_id, "status": "updated"}


@app.get("/api/v1/officers", tags=["Officers"])
def list_officers(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    records = db.query(OfficerLocationRecord).filter_by(on_duty=True).all()
    return [
        {
            "officer_id": r.officer_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "heading": r.heading,
            "speed_mps": r.speed_mps,
            "on_duty": r.on_duty,
            "last_updated": r.last_updated.isoformat() if r.last_updated else None,
        }
        for r in records
    ]


# ── Incidents ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/incidents", tags=["Incidents"])
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    city: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    q = db.query(IncidentRecord)
    if status_filter:
        q = q.filter(IncidentRecord.status == status_filter.upper())
    if city:
        q = q.filter(IncidentRecord.city == city)
    records = q.order_by(IncidentRecord.detected_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "type": r.type,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "camera_id": r.camera_id,
            "confidence": r.confidence,
            "status": r.status,
            "city": r.city,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            "cleared_at": r.cleared_at.isoformat() if r.cleared_at else None,
        }
        for r in records
    ]


@app.post("/api/v1/incidents/{incident_id}/clear", tags=["Incidents"])
def clear_incident(incident_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Mark an incident as cleared and notify the Navigation API."""
    record = db.query(IncidentRecord).filter_by(id=incident_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    record.status = "CLEARED"
    record.cleared_at = datetime.now(tz=timezone.utc)
    db.commit()

    # Best-effort Nav API clear notification
    try:
        from src.services.nav_api import nav_client
        nav_client.notify_incident_cleared(incident_id)
    except Exception as exc:
        logger.warning(f"Nav API clear failed: {exc}")

    # Broadcast cleared event to control dashboard
    ws_manager.broadcast_to_control_sync({
        "type": "INCIDENT_CLEARED",
        "incident_id": incident_id,
        "cleared_at": record.cleared_at.isoformat(),
    })
    return {"id": incident_id, "status": "CLEARED"}


# ── Simulation Endpoints (for demo/testing without real camera feeds) ─────────

class SimulateIncidentRequest(BaseModel):
    type: str = "STALLED_VEHICLE"
    latitude: float
    longitude: float
    camera_id: str = "SIM-CAM-01"
    confidence: float = 0.91
    city: Optional[str] = None


class SimulateInterceptRequest(BaseModel):
    officer_id: str = "OFF-001"
    vehicle_plate: str
    vehicle_make: str = "Toyota"
    vehicle_model: str = "Innova"
    violation_type: str = "EXPIRED_PERMIT"
    latitude: float
    longitude: float
    distance_m: float = 320.0
    direction: str = "NE"
    estimated_intercept_s: float = 45.0


@app.post("/api/v1/simulate/incident", status_code=status.HTTP_201_CREATED, tags=["Simulation"])
def simulate_incident(
    req: SimulateIncidentRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Inject a synthetic incident directly — bypasses ML pipeline. For demo/testing only."""
    record = IncidentRecord(
        type=req.type,
        latitude=req.latitude,
        longitude=req.longitude,
        camera_id=req.camera_id,
        confidence=req.confidence,
        status="ACTIVE",
        city=req.city,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    ws_manager.broadcast_to_control_sync({
        "type": "INCIDENT_DETECTED",
        "id": record.id,
        "data": {
            "type": record.type,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "camera_id": record.camera_id,
            "confidence": record.confidence,
            "status": record.status,
            "city": record.city,
            "detected_at": record.detected_at.isoformat() if record.detected_at else None,
        },
    })
    return {"id": record.id, "type": record.type, "status": "ACTIVE"}


@app.post("/api/v1/simulate/intercept", status_code=status.HTTP_201_CREATED, tags=["Simulation"])
def simulate_intercept(
    req: SimulateInterceptRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Inject a synthetic intercept alert — bypasses proximity engine. For demo/testing only."""
    record = InterceptAlertRecord(
        officer_id=req.officer_id,
        vehicle_plate=req.vehicle_plate,
        vehicle_make=req.vehicle_make,
        vehicle_model=req.vehicle_model,
        violation_type=req.violation_type,
        latitude=req.latitude,
        longitude=req.longitude,
        distance_m=req.distance_m,
        direction=req.direction,
        estimated_intercept_s=req.estimated_intercept_s,
        status="PENDING",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    alert_payload = {
        "type": "INTERCEPT_ALERT",
        "alert_id": record.id,
        "officer_id": record.officer_id,
        "vehicle_plate": record.vehicle_plate,
        "vehicle_make": record.vehicle_make,
        "vehicle_model": record.vehicle_model,
        "violation_type": record.violation_type,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "distance_m": record.distance_m,
        "direction": record.direction,
        "estimated_intercept_s": record.estimated_intercept_s,
        "status": record.status,
    }
    ws_manager.broadcast_to_control_sync(alert_payload)
    ws_manager.send_to_officer_sync(req.officer_id, alert_payload)
    return {"id": record.id, "officer_id": record.officer_id, "status": "PENDING"}


# ── Intercept Alerts ──────────────────────────────────────────────────────────

@app.get("/api/v1/alerts", tags=["Alerts"])
def list_alerts(
    officer_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    q = db.query(InterceptAlertRecord)
    if officer_id:
        q = q.filter(InterceptAlertRecord.officer_id == officer_id)
    records = q.order_by(InterceptAlertRecord.generated_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "officer_id": r.officer_id,
            "vehicle_plate": r.vehicle_plate,
            "vehicle_make": r.vehicle_make,
            "vehicle_model": r.vehicle_model,
            "violation_type": r.violation_type,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "distance_m": r.distance_m,
            "direction": r.direction,
            "estimated_intercept_s": r.estimated_intercept_s,
            "status": r.status,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
        }
        for r in records
    ]


@app.post("/api/v1/alerts/{alert_id}/acknowledge", tags=["Alerts"])
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    record = db.query(InterceptAlertRecord).filter_by(id=alert_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Alert not found")
    record.status = "ACKNOWLEDGED"
    record.acknowledged_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"id": alert_id, "status": "ACKNOWLEDGED"}


# ── Vehicle Tracking (Re-ID / Cross-Camera) ───────────────────────────────────

@app.get("/api/v1/tracking/{plate}", tags=["Tracking"])
def get_vehicle_path(plate: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return the latest active tracking session and full camera path for a plate."""
    track = (
        db.query(VehicleTrackingRecord)
        .filter(VehicleTrackingRecord.license_plate == plate.upper())
        .order_by(VehicleTrackingRecord.last_seen_at.desc())
        .first()
    )
    if not track:
        raise HTTPException(status_code=404, detail="No tracking session found for plate")
    sightings = (
        db.query(TrackingSightingRecord)
        .filter(TrackingSightingRecord.tracking_id == track.id)
        .order_by(TrackingSightingRecord.timestamp)
        .all()
    )
    return {
        "tracking_id": track.id,
        "license_plate": track.license_plate,
        "camera_count": track.camera_count,
        "started_at": track.started_at.isoformat() if track.started_at else None,
        "last_seen_at": track.last_seen_at.isoformat() if track.last_seen_at else None,
        "path": [
            {
                "camera_id": s.camera_id,
                "lat": s.latitude,
                "lng": s.longitude,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in sightings
        ],
    }


class SimulateSightingRequest(BaseModel):
    license_plate: str
    camera_id: str
    latitude: float
    longitude: float


@app.post("/api/v1/simulate/sighting", status_code=status.HTTP_202_ACCEPTED, tags=["Simulation"])
def simulate_sighting(
    req: SimulateSightingRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Inject a synthetic vehicle sighting for Re-ID / cross-camera tracking demo."""
    track = reid_service.record_sighting(
        db, req.license_plate, req.camera_id, req.latitude, req.longitude
    )
    return {
        "status": "accepted",
        "tracking_id": track.id,
        "license_plate": track.license_plate,
        "camera_count": track.camera_count,
    }


# ── WebSocket Endpoints ───────────────────────────────────────────────────────

@app.websocket("/ws/officer/{officer_id}")
async def officer_websocket(websocket: WebSocket, officer_id: str) -> None:
    """
    Persistent WebSocket connection for the Officer App.
    Receives INTERCEPT_ALERT messages pushed by the proximity engine.
    Officers can also send back ACKNOWLEDGE_ALERT messages.
    """
    await ws_manager.connect_officer(websocket, officer_id)
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ACKNOWLEDGE_ALERT":
                alert_id = data.get("alert_id")
                if alert_id:
                    record = db.query(InterceptAlertRecord).filter_by(id=alert_id).first()
                    if record:
                        record.status = "ACKNOWLEDGED"
                        record.acknowledged_at = datetime.now(tz=timezone.utc)
                        db.commit()
    except WebSocketDisconnect:
        ws_manager.disconnect_officer(officer_id)
        logger.info(f"Officer {officer_id} disconnected")
    finally:
        db.close()


@app.websocket("/ws/control/{client_id}")
async def control_websocket(websocket: WebSocket, client_id: str) -> None:
    """
    Persistent WebSocket connection for the Control Dashboard.
    Receives INCIDENT_DETECTED, INCIDENT_CLEARED, CRITICAL_VEHICLE_DETECTED events.
    """
    await ws_manager.connect_control(websocket, client_id)
    try:
        while True:
            # Keep connection alive; control dashboard is receive-only
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_control(client_id)
        logger.info(f"Control client {client_id} disconnected")


# ── Entry point ───────────────────────────────────────────────────────────────

def run_server() -> None:
    uvicorn.run(
        "src.services.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment.value == "dev",
    )


if __name__ == "__main__":
    run_server()
