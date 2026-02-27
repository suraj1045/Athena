"""
Athena Edge — Local Anomaly Detector

A lightweight anomaly detector running on-premise (Greengrass / Outposts)
for ultra-low-latency critical alerts before full cloud inference completes.

Performs fast, coarse-grained checks (motion delta, vehicle stall heuristics)
and escalates to SageMaker only when the local confidence threshold is met.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.common.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class LocalDetection:
    """Result of the on-device anomaly check."""
    anomaly_detected: bool
    anomaly_type: Optional[str] = None  # "MOTION_STOP" | "SUDDEN_DENSITY"
    confidence: float = 0.0
    should_escalate: bool = False


class EdgeAnomalyDetector:
    """
    Stateful detector that compares consecutive frames for
    rapid, heuristic-based anomaly signals.
    """

    def __init__(self, motion_threshold: float = 0.02, stall_frames: int = 5) -> None:
        self._motion_threshold = motion_threshold
        self._stall_frames = stall_frames
        self._prev_frame: Optional[np.ndarray] = None
        self._consecutive_still: int = 0

    def analyze(self, frame: np.ndarray) -> LocalDetection:
        """
        Compare `frame` to the previous frame.  If motion is below
        threshold for N consecutive frames, flag a potential stall.
        """
        if self._prev_frame is None:
            self._prev_frame = frame
            return LocalDetection(anomaly_detected=False)

        diff = np.mean(np.abs(frame.astype(float) - self._prev_frame.astype(float)))
        self._prev_frame = frame

        if diff < self._motion_threshold:
            self._consecutive_still += 1
        else:
            self._consecutive_still = 0

        if self._consecutive_still >= self._stall_frames:
            logger.info(
                "Edge anomaly: motion stall detected",
                extra={"context": {"consecutive_still": self._consecutive_still}},
            )
            return LocalDetection(
                anomaly_detected=True,
                anomaly_type="MOTION_STOP",
                confidence=min(self._consecutive_still / (self._stall_frames * 2), 1.0),
                should_escalate=True,
            )

        return LocalDetection(anomaly_detected=False)
