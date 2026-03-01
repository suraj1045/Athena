"""
Athena ML — YOLO Training Pipeline

Orchestrates model training, validation, and artifact export for
the YOLOv8 vehicle detection model.

Training data is expected in COCO format under:
    data/training/yolo/images/
    data/training/yolo/labels/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrainingConfig:
    """Hyperparameters and paths for a training run."""
    data_dir: Path
    output_dir: Path
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.01
    pretrained_weights: str | None = "yolov8n.pt"
    device: str = "cuda:0"


def train(config: TrainingConfig) -> Path:
    """
    Launch a YOLO training run.

    Returns:
        Path to the best exported model weights.
    """
    logger.info("Starting YOLO training", extra={"context": {
        "data_dir": str(config.data_dir),
        "epochs": config.epochs,
        "batch_size": config.batch_size,
    }})

    # TODO: Integrate ultralytics YOLO training API
    #   from ultralytics import YOLO
    #   model = YOLO(config.pretrained_weights)
    #   model.train(data=str(config.data_dir / "data.yaml"), ...)

    best_weights = config.output_dir / "weights" / "best.pt"
    logger.info("Training complete", extra={"context": {"weights": str(best_weights)}})
    return best_weights


def export_onnx(weights_path: Path, output_path: Path) -> Path:
    """Export trained YOLO weights to ONNX for SageMaker deployment."""
    logger.info("Exporting to ONNX", extra={"context": {"source": str(weights_path)}})
    # TODO: model.export(format="onnx")
    onnx_path = output_path / "model.onnx"
    return onnx_path
