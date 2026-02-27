"""
Athena — WebSocket Connection Manager

Manages real-time WebSocket connections for:
  - Officer App (receives intercept alerts per officer_id)
  - Control Dashboard (receives all incident + critical vehicle events)

Provides both async methods (for WebSocket endpoints) and
sync-safe methods (for calling from background pipeline threads).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Central hub for all active WebSocket connections."""

    def __init__(self) -> None:
        self.officer_connections: Dict[str, WebSocket] = {}
        self.control_connections: Dict[str, WebSocket] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called at startup to capture the running event loop."""
        self._loop = loop

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect_officer(self, websocket: WebSocket, officer_id: str) -> None:
        await websocket.accept()
        self.officer_connections[officer_id] = websocket
        logger.info(f"Officer {officer_id} connected via WebSocket")

    async def connect_control(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.control_connections[client_id] = websocket
        logger.info(f"Control client {client_id} connected")

    def disconnect_officer(self, officer_id: str) -> None:
        self.officer_connections.pop(officer_id, None)

    def disconnect_control(self, client_id: str) -> None:
        self.control_connections.pop(client_id, None)

    # ── Async send (for use inside async endpoint handlers) ──────────────────

    async def send_to_officer(self, officer_id: str, data: dict) -> None:
        ws = self.officer_connections.get(officer_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as exc:
                logger.warning(f"Officer WS send failed ({officer_id}): {exc}")
                self.disconnect_officer(officer_id)

    async def broadcast_to_control(self, data: dict) -> None:
        for cid in list(self.control_connections.keys()):
            ws = self.control_connections.get(cid)
            if ws:
                try:
                    await ws.send_json(data)
                except Exception as exc:
                    logger.warning(f"Control WS send failed ({cid}): {exc}")
                    self.disconnect_control(cid)

    # ── Sync-safe sends (called from worker threads in pipeline) ─────────────

    def send_to_officer_sync(self, officer_id: str, data: dict) -> None:
        """Fire-and-forget from a sync thread."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_to_officer(officer_id, data), self._loop
            )

    def broadcast_to_control_sync(self, data: dict) -> None:
        """Fire-and-forget from a sync thread."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast_to_control(data), self._loop
            )


# Global singleton shared across the entire app
ws_manager = ConnectionManager()
