"""
Athena — Navigation API Client

Notifies external traffic APIs (Waze/OSM/mock) when incidents are detected
or cleared. Uses simple HTTP POST with 3 retries for the hackathon demo.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import requests

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# For hackathon: if the real Nav API is unreachable we log but never crash
_TIMEOUT = 4.0


class NavAPIClient:
    """Posts incident events to a Navigation API endpoint."""

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or settings.nav_api_nominatim_url

    def notify_incident(
        self,
        incident_id: str,
        incident_type: str,
        latitude: float,
        longitude: float,
        detected_at: datetime,
    ) -> bool:
        payload = {
            "event": "INCIDENT_DETECTED",
            "incident_id": incident_id,
            "type": incident_type,
            "location": {"latitude": latitude, "longitude": longitude},
            "timestamp": detected_at.isoformat(),
        }
        return self._post_with_retry(payload)

    def notify_incident_cleared(self, incident_id: str) -> bool:
        payload = {
            "event": "INCIDENT_CLEARED",
            "incident_id": incident_id,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
        return self._post_with_retry(payload)

    def _post_with_retry(self, payload: dict) -> bool:
        for attempt in range(3):
            try:
                resp = requests.post(self._endpoint, json=payload, timeout=_TIMEOUT)
                logger.info(
                    f"Nav API [{payload['event']}] → HTTP {resp.status_code}"
                )
                return True
            except requests.RequestException as exc:
                delay = 2 ** attempt
                logger.warning(
                    f"Nav API attempt {attempt + 1}/3 failed: {exc}. "
                    + (f"Retrying in {delay}s…" if attempt < 2 else "Giving up.")
                )
                if attempt < 2:
                    time.sleep(delay)
        return False


# Global singleton
nav_client = NavAPIClient()
