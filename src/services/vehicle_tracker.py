"""
Athena — Vehicle Tracker (Critical Vehicle Watchlist Matching)

Checks each ANPR result against the active critical vehicle watchlist.
On match: records sighting to DB and broadcasts alert to control dashboard.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.database.models import CriticalVehicleRecord, VehicleSightingRecord
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class VehicleTracker:
    """Matches identified vehicles against the critical vehicle watchlist."""

    def check_and_record(
        self,
        db: Session,
        license_plate: str,
        make: str,
        model: str,
        latitude: float,
        longitude: float,
        camera_id: str,
        confidence: float,
    ) -> CriticalVehicleRecord | None:
        """
        Returns the matched CriticalVehicleRecord if the plate is on the watchlist
        (and make matches), recording a sighting and broadcasting an alert.
        Returns None if no active match found.
        """
        matched = (
            db.query(CriticalVehicleRecord)
            .filter(
                CriticalVehicleRecord.license_plate == license_plate.upper(),
                CriticalVehicleRecord.status == "ACTIVE",
            )
            .first()
        )

        if not matched:
            return None

        # Secondary validation: make (fuzzy, case-insensitive)
        if not (
            matched.make.lower() in make.lower()
            or make.lower() in matched.make.lower()
        ):
            logger.debug(
                f"Plate {license_plate} watchlist hit but make mismatch "
                f"({make} ≠ {matched.make})"
            )
            return None

        # Record sighting
        sighting = VehicleSightingRecord(
            vehicle_id=matched.id,
            camera_id=camera_id,
            latitude=latitude,
            longitude=longitude,
            confidence=confidence,
        )
        db.add(sighting)
        db.commit()
        db.refresh(sighting)

        logger.warning(
            f"🚨 CRITICAL VEHICLE: {license_plate} | Case: {matched.case_type} "
            f"| Camera: {camera_id}"
        )

        # Broadcast to all control dashboard clients
        ws_manager.broadcast_to_control_sync({
            "type": "CRITICAL_VEHICLE_DETECTED",
            "vehicle_id": matched.id,
            "license_plate": license_plate.upper(),
            "make": make,
            "model": model,
            "case_type": matched.case_type,
            "case_number": matched.case_number,
            "priority": matched.priority,
            "location": {"latitude": latitude, "longitude": longitude},
            "camera_id": camera_id,
            "timestamp": sighting.timestamp.isoformat() if sighting.timestamp else None,
        })

        return matched


# Global singleton
vehicle_tracker = VehicleTracker()
