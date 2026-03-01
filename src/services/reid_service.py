"""
Athena — Vehicle Re-Identification Service (Demo-Ready)

Groups vehicle sightings into cross-camera tracking sessions using license plate
+ time window (no ML embeddings required).

Logic:
  - If the same plate is seen within SESSION_WINDOW_MINUTES, it belongs to the
    same "journey" (tracking session).
  - Each new camera in a session increments camera_count.
  - Once a vehicle has been spotted at ≥2 cameras, a VEHICLE_PATH_UPDATE event
    is broadcast to all control dashboard clients so a polyline is drawn on the map.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from src.database.models import TrackingSightingRecord, VehicleTrackingRecord
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

SESSION_WINDOW_MINUTES = 30  # sightings within this window = same journey


class ReIDService:
    """Plate-based vehicle re-identification and cross-camera path tracker."""

    def record_sighting(
        self,
        db: Session,
        license_plate: str,
        camera_id: str,
        latitude: float,
        longitude: float,
    ) -> VehicleTrackingRecord:
        """
        Record one camera sighting for a vehicle.  Creates a new tracking session
        if none is active within the time window, otherwise appends to the existing
        one.  Broadcasts a path update whenever the vehicle crosses into a new camera.
        """
        plate = license_plate.upper()
        cutoff = datetime.utcnow() - timedelta(minutes=SESSION_WINDOW_MINUTES)

        # 1. Find an active tracking session for this plate
        track = (
            db.query(VehicleTrackingRecord)
            .filter(
                VehicleTrackingRecord.license_plate == plate,
                VehicleTrackingRecord.last_seen_at >= cutoff,
            )
            .order_by(VehicleTrackingRecord.last_seen_at.desc())
            .first()
        )

        # 2. Start a new session if none found
        if track is None:
            track = VehicleTrackingRecord(license_plate=plate)
            db.add(track)
            db.flush()
            logger.info(f"[ReID] New tracking session {track.id[:8]} for {plate}")

        # 3. Append sighting
        sighting = TrackingSightingRecord(
            tracking_id=track.id,
            camera_id=camera_id,
            latitude=latitude,
            longitude=longitude,
        )
        db.add(sighting)

        # 4. Update session metadata
        track.last_seen_at = datetime.utcnow()
        distinct_cameras: int = (
            db.query(func.count(distinct(TrackingSightingRecord.camera_id)))
            .filter(TrackingSightingRecord.tracking_id == track.id)
            .scalar()
            or 0
        )
        # +1 for the sighting we just added (not yet committed)
        track.camera_count = distinct_cameras + (0 if camera_id in {
            s.camera_id for s in track.path
        } else 1)

        db.commit()
        db.refresh(track)

        logger.debug(
            f"[ReID] {plate} @ {camera_id} — session {track.id[:8]}, "
            f"{track.camera_count} camera(s)"
        )

        # 5. Broadcast path once vehicle is seen at ≥2 distinct cameras
        if track.camera_count >= 2:
            self._broadcast_path(db, track)

        return track

    # ── Internal ───────────────────────────────────────────────────────────────

    def _broadcast_path(self, db: Session, track: VehicleTrackingRecord) -> None:
        sightings = (
            db.query(TrackingSightingRecord)
            .filter(TrackingSightingRecord.tracking_id == track.id)
            .order_by(TrackingSightingRecord.timestamp)
            .all()
        )
        path = [
            {
                "camera_id": s.camera_id,
                "lat": s.latitude,
                "lng": s.longitude,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in sightings
        ]
        ws_manager.broadcast_to_control_sync({
            "type": "VEHICLE_PATH_UPDATE",
            "tracking_id": track.id,
            "license_plate": track.license_plate,
            "camera_count": track.camera_count,
            "path": path,
        })
        logger.info(
            f"[ReID] Path broadcast for {track.license_plate} — "
            f"{len(path)} sightings across {track.camera_count} cameras"
        )


# Global singleton
reid_service = ReIDService()
