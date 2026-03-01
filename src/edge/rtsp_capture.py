"""
FOSS Video Capture Agent (Edge)

Captures RTSP streams or local video files and forwards frames to the local
Athena FastAPI backend for processing.

Reference: Agent.md § 2 (Performance First).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import cv2
import requests

from src.config import get_settings


class EdgeRTSPCapture:
    """
    Capture an RTSP stream or local video file and push frames to the backend.

    Parameters
    ----------
    camera_id : str
        Logical camera identifier sent with every frame.
    source : str
        RTSP URL  (e.g. ``rtsp://192.168.1.10:554/stream``) **or**
        local file path  (e.g. ``/data/test_clip.mp4``).
    fps : float
        Target frame rate to forward to the backend (1–30).  Defaults to 5.
    loop : bool
        If *True* and the source is a local file, replay from the start when
        the file ends.  Has no effect on live RTSP streams.
    latitude : float
        Camera geo-location latitude (hardcoded for demo).
    longitude : float
        Camera geo-location longitude (hardcoded for demo).
    """

    def __init__(
        self,
        camera_id: str,
        source: str,
        fps: float = 5.0,
        loop: bool = False,
        latitude: float = 12.9716,
        longitude: float = 77.5946,
    ) -> None:
        self.settings = get_settings()
        self.camera_id = camera_id
        self.source = source
        self.fps = max(0.1, float(fps))
        self.loop = loop
        self.latitude = latitude
        self.longitude = longitude
        self.logger = logging.getLogger(__name__)

        self._is_file = os.path.exists(source)
        self._api_endpoint = (
            f"http://{self.settings.api_host}:{self.settings.api_port}"
            f"/api/v1/ingest/frame"
        )
        self._capture: Optional[cv2.VideoCapture] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Begin the capture-and-transmit loop (blocking)."""
        source_type = "file" if self._is_file else "RTSP stream"
        self.logger.info(f"Opening {source_type}: {self.source}  (target {self.fps} FPS)")

        while True:
            self._capture = cv2.VideoCapture(self.source)
            if not self._capture.isOpened():
                self.logger.error(f"Failed to open {source_type} for camera {self.camera_id}")
                return

            native_fps = self._capture.get(cv2.CAP_PROP_FPS)
            self.logger.info(
                f"[{self.camera_id}] Connected — native {native_fps:.1f} FPS, "
                f"forwarding at {self.fps:.1f} FPS"
            )

            finished = self._run_loop()

            # Loop only makes sense for files; live streams just stop
            if not (self.loop and self._is_file and finished):
                break

            self.logger.info(f"[{self.camera_id}] File ended — looping from start")
            self._cleanup()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _run_loop(self) -> bool:
        """
        Read + transmit frames until the stream ends or KeyboardInterrupt.

        Returns True when the source finished naturally (file EOF), False on interrupt.
        """
        interval = 1.0 / self.fps
        try:
            while self._capture.isOpened():
                ret, frame = self._capture.read()
                if not ret:
                    self.logger.info(f"[{self.camera_id}] Stream/file ended.")
                    return True  # natural EOF

                success, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                )
                if not success:
                    continue

                self._send_frame(buffer.tobytes())
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info(f"[{self.camera_id}] Capture stopped (KeyboardInterrupt).")
            return False
        finally:
            self._cleanup()

        return True

    def _send_frame(self, frame_bytes: bytes) -> None:
        try:
            response = requests.post(
                self._api_endpoint,
                params={
                    "camera_id": self.camera_id,
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                },
                files={"file": ("frame.jpg", frame_bytes, "image/jpeg")},
                timeout=5.0,
            )
            if response.status_code != 202:
                self.logger.error(f"[{self.camera_id}] Backend rejected frame: {response.text}")
        except requests.RequestException as exc:
            self.logger.error(f"[{self.camera_id}] Frame send failed: {exc}")

    def _cleanup(self) -> None:
        if self._capture:
            self._capture.release()
            self._capture = None
