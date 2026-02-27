"""
Tests — Common Utilities (Haversine, bearing, approach detection)

Tier 1: Logic sandbox — verifies pure utility functions.
"""

from __future__ import annotations

import math

import pytest

from src.common.utils import bearing_degrees, haversine_distance_m, is_approaching


class TestHaversineDistance:
    """Verify great-circle distance calculations."""

    def test_same_point_returns_zero(self) -> None:
        assert haversine_distance_m(28.6139, 77.2090, 28.6139, 77.2090) == 0.0

    def test_known_distance_delhi_to_mumbai(self) -> None:
        """Delhi (28.6139°N, 77.2090°E) → Mumbai (19.0760°N, 72.8777°E) ≈ 1,148 km."""
        dist = haversine_distance_m(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1_140_000 < dist < 1_160_000  # within 10 km tolerance

    def test_short_distance(self) -> None:
        """Two points ~111m apart (0.001° latitude at equator)."""
        dist = haversine_distance_m(0.0, 0.0, 0.001, 0.0)
        assert 100 < dist < 120


class TestBearing:
    """Verify bearing calculation between two coordinates."""

    def test_due_north(self) -> None:
        bearing = bearing_degrees(0.0, 0.0, 1.0, 0.0)
        assert abs(bearing - 0.0) < 1.0  # ~0° (North)

    def test_due_east(self) -> None:
        bearing = bearing_degrees(0.0, 0.0, 0.0, 1.0)
        assert abs(bearing - 90.0) < 1.0  # ~90° (East)

    def test_due_south(self) -> None:
        bearing = bearing_degrees(1.0, 0.0, 0.0, 0.0)
        assert abs(bearing - 180.0) < 1.0  # ~180° (South)


class TestIsApproaching:
    """Verify approach detection logic."""

    def test_directly_approaching(self) -> None:
        assert is_approaching(180.0, 180.0, 45.0) is True

    def test_moving_away(self) -> None:
        assert is_approaching(0.0, 180.0, 45.0) is False

    def test_edge_of_threshold(self) -> None:
        assert is_approaching(180.0, 136.0, 45.0) is True   # diff = 44°
        assert is_approaching(180.0, 134.0, 45.0) is False  # diff = 46°

    def test_wrap_around_360(self) -> None:
        """350° and 10° are only 20° apart."""
        assert is_approaching(350.0, 10.0, 45.0) is True
