"""Device and flow schemas for network observability."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class DeviceBase(BaseModel):
    """Base device attributes."""

    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None


class DeviceCreate(DeviceBase):
    """Device creation payload from agents."""

    agent_id: str
    bandwidth_tx_bps: Optional[float] = 0.0
    bandwidth_rx_bps: Optional[float] = 0.0
    open_ports: Optional[list[int]] = []
    last_seen: Optional[datetime] = None


class Device(DeviceBase):
    """Device with computed fields."""

    id: str
    agent_id: str
    status: DeviceStatus = DeviceStatus.UNKNOWN
    bandwidth_tx_bps: float = 0.0
    bandwidth_rx_bps: float = 0.0
    open_ports: list[int] = []
    risk_score: Optional[float] = None
    trust_score: Optional[float] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None


class FlowRecord(BaseModel):
    """Network flow record (5-tuple + metrics)."""

    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str = "tcp"
    bytes_sent: int = 0
    bytes_recv: int = 0
    retrans_count: int = 0
    rtt_avg_ms: Optional[float] = None
    drop_count: int = 0
    node: Optional[str] = None
    pod: Optional[str] = None
    namespace: Optional[str] = None
    timestamp: Optional[datetime] = None


class FlowBatch(BaseModel):
    """Batch of flows from agent."""

    agent_id: str
    flows: list[FlowRecord]
