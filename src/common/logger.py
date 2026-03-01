"""
Athena — Structured JSON Logger

Provides deterministic, structured logging as mandated by
Agent.md § 5 (Resilience & Observability).

Every log entry is a JSON object with:
  - timestamp (ISO 8601)
  - level
  - module
  - message
  - optional context fields (trace_id, camera_id, etc.)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        # Merge any extra context attached to the record
        if hasattr(record, "context") and isinstance(record.context, dict):
            log_entry["context"] = record.context

        # Include traceback on ERROR / CRITICAL
        if record.exc_info and record.exc_info[1]:
            log_entry["traceback"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Return a logger configured with structured JSON output.

    Usage:
        from src.common.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Camera connected", extra={"context": {"camera_id": "cam-012"}})
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
