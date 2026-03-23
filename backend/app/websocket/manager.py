"""WebSocket connection manager for real-time streaming."""
import asyncio
import json
from typing import Any, Optional

from structlog import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcast events."""

    def __init__(self):
        self._connections: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws) -> None:
        """Register new WebSocket connection."""
        async with self._lock:
            self._connections.add(ws)
        log.info("websocket_connected", total=len(self._connections))

    async def disconnect(self, ws) -> None:
        """Remove WebSocket connection."""
        async with self._lock:
            self._connections.discard(ws)
        log.info("websocket_disconnected", total=len(self._connections))

    async def broadcast(self, event_type: str, payload: dict) -> None:
        """Broadcast event to all connected clients."""
        msg = {"type": event_type, "payload": payload}
        data = json.dumps(msg, default=str)
        async with self._lock:
            conns = list(self._connections)
        dead = []
        for ws in conns:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def broadcast_device(self, device: dict) -> None:
        """Broadcast device update."""
        await self.broadcast("device", device)

    async def broadcast_flow(self, flow: dict) -> None:
        """Broadcast flow update."""
        await self.broadcast("flow", flow)

    async def broadcast_alert(self, alert: dict) -> None:
        """Broadcast alert."""
        await self.broadcast("alert", alert)

    async def broadcast_metrics(self, metrics: dict) -> None:
        """Broadcast aggregate metrics snapshot."""
        await self.broadcast("metrics", metrics)
