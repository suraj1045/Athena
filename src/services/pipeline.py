"""
Athena — End-to-End Frame Processing Pipeline

Wires together: JPEG frame → YOLO (incident detection) → ANPR (vehicle ID)
                → DB persistence → Nav API notification → WebSocket broadcasts

Called synchronously from a FastAPI BackgroundTask thread.
The WebSocket manager's sync-safe methods handle cross-thread alert delivery.
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from src.common.schemas import GeoLocation
from src.config import get_settings
from src.database.models import IncidentRecord, VehicleIdentificationRecord
from src.database.session import SessionLocal
from src.ml_models.anpr.engine import ANPREngine
from src.ml_models.yolo_detector.model import YOLODetector
from src.services.nav_api import nav_client
from src.services.proximity_engine import proximity_engine
from src.services.vehicle_tracker import vehicle_tracker
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Lazy-loaded ML models (expensive to initialise, share across calls) ────────
_yolo: Optional[YOLODetector] = None
_anpr: Optional[ANPREngine] = None


def _get_yolo() -> YOLODetector:
    global _yolo
    if _yolo is None:
        _yolo = YOLODetector()
    return _yolo


def _get_anpr() -> ANPREngine:
    global _anpr
    if _anpr is None:
        _anpr = ANPREngine()
    return _anpr


# ── Pipeline ───────────────────────────────────────────────────────────────────

class FramePipeline:
    """
    Processes one JPEG frame through the complete detection pipeline.
    Designed to run in a background thread (sync DB + blocking ML calls).
    """

    def process(
        self,
        frame_bytes: bytes,
        camera_id: str,
        latitude: float,
        longitude: float,
    ) -> None:
        frame = self._decode(frame_bytes)
        if frame is None:
            logger.warning(f"Undecoded frame from camera {camera_id} — skipping")
            return

        location = GeoLocation(latitude=latitude, longitude=longitude)
        db = SessionLocal()
        try:
            self._incident_detection(db, frame, camera_id, location)
            self._vehicle_identification(db, frame, camera_id, location)
        except Exception as exc:
            logger.error(f"Pipeline error on camera {camera_id}: {exc}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    # ── Incident detection ────────────────────────────────────────────────────

    def _incident_detection(
        self, db, frame: np.ndarray, camera_id: str, location: GeoLocation
    ) -> None:
        try:
            incidents = _get_yolo().detect(frame, camera_id, location)
        except Exception as exc:
            logger.error(f"YOLO error ({camera_id}): {exc}")
            return

        for inc in incidents:
            if inc.confidence < settings.detection_confidence_min:
                continue

            record = IncidentRecord(
                type=inc.type.value,
                latitude=location.latitude,
                longitude=location.longitude,
                camera_id=camera_id,
                confidence=inc.confidence,
                status="ACTIVE",
            )
            db.add(record)
            db.flush()  # populate record.id

            logger.info(
                f"Incident: {record.type} at {camera_id} (conf={inc.confidence:.2f})"
            )

            # Nav API notification (best-effort, non-blocking)
            try:
                nav_client.notify_incident(
                    incident_id=record.id,
                    incident_type=record.type,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    detected_at=record.detected_at,
                )
            except Exception as exc:
                logger.warning(f"Nav API failed: {exc}")

            # Push to control dashboard over WebSocket
            ws_manager.broadcast_to_control_sync({
                "type": "INCIDENT_DETECTED",
                "incident_id": record.id,
                "incident_type": record.type,
                "location": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                },
                "camera_id": camera_id,
                "confidence": inc.confidence,
                "status": "ACTIVE",
            })

        db.commit()

    # ── Vehicle identification ────────────────────────────────────────────────

    def _vehicle_identification(
        self, db, frame: np.ndarray, camera_id: str, location: GeoLocation
    ) -> None:
        try:
            identification = _get_anpr().process(frame, camera_id, location)
        except Exception as exc:
            logger.error(f"ANPR error ({camera_id}): {exc}")
            return

        if identification is None:
            return

        plate = identification.license_plate
        lat, lon = location.latitude, location.longitude

        record = VehicleIdentificationRecord(
            license_plate=plate,
            make=identification.make,
            model=identification.model,
            color=identification.color,
            latitude=lat,
            longitude=lon,
            camera_id=camera_id,
            plate_confidence=identification.confidence.plate,
            make_confidence=identification.confidence.make,
            model_confidence=identification.confidence.model,
        )
        db.add(record)
        db.commit()

        logger.info(
            f"Vehicle: {plate} ({identification.make} {identification.model}) "
            f"at {camera_id}"
        )

        # Check critical vehicle watchlist
        vehicle_tracker.check_and_record(
            db=db,
            license_plate=plate,
            make=identification.make,
            model=identification.model,
            latitude=lat,
            longitude=lon,
            camera_id=camera_id,
            confidence=identification.confidence.plate,
        )

        # Check proximity alerts for violation vehicles
        proximity_engine.process(
            db=db,
            license_plate=plate,
            make=identification.make,
            model=identification.model,
            latitude=lat,
            longitude=lon,
        )

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _decode(frame_bytes: bytes) -> Optional[np.ndarray]:
        try:
            arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:
            return None


# Global singleton
frame_pipeline = FramePipeline()
