"""
Athena — Proximity Engine

For each ANPR sighting, checks if the vehicle is on the violation list
and whether any on-duty officers are within the intercept radius (500m).
Fires InterceptAlert records and pushes real-time WebSocket alerts to officers.

Algorithm (from design doc §6):
  1. Lookup plate in violation_vehicles table
  2. Query all on-duty officers within 1km (proximity_scan_radius_m)
  3. For each officer: compute distance + bearing
  4. If distance < 500m AND vehicle approaching: generate alert, push via WS
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.orm import Session

from src.common.utils import bearing_degrees, haversine_distance_m, is_approaching
from src.config import get_settings
from src.database.models import (
    InterceptAlertRecord,
    OfficerLocationRecord,
    ViolationVehicleRecord,
)
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)
settings = get_settings()


def _cardinal(bearing: float) -> str:
    """Convert a bearing (0-360°) to an 8-point cardinal direction string."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(bearing / 45) % 8]


class ProximityEngine:
    """Generates intercept alerts when violation vehicles are near officers."""

    def process(
        self,
        db: Session,
        license_plate: str,
        make: str,
        model: str,
        latitude: float,
        longitude: float,
    ) -> List[InterceptAlertRecord]:
        """
        Checks if vehicle is a violation vehicle, then scans nearby officers.
        Returns list of generated InterceptAlertRecords (may be empty).
        """
        violation = (
            db.query(ViolationVehicleRecord)
            .filter(ViolationVehicleRecord.license_plate == license_plate.upper())
            .first()
        )
        if not violation:
            return []

        logger.info(f"Violation vehicle in frame: {license_plate} ({violation.violation_type})")

        officers = (
            db.query(OfficerLocationRecord)
            .filter(OfficerLocationRecord.on_duty == True)  # noqa: E712
            .all()
        )

        alerts: List[InterceptAlertRecord] = []

        for officer in officers:
            distance = haversine_distance_m(
                latitude, longitude, officer.latitude, officer.longitude
            )
            # Pre-filter: skip if far outside scan radius
            if distance > settings.proximity_scan_radius_m:
                continue

            # Bearing from vehicle position toward officer
            bearing_veh_to_officer = bearing_degrees(
                latitude, longitude, officer.latitude, officer.longitude
            )

            approaching = is_approaching(
                bearing_veh_to_officer,
                officer.heading,
                settings.proximity_approach_angle_deg,
            )

            # Only alert if within 500m AND approaching (or very close < 100m)
            if distance > settings.proximity_radius_m:
                continue
            if not approaching and distance > 100:
                continue

            estimated_intercept_s = distance / max(officer.speed_mps, 5.0)

            alert = InterceptAlertRecord(
                officer_id=officer.officer_id,
                vehicle_plate=license_plate.upper(),
                vehicle_make=make,
                vehicle_model=model,
                violation_type=violation.violation_type,
                latitude=latitude,
                longitude=longitude,
                distance_m=round(distance, 1),
                direction=_cardinal(bearing_veh_to_officer),
                estimated_intercept_s=round(estimated_intercept_s, 1),
                status="PENDING",
            )
            db.add(alert)
            alerts.append(alert)

            ws_manager.send_to_officer_sync(
                officer.officer_id,
                {
                    "type": "INTERCEPT_ALERT",
                    "alert_id": alert.id,
                    "vehicle_plate": license_plate.upper(),
                    "vehicle_make": make,
                    "vehicle_model": model,
                    "violation_type": violation.violation_type,
                    "location": {"latitude": latitude, "longitude": longitude},
                    "distance_m": round(distance, 1),
                    "direction": _cardinal(bearing_veh_to_officer),
                    "estimated_intercept_s": round(estimated_intercept_s, 1),
                },
            )

            logger.info(
                f"Intercept alert → officer {officer.officer_id}: "
                f"{license_plate} at {round(distance)}m {_cardinal(bearing_veh_to_officer)}"
            )

        if alerts:
            db.commit()

        return alerts


# Global singleton
proximity_engine = ProximityEngine()
