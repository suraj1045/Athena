"""
Local ANPR Engine (FOSS Architecture)

Replaces SageMaker endpoints with local EasyOCR runs + a placeholder PyTorch classifier.
"""

from __future__ import annotations

import logging
from typing import Any, Tuple

import cv2
import numpy as np

try:
    import easyocr
except ImportError:
    easyocr = Any

from src.common.schemas import ConfidenceScores, VehicleIdentification
from src.config import get_settings


class ANPREngine:
    """Local ANPR engine using EasyOCR for plate reading."""

    def __init__(self, model_path: str | None = None) -> None:
        self.settings = get_settings()
        self.model_path = model_path or self.settings.anpr_model_path
        self._ocr_reader: easyocr.Reader | None = None
        self.logger = logging.getLogger(__name__)

    def _load_model(self) -> None:
        if self._ocr_reader is None:
            self.logger.info("Initializing EasyOCR reader locally")
            # EasyOCR downloads its weights on first run
            gpu = self.settings.environment != "dev"
            self._ocr_reader = easyocr.Reader(['en'], gpu=gpu)

    def process(self, image: np.ndarray, camera_id: str) -> VehicleIdentification | None:
        """
        Read license plate from given crop and return vehicle ID entity.
        """
        self._load_model()

        # Step 1: Image Enhancement for OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Step 2: EasyOCR inference
        results = self._ocr_reader.readtext(gray)
        
        if not results:
            return None
            
        # Results format: [(bounding_box, text, confidence)]
        # We take the highest confidence text block
        best_result = max(results, key=lambda x: x[2])
        bbox, text, conf = best_result
        
        # Clean up output string (remove spaces and special chars)
        clean_plate = ''.join(e for e in text if e.isalnum()).upper()
        
        if float(conf) < self.settings.anpr_confidence_min or len(clean_plate) < 4:
            return None

        # Step 3: Mock/Placeholder for Make/Model Classification
        # In the full free tier, you'd load a local PyTorch ResNet model here
        predicted_make = "Toyota"
        predicted_model = "Corolla"
        make_conf = 0.90
        model_conf = 0.88

        # Step 4: Construct Domain Entity
        return VehicleIdentification(
            license_plate=clean_plate,
            make=predicted_make,
            model=predicted_model,
            color="Silver",  # Placeholder
            camera_id=camera_id,
            confidence=ConfidenceScores(
                plate=float(conf),
                make=make_conf,
                model=model_conf
            )
        )
