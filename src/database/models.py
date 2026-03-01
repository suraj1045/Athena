"""
Athena — SQLAlchemy ORM Models

All database tables for the Athena MVP. Uses create_all() at startup —
no migrations needed for the hackathon.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.session import Base


def _uuid() -> str:
    return str(uuid4())


# ── Incidents ──────────────────────────────────────────────────────────────────

class IncidentRecord(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=_uuid)
    type = Column(String, nullable=False)           # STALLED_VEHICLE | BREAKDOWN | ACCIDENT
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    camera_id = Column(String, nullable=False)
    detected_at = Column(DateTime, server_default=func.now())
    cleared_at = Column(DateTime, nullable=True)
    confidence = Column(Float, nullable=False)
    status = Column(String, default="ACTIVE")       # ACTIVE | CLEARED
    city = Column(String, nullable=True, index=True)


# ── Vehicle Identifications ────────────────────────────────────────────────────

class VehicleIdentificationRecord(Base):
    __tablename__ = "vehicle_identifications"

    id = Column(String, primary_key=True, default=_uuid)
    license_plate = Column(String, nullable=False, index=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    color = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    camera_id = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    plate_confidence = Column(Float, nullable=False)
    make_confidence = Column(Float, nullable=False)
    model_confidence = Column(Float, nullable=False)


# ── Critical Vehicles (Watchlist) ──────────────────────────────────────────────

class CriticalVehicleRecord(Base):
    __tablename__ = "critical_vehicles"

    id = Column(String, primary_key=True, default=_uuid)
    license_plate = Column(String, nullable=False, index=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    case_type = Column(String, nullable=False)      # KIDNAPPING | HIT_AND_RUN | STOLEN
    case_number = Column(String, nullable=False)
    priority = Column(String, default="HIGH")       # HIGH | CRITICAL
    status = Column(String, default="ACTIVE")       # ACTIVE | RESOLVED | CANCELLED
    registered_at = Column(DateTime, server_default=func.now())
    registered_by = Column(String, nullable=False)

    sightings = relationship("VehicleSightingRecord", back_populates="vehicle",
                             cascade="all, delete-orphan")


class VehicleSightingRecord(Base):
    __tablename__ = "vehicle_sightings"

    id = Column(String, primary_key=True, default=_uuid)
    vehicle_id = Column(String, ForeignKey("critical_vehicles.id"), nullable=False, index=True)
    camera_id = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    confidence = Column(Float, nullable=False)

    vehicle = relationship("CriticalVehicleRecord", back_populates="sightings")


# ── Violation Vehicles ─────────────────────────────────────────────────────────

class ViolationVehicleRecord(Base):
    __tablename__ = "violation_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String, nullable=False, unique=True, index=True)
    violation_type = Column(String, nullable=False)  # EXPIRED_PERMIT | UNPAID_FINE | SUSPENDED_REGISTRATION
    description = Column(String, nullable=False)
    severity = Column(String, default="LOW")         # LOW | MEDIUM | HIGH
    added_at = Column(DateTime, server_default=func.now())


# ── Officer Locations ──────────────────────────────────────────────────────────

class OfficerLocationRecord(Base):
    __tablename__ = "officer_locations"

    officer_id = Column(String, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    heading = Column(Float, default=0.0)            # degrees 0-360
    speed_mps = Column(Float, default=0.0)
    on_duty = Column(Boolean, default=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ── Intercept Alerts ───────────────────────────────────────────────────────────

class InterceptAlertRecord(Base):
    __tablename__ = "intercept_alerts"

    id = Column(String, primary_key=True, default=_uuid)
    officer_id = Column(String, nullable=False, index=True)
    vehicle_plate = Column(String, nullable=False)
    vehicle_make = Column(String, nullable=False)
    vehicle_model = Column(String, nullable=False)
    violation_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_m = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    estimated_intercept_s = Column(Float, nullable=False)
    generated_at = Column(DateTime, server_default=func.now())
    acknowledged_at = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING")      # PENDING | ACKNOWLEDGED | EXPIRED


# ── Vehicle Tracking (Re-ID / Cross-Camera) ────────────────────────────────────

class VehicleTrackingRecord(Base):
    __tablename__ = "vehicle_tracking"

    id            = Column(String, primary_key=True, default=_uuid)
    license_plate = Column(String, nullable=False, index=True)
    started_at    = Column(DateTime, server_default=func.now())
    last_seen_at  = Column(DateTime, server_default=func.now())
    camera_count  = Column(Integer, default=1)      # distinct cameras in this session

    path = relationship(
        "TrackingSightingRecord",
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="TrackingSightingRecord.timestamp",
    )


class TrackingSightingRecord(Base):
    __tablename__ = "tracking_sightings"

    id          = Column(String, primary_key=True, default=_uuid)
    tracking_id = Column(String, ForeignKey("vehicle_tracking.id"), nullable=False, index=True)
    camera_id   = Column(String, nullable=False)
    latitude    = Column(Float, nullable=False)
    longitude   = Column(Float, nullable=False)
    timestamp   = Column(DateTime, server_default=func.now())

    track = relationship("VehicleTrackingRecord", back_populates="path")
