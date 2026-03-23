"""In-memory device store with TTL (replace with Redis/DB in production)."""
from datetime import datetime, timedelta
from typing import Optional

from app.schemas.devices import Device, DeviceCreate, DeviceStatus


class DeviceStore:
    """Store devices; compute status from last_seen."""

    def __init__(self, offline_threshold_sec: int = 120):
        self._devices: dict[str, Device] = {}
        self._offline_threshold = timedelta(seconds=offline_threshold_sec)

    def _make_id(self, ip: str, agent_id: str) -> str:
        return f"{agent_id}:{ip}"

    def upsert(self, d: DeviceCreate) -> Device:
        """Insert or update device."""
        did = self._make_id(d.ip, d.agent_id)
        now = datetime.utcnow()
        last = d.last_seen or now
        status = DeviceStatus.ONLINE if (now - last) < self._offline_threshold else DeviceStatus.OFFLINE
        existing = self._devices.get(did)
        created = existing.created_at if existing else now
        device = Device(
            id=did,
            ip=d.ip,
            mac=d.mac,
            hostname=d.hostname,
            vendor=d.vendor,
            agent_id=d.agent_id,
            status=status,
            bandwidth_tx_bps=d.bandwidth_tx_bps or 0.0,
            bandwidth_rx_bps=d.bandwidth_rx_bps or 0.0,
            open_ports=d.open_ports or [],
            last_seen=last,
            created_at=created,
        )
        self._devices[did] = device
        return device

    def get(self, device_id: str) -> Optional[Device]:
        return self._devices.get(device_id)

    def list_all(self) -> list[Device]:
        """Return all devices (refresh status)."""
        now = datetime.utcnow()
        for d in self._devices.values():
            if d.last_seen and (now - d.last_seen) > self._offline_threshold:
                d.status = DeviceStatus.OFFLINE
            elif d.last_seen:
                d.status = DeviceStatus.ONLINE
        return list(self._devices.values())

    def update_risk(self, device_id: str, risk_score: float) -> None:
        if device_id in self._devices:
            self._devices[device_id].risk_score = risk_score

    def update_trust(self, device_id: str, trust_score: float) -> None:
        if device_id in self._devices:
            self._devices[device_id].trust_score = trust_score
