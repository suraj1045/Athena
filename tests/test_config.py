"""
Tests — Configuration Loading

Tier 1: Validates that the SSoT config loads correctly from
environment variables and applies defaults.
"""

from __future__ import annotations

import os

import pytest

from src.config import AthenaSettings, Environment, LogLevel


class TestAthenaSettings:
    def test_defaults(self) -> None:
        """Settings should load with sensible defaults when no env vars are set."""
        settings = AthenaSettings()
        assert settings.environment == Environment.DEV
        assert settings.log_level == LogLevel.INFO
        assert settings.aws_region == "ap-south-1"
        assert settings.proximity_radius_m == 500.0
        assert settings.data_retention_days == 90

    def test_override_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables should override defaults."""
        monkeypatch.setenv("ATHENA_ENVIRONMENT", "production")
        monkeypatch.setenv("ATHENA_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ATHENA_PROXIMITY_RADIUS_M", "750")

        settings = AthenaSettings()
        assert settings.environment == Environment.PRODUCTION
        assert settings.log_level == LogLevel.DEBUG
        assert settings.proximity_radius_m == 750.0
