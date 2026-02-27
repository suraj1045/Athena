"""
Athena — Shared Utilities

Pure, stateless helper functions used across multiple services.
Each function targets O(n) or better efficiency (Agent.md § 2).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


def haversine_distance_m(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance in **meters** between two
    GPS coordinates using the Haversine formula.

    Used by the Proximity Engine to compute officer ↔ vehicle distance.
    """
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_degrees(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the initial bearing (forward azimuth) from point 1 to point 2.
    Returns a value in [0, 360).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)

    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - (
        math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def is_approaching(
    vehicle_bearing: float, officer_bearing: float, threshold_deg: float = 45.0
) -> bool:
    """
    Determine if a vehicle is moving *toward* an officer's position.
    Returns True when the angular difference is less than `threshold_deg`.
    """
    diff = abs(vehicle_bearing - officer_bearing) % 360
    if diff > 180:
        diff = 360 - diff
    return diff < threshold_deg


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)
