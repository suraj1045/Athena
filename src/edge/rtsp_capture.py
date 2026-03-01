"""
FOSS RTSP Capture Agent (Edge)

Captures RTSP video streams and forwards them to the local Athena FastAPI backend
to be processed, instead of Amazon Kinesis Video Streams.

Reference: Agent.md § 2 (Performance First).
"""

from __future__ import annotations

import logging
import time

import cv2
import requests

from src.config import get_settings


class EdgeRTSPCapture:
    """Capture RTSP stream and push frames to local backend via HTTP."""

    def __init__(self, camera_id: str, rtsp_url: str) -> None:
        self.settings = get_settings()
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.logger = logging.getLogger(__name__)

        # Point to the local FastAPI ingestion endpoint
        self.api_endpoint = f"http://{self.settings.api_host}:{self.settings.api_port}/api/v1/ingest/frame"

        self._capture: cv2.VideoCapture | None = None

    def start(self) -> None:
        """Begin the capture and transmission loop."""
        self.logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
        self._capture = cv2.VideoCapture(self.rtsp_url)

        if not self._capture.isOpened():
            self.logger.error(f"Failed to open RTSP stream for {self.camera_id}")
            return

        fps = self._capture.get(cv2.CAP_PROP_FPS)
        self.logger.info(f"Stream connected at {fps} FPS")

        try:
            while self._capture.isOpened():
                ret, frame = self._capture.read()
                if not ret:
                    self.logger.warning("Dropped frame or stream ended.")
                    break

                # Serialize frame to JPEG for HTTP Transmission
                success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not success:
                    continue

                # In a real FOSS setup, we might write directly to Redis Pub/Sub
                # or send over an intra-network HTTP port to FastAPI.
                try:
                    response = requests.post(
                        self.api_endpoint,
                        params={"camera_id": self.camera_id},
                        files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                        timeout=5.0
                    )

                    if response.status_code != 202:
                        self.logger.error(f"Backend rejected frame: {response.text}")

                except requests.RequestException as e:
                    self.logger.error(f"Failed to send frame to backend: {e}")

                # Rate limiting (e.g. 5 FPS to not overwhelm local REST API)
                time.sleep(0.2)

        except KeyboardInterrupt:
            self.logger.info("Stopping capture (KeyboardInterrupt).")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        if self._capture:
            self.logger.info("Releasing OpenCV capture handle")
            self._capture.release()
