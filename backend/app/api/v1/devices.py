"""Device API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import require_auth
from app.schemas.devices import Device, DeviceCreate
from app.services.device_store import DeviceStore

router = APIRouter(prefix="/devices", tags=["devices"])

# Module-level store; in production use dependency injection with DB/Redis
_store = DeviceStore()


@router.get("", response_model=list[Device])
async def list_devices(
    _user=Depends(require_auth),
) -> list[Device]:
    """List all discovered devices."""
    return _store.list_all()


@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    _user=Depends(require_auth),
) -> Device:
    """Get device by ID."""
    d = _store.get(device_id)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return d


@router.post("", response_model=Device, status_code=201)
async def register_device(
    body: DeviceCreate,
    _user=Depends(require_auth),
) -> Device:
    """Register or update device (from agent)."""
    return _store.upsert(body)
