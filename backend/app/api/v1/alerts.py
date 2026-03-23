"""Alerts API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_auth
from app.schemas.alerts import Alert, AlertAck, AlertCreate
from app.schemas.common import Severity

router = APIRouter(prefix="/alerts", tags=["alerts"])

# In-memory alert store; replace with DB
_alerts: list[Alert] = []
_alert_counter = 0


def _next_id() -> str:
    global _alert_counter
    _alert_counter += 1
    return f"alert-{_alert_counter}"


@router.get("", response_model=list[Alert])
async def list_alerts(
    _user=Depends(require_auth),
    severity: Optional[Severity] = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> list[Alert]:
    """List alerts with optional severity filter."""
    out = _alerts.copy()
    if severity:
        out = [a for a in out if a.severity == severity]
    return out[-limit:][::-1]


@router.post("", response_model=Alert, status_code=201)
async def create_alert(
    body: AlertCreate,
    _user=Depends(require_auth),
) -> Alert:
    """Create alert (used by IDS, threat intel, anomaly)."""
    import datetime
    a = Alert(**body.model_dump(), id=_next_id(), created_at=datetime.datetime.utcnow())
    _alerts.append(a)
    return a


@router.patch("/{alert_id}/ack", response_model=Alert)
async def ack_alert(
    alert_id: str,
    body: AlertAck,
    _user=Depends(require_auth),
) -> Alert:
    """Acknowledge alert."""
    import datetime
    for a in _alerts:
        if a.id == alert_id:
            a.acknowledged = body.acknowledged
            a.acknowledged_at = datetime.datetime.utcnow() if body.acknowledged else None
            return a
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Alert not found")
