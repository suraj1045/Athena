"""
Tests — Edge Anomaly Detector

Tier 1: Validates the on-device motion-stall heuristic.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.edge.anomaly_detector import EdgeAnomalyDetector


class TestEdgeAnomalyDetector:
    def test_no_anomaly_on_first_frame(self) -> None:
        detector = EdgeAnomalyDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.analyze(frame)
        assert result.anomaly_detected is False

    def test_motion_detected_clears_counter(self) -> None:
        detector = EdgeAnomalyDetector(stall_frames=3)
        static_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Feed identical frames
        detector.analyze(static_frame)
        detector.analyze(static_frame.copy())
        detector.analyze(static_frame.copy())

        # Inject a different frame (motion)
        moving_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = detector.analyze(moving_frame)
        assert result.anomaly_detected is False

    def test_stall_detected_after_threshold(self) -> None:
        detector = EdgeAnomalyDetector(motion_threshold=1.0, stall_frames=3)
        static_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        results = []
        for _ in range(5):
            results.append(detector.analyze(static_frame.copy()))

        # Should detect anomaly after stall_frames consecutive still frames
        assert any(r.anomaly_detected for r in results)
        assert any(r.should_escalate for r in results)
