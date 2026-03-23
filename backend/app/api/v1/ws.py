"""WebSocket endpoint for real-time streaming."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.websocket.manager import ConnectionManager

router = APIRouter(tags=["websocket"])
_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None, description="Optional JWT for authenticated clients"),
):
    """Live stream: devices, flows, alerts, metrics."""
    await websocket.accept()
    await _manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or handle client commands (e.g. subscribe to specific channels)
            # For now, we just keep connection alive; server pushes via broadcast
            pass
    except WebSocketDisconnect:
        await _manager.disconnect(websocket)


def get_ws_manager() -> ConnectionManager:
    return _manager
