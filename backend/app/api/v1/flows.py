"""Flows API - receive and serve flow data from agents."""
from collections import deque
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_auth
from app.schemas.devices import FlowBatch, FlowRecord

router = APIRouter(prefix="/flows", tags=["flows"])
_flow_buffer: deque = deque(maxlen=10000)


@router.post("/batch", status_code=202)
async def ingest_flows(
    body: FlowBatch,
    _user=Depends(require_auth),
) -> dict:
    """Ingest flow batch from agent. Runs IDS and anomaly detection."""
    from app.services.flow_processor import process_flow

    for f in body.flows:
        fd = f.model_dump()
        _flow_buffer.append((body.agent_id, fd))
        await process_flow(body.agent_id, fd)
    return {"accepted": len(body.flows)}


@router.get("", response_model=list[dict])
async def list_flows(
    _user=Depends(require_auth),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List recent flows (from buffer)."""
    items = list(_flow_buffer)[-limit:][::-1]
    return [{"agent_id": a, **f} for a, f in items]
