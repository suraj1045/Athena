"""
Athena Edge — Greengrass Component Deployment Config

Defines the AWS IoT Greengrass v2 component recipe for deploying
the edge anomaly detector and RTSP capture agent on local hardware.
"""

from __future__ import annotations

GREENGRASS_RECIPE: dict = {
    "RecipeFormatVersion": "2020-01-25",
    "ComponentName": "com.athena.EdgeProcessor",
    "ComponentVersion": "1.0.0",
    "ComponentDescription": "Athena edge processing — RTSP capture + local anomaly detection",
    "ComponentPublisher": "Athena AI",
    "Manifests": [
        {
            "Platform": {"os": "linux"},
            "Lifecycle": {
                "Install": "pip install -r {artifacts:path}/requirements-edge.txt",
                "Run": "python -m src.edge.rtsp_capture --camera-url $CAMERA_URL",
            },
            "Artifacts": [
                {"URI": "s3://athena-edge-artifacts/edge-processor-1.0.0.zip", "Unarchive": "ZIP"}
            ],
        }
    ],
}
