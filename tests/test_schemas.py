"""
Tests — Pydantic Schema Validation

Tier 1: Ensures all domain models enforce type constraints correctly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.common.schemas import (
    CaseType,
    ConfidenceScores,
    CriticalVehicle,
    GeoLocation,
    Incident,
    IncidentType,
    InterceptAlert,
    Priority,
    ViolationType,
)


class TestGeoLocation:
    def test_valid_location(self) -> None:
        loc = GeoLocation(latitude=28.6139, longitude=77.2090)
        assert loc.latitude == 28.6139

    def test_invalid_latitude(self) -> None:
        with pytest.raises(ValidationError):
            GeoLocation(latitude=91.0, longitude=0.0)

    def test_invalid_longitude(self) -> None:
        with pytest.raises(ValidationError):
            GeoLocation(latitude=0.0, longitude=181.0)


class TestIncident:
    def test_create_valid_incident(self) -> None:
        incident = Incident(
            type=IncidentType.ACCIDENT,
            location=GeoLocation(latitude=28.6139, longitude=77.2090),
            camera_id="cam-001",
            detected_at=datetime.now(tz=timezone.utc),
            confidence=0.95,
        )
        assert incident.type == IncidentType.ACCIDENT
        assert incident.confidence == 0.95

    def test_confidence_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            Incident(
                type=IncidentType.ACCIDENT,
                location=GeoLocation(latitude=0.0, longitude=0.0),
                camera_id="cam-001",
                detected_at=datetime.now(tz=timezone.utc),
                confidence=1.5,  # Invalid: > 1.0
            )


class TestConfidenceScores:
    def test_valid_scores(self) -> None:
        scores = ConfidenceScores(plate=0.97, make=0.85, model=0.80)
        assert scores.plate == 0.97

    def test_negative_score(self) -> None:
        with pytest.raises(ValidationError):
            ConfidenceScores(plate=-0.1, make=0.5, model=0.5)


class TestInterceptAlert:
    def test_create_alert(self) -> None:
        alert = InterceptAlert(
            officer_id="OFF-001",
            vehicle_plate="MH12AB1234",
            vehicle_make="Maruti",
            vehicle_model="Swift",
            violation_type=ViolationType.EXPIRED_PERMIT,
            location=GeoLocation(latitude=19.0760, longitude=72.8777),
            distance_m=350.0,
            direction="NE",
            estimated_intercept_s=45.0,
            generated_at=datetime.now(tz=timezone.utc),
        )
        assert alert.distance_m == 350.0
        assert alert.status.value == "PENDING"
