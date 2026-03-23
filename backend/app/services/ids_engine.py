"""Intrusion detection: port scan, ARP spoofing, MITM detection."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from structlog import get_logger

from app.schemas.alerts import AlertCreate
from app.schemas.common import Severity

log = get_logger(__name__)


@dataclass
class PortScanState:
    """Track connection attempts for port scan detection."""

    src_ip: str
    dst_ports: set[int] = field(default_factory=set)
    conn_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ARPEntry:
    """ARP table entry for spoofing detection."""

    ip: str
    mac: str
    first_seen: datetime = field(default_factory=datetime.utcnow)


class IDSEngine:
    """Rule-based IDS: port scan, ARP spoofing, MITM patterns."""

    def __init__(
        self,
        port_scan_threshold: int = 10,
        port_scan_window_sec: int = 60,
        arp_conflict_window_sec: int = 300,
    ):
        self.port_scan_threshold = port_scan_threshold
        self.port_scan_window = timedelta(seconds=port_scan_window_sec)
        self.arp_conflict_window = timedelta(seconds=arp_conflict_window_sec)
        self._port_scan_tracker: dict[str, PortScanState] = {}
        self._arp_table: dict[str, list[ARPEntry]] = defaultdict(list)
        self._alerts_callback = None

    def set_alerts_callback(self, fn):
        """Set callback for emitting alerts (receives AlertCreate)."""
        self._alerts_callback = fn

    def _emit_alert(self, alert: AlertCreate):
        if self._alerts_callback:
            self._alerts_callback(alert)
        log.warning("ids_alert", **alert.model_dump())

    def on_connection(self, src_ip: str, dst_ip: str, dst_port: int) -> Optional[AlertCreate]:
        """Process new connection; return alert if port scan detected."""
        now = datetime.utcnow()
        key = src_ip
        if key not in self._port_scan_tracker:
            self._port_scan_tracker[key] = PortScanState(src_ip=src_ip)
        state = self._port_scan_tracker[key]
        if now - state.first_seen > self.port_scan_window:
            self._port_scan_tracker[key] = PortScanState(src_ip=src_ip)
            state = self._port_scan_tracker[key]
        state.dst_ports.add(dst_port)
        state.conn_count += 1
        if len(state.dst_ports) >= self.port_scan_threshold or state.conn_count >= self.port_scan_threshold * 2:
            alert = AlertCreate(
                title="Port scan detected",
                message=f"Source {src_ip} probed {len(state.dst_ports)} ports on {dst_ip}",
                severity=Severity.HIGH,
                source="ids",
                ip=src_ip,
                metadata={"dst_ip": dst_ip, "ports": list(state.dst_ports)[:20], "count": state.conn_count},
            )
            self._emit_alert(alert)
            del self._port_scan_tracker[key]
            return alert
        return None

    def on_arp_observation(self, ip: str, mac: str) -> Optional[AlertCreate]:
        """Record ARP observation; alert on IP-MAC conflict (ARP spoofing)."""
        now = datetime.utcnow()
        entries = self._arp_table[ip]
        entries.append(ARPEntry(ip=ip, mac=mac, first_seen=now))
        entries[:] = [e for e in entries if now - e.first_seen < self.arp_conflict_window]
        macs = {e.mac for e in entries}
        if len(macs) > 1:
            alert = AlertCreate(
                title="ARP spoofing suspected",
                message=f"IP {ip} associated with multiple MACs: {macs}",
                severity=Severity.CRITICAL,
                source="ids",
                ip=ip,
                metadata={"macs": list(macs)},
            )
            self._emit_alert(alert)
            return alert
        return None

    def on_mitm_pattern(self, client_ip: str, gateway_ip: str, suspicious_mac: str) -> AlertCreate:
        """Emit alert for potential MITM (client talking to non-gateway MAC for gateway IP)."""
        alert = AlertCreate(
            title="MITM attack suspected",
            message=f"Client {client_ip} gateway traffic to {gateway_ip} via suspicious MAC {suspicious_mac}",
            severity=Severity.CRITICAL,
            source="ids",
            ip=client_ip,
            metadata={"gateway_ip": gateway_ip, "suspicious_mac": suspicious_mac},
        )
        self._emit_alert(alert)
        return alert

    def cleanup(self):
        """Remove stale entries."""
        now = datetime.utcnow()
        self._port_scan_tracker = {
            k: v for k, v in self._port_scan_tracker.items()
            if now - v.first_seen <= self.port_scan_window
        }
        for ip in list(self._arp_table.keys()):
            self._arp_table[ip] = [
                e for e in self._arp_table[ip]
                if now - e.first_seen <= self.arp_conflict_window
            ]
