"""Alert schemas."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.common import Severity


class AlertCreate(BaseModel):
    """Alert creation payload."""

    title: str
    message: str
    severity: Severity = Severity.MEDIUM
    source: str = "ids"
    device_id: Optional[str] = None
    ip: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class Alert(AlertCreate):
    """Alert with ID and timestamps."""

    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


class AlertAck(BaseModel):
    """Acknowledge alert."""

    acknowledged: bool = True
