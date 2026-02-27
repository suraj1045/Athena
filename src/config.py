"""
Athena Configuration — Single Source of Truth (SSoT)

All application-wide settings, feature toggles, model parameters,
and environment-specific values are centralized here using pydantic-settings.
Secrets are loaded from `.env` files and NEVER hardcoded.

Now updated for the 100% Free & Open-Source (FOSS) architectural stack.
Reference: Agent.md § 1 — THE ARCHITECTURAL CORE (SSoT)
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─── Enums ────────────────────────────────────────────────────────────────────

class Environment(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ─── Core Application Settings ───────────────────────────────────────────────

class AthenaSettings(BaseSettings):
    """Global configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ATHENA_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──────────────────────────────────────────────────────────────
    environment: Environment = Field(default=Environment.DEV)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    debug: bool = Field(default=True)

    # ── API Server ───────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # ── Database (PostgreSQL) ────────────────────────────────────────────────
    db_user: str = Field(default="athena")
    db_password: str = Field(default="athena_secret")
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="athena_db")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # ── PubSub / Queue (Redis) ───────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── Object Storage (MinIO) ───────────────────────────────────────────────
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="athena_minio_admin")
    minio_secret_key: str = Field(default="athena_minio_secret")
    minio_secure: bool = Field(default=False)
    minio_video_bucket: str = Field(default="athena-video-archive")
    minio_frames_bucket: str = Field(default="athena-raw-frames")

    # ── Model Paths ──────────────────────────────────────────────────────────
    yolo_model_path: str = Field(default="data/models/yolo/yolov8n.pt")
    anpr_model_path: str = Field(default="data/models/anpr/best.pt")

    # ── Detection Thresholds ─────────────────────────────────────────────────
    detection_confidence_min: float = Field(default=0.85)
    anpr_confidence_min: float = Field(default=0.90)
    incident_detection_interval_s: float = Field(default=1.0)  # 1 FPS

    # ── Proximity Engine ─────────────────────────────────────────────────────
    proximity_radius_m: float = Field(default=500.0)
    proximity_scan_radius_m: float = Field(default=1000.0)
    proximity_approach_angle_deg: float = Field(default=45.0)
    proximity_alert_cooldown_s: int = Field(default=30)

    # ── Navigation APIs ──────────────────────────────────────────────────────
    nav_api_nominatim_url: str = Field(default="https://nominatim.openstreetmap.org/search")


# ─── Singleton accessor ──────────────────────────────────────────────────────

_settings: Optional[AthenaSettings] = None


def get_settings() -> AthenaSettings:
    """Return the cached global settings instance (lazy-loaded)."""
    global _settings
    if _settings is None:
        _settings = AthenaSettings()
    return _settings
