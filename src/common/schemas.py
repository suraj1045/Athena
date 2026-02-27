"""
Athena — Pydantic Domain Schemas

Strict type-safe data models for every data boundary (API, DB, events).
Reference: Agent.md § 3 — ENTERPRISE-GRADE PYTHON (Validation Layers)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class IncidentType(str, Enum):
    STALLED_VEHICLE = "STALLED_VEHICLE"
    BREAKDOWN = "BREAKDOWN"
    ACCIDENT = "ACCIDENT"
    PEDESTRIAN_VIOLATION = "PEDESTRIAN_VIOLATION"
    NONE = "NONE"


class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLEARED = "CLEARED"


class CaseType(str, Enum):
    KIDNAPPING = "KIDNAPPING"
    HIT_AND_RUN = "HIT_AND_RUN"
    STOLEN = "STOLEN"


class VehicleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class Priority(str, Enum):
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ViolationType(str, Enum):
    EXPIRED_PERMIT = "EXPIRED_PERMIT"
    UNPAID_FINE = "UNPAID_FINE"
    SUSPENDED_REGISTRATION = "SUSPENDED_REGISTRATION"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlertStatus(str, Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    EXPIRED = "EXPIRED"


# ─── Value Objects ────────────────────────────────────────────────────────────

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class ConfidenceScores(BaseModel):
    plate: float = Field(..., ge=0.0, le=1.0)
    make: float = Field(..., ge=0.0, le=1.0)
    model: float = Field(..., ge=0.0, le=1.0)


class S3Reference(BaseModel):
    s3_bucket: str
    s3_key: str
    duration_s: Optional[float] = None


# ─── Domain Models ────────────────────────────────────────────────────────────

class Incident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    type: IncidentType
    location: GeoLocation
    camera_id: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    cleared_at: Optional[datetime] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: IncidentStatus = IncidentStatus.ACTIVE
    bounding_box: Optional[BoundingBox] = None
    video_segment: Optional[S3Reference] = None


class VehicleIdentification(BaseModel):
    identification_id: UUID = Field(default_factory=uuid4)
    license_plate: str
    make: str
    model: str
    color: Optional[str] = None
    location: Optional[GeoLocation] = None
    camera_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: ConfidenceScores
    image_ref: Optional[S3Reference] = None


class CriticalVehicle(BaseModel):
    vehicle_id: UUID = Field(default_factory=uuid4)
    license_plate: str
    make: str
    model: str
    case_type: CaseType
    case_number: str
    priority: Priority = Priority.HIGH
    status: VehicleStatus = VehicleStatus.ACTIVE
    registered_at: datetime
    registered_by: str


class ViolationVehicle(BaseModel):
    license_plate: str
    violation_type: ViolationType
    description: str
    severity: Severity = Severity.LOW
    added_at: datetime


class OfficerLocation(BaseModel):
    officer_id: str
    location: GeoLocation
    heading: float = Field(..., ge=0.0, lt=360.0)
    speed_mps: float = Field(default=0.0, ge=0.0)
    on_duty: bool = True
    last_updated: datetime


class InterceptAlert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    officer_id: str
    vehicle_plate: str
    vehicle_make: str
    vehicle_model: str
    violation_type: ViolationType
    location: GeoLocation
    distance_m: float
    direction: str
    estimated_intercept_s: float
    generated_at: datetime
    acknowledged_at: Optional[datetime] = None
    status: AlertStatus = AlertStatus.PENDING
