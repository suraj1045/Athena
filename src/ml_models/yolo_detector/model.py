"""
Local YOLOv8 Detector Wrapper (FOSS Architecture)

Replaces the SageMaker client implementation with a direct, local PyTorch
inference wrapper using the ultralytics library.

Reference: Agent.md § 2 (Performance First) — local VRAM usage.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

# We lazy-load YOLO to keep the import fast, but keep the import type check
try:
    from ultralytics import YOLO
except ImportError:
    YOLO = Any

from src.common.schemas import BoundingBox, GeoLocation, Incident, IncidentType
from src.config import get_settings


class YOLODetector:
    """Wrapper for local Ultralytics YOLO inference."""

    def __init__(self, model_path: str | None = None) -> None:
        self.settings = get_settings()
        self.model_path = model_path or self.settings.yolo_model_path
        self._model: YOLO | None = None
        self.logger = logging.getLogger(__name__)

    def _load_model(self) -> None:
        if self._model is None:
            self.logger.info(f"Loading local YOLO model from {self.model_path}")
            # Requires `pip install ultralytics`
            self._model = YOLO(self.model_path)
            # Send to GPU if available, else CPU
            self._model.to('cuda' if self.settings.environment != "dev" else 'cpu')

    def detect(self, frame: np.ndarray, camera_id: str, location: GeoLocation) -> list[Incident]:
        """
        Run inference on a single frame and return a list of Incidents.
        """
        self._load_model()

        # YOLOv8 returns a list of Results objects
        results = self._model(
            frame,
            conf=self.settings.detection_confidence_min,
            verbose=False
        )

        incidents: list[Incident] = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # box.xyxy: [xmin, ymin, xmax, ymax]
                # box.conf: confidence score
                # box.cls: class ID
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # We map class IDs to our domain 'IncidentType'.
                # E.g., class 0 might be person, 2 car, etc in COCO
                incident_type = self._map_class_to_incident(cls_id)
                if incident_type is None:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                incident = Incident(
                    type=incident_type,
                    location=location,
                    camera_id=camera_id,
                    confidence=conf,
                    bounding_box=BoundingBox(
                        x_min=float(x1),
                        y_min=float(y1),
                        x_max=float(x2),
                        y_max=float(y2)
                    )
                )
                incidents.append(incident)

        return incidents

    def _map_class_to_incident(self, class_id: int) -> IncidentType | None:
        """Map raw YOLO class IDs to our domain enum."""
        # This is a placeholder mapping based on COCO defaults.
        # Should be updated based on the actual trained model outputs.
        # Example: 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
        if class_id in [2, 3, 5, 7]:
            return IncidentType.STALLED_VEHICLE  # Generic placeholder mapping
        if class_id == 0:
            return IncidentType.PEDESTRIAN_VIOLATION
        return None
