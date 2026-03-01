"""
Athena — Event Schemas

Pydantic models for all inter-service events published through SNS / EventBridge.
These form the canonical contract between microservices.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.common.schemas import (
    CaseType,
    GeoLocation,
    IncidentType,
    Priority,
    ViolationType,
)


class BaseEvent(BaseModel):
    """Common envelope for all Athena events."""
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    source: str = "athena"


class StreamConnectedEvent(BaseEvent):
    event_type: str = "StreamConnected"
    camera_id: str
    stream_quality: str | None = None


class StreamDisconnectedEvent(BaseEvent):
    event_type: str = "StreamDisconnected"
    camera_id: str
    reason: str


class IncidentDetectedEvent(BaseEvent):
    event_type: str = "IncidentDetected"
    incident_id: UUID
    incident_type: IncidentType
    location: GeoLocation
    camera_id: str
    confidence: float


class IncidentClearedEvent(BaseEvent):
    event_type: str = "IncidentCleared"
    incident_id: UUID
    camera_id: str


class VehicleIdentifiedEvent(BaseEvent):
    event_type: str = "VehicleIdentified"
    identification_id: UUID
    license_plate: str
    make: str
    model: str
    location: GeoLocation
    camera_id: str
    confidence: float


class CriticalVehicleDetectedEvent(BaseEvent):
    event_type: str = "CriticalVehicleDetected"
    vehicle_id: UUID
    sighting_id: UUID
    location: GeoLocation
    camera_id: str
    case_type: CaseType
    priority: Priority


class InterceptAlertGeneratedEvent(BaseEvent):
    event_type: str = "InterceptAlertGenerated"
    officer_id: str
    vehicle_plate: str
    violation_type: ViolationType
    distance_m: float
    direction: str
    estimated_intercept_s: float
