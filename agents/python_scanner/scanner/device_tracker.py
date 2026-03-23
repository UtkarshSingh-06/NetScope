"""Device tracking: IP, MAC, bandwidth, open ports."""
import asyncio
import platform
import socket
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class DeviceInfo:
    """Discovered device info."""

    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    bandwidth_tx_bps: float = 0.0
    bandwidth_rx_bps: float = 0.0
    open_ports: list[int] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.utcnow)


def get_agent_id() -> str:
    """Unique agent identifier."""
    try:
        return str(uuid.getnode())
    except Exception:
        return platform.node() or "unknown"


def get_local_ip() -> Optional[str]:
    """Get primary local IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


async def discover_local_devices() -> list[DeviceInfo]:
    """Discover devices on local network (simplified - own host + interfaces)."""
    devices = []
    if psutil:
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    devices.append(DeviceInfo(ip=addr.address, hostname=platform.node()))
    else:
        ip = get_local_ip()
        if ip:
            devices.append(DeviceInfo(ip=ip, hostname=platform.node()))
    return devices


async def get_bandwidth_stats() -> tuple[float, float]:
    """Get current tx/rx bytes per second (requires psutil)."""
    if not psutil:
        return 0.0, 0.0
    try:
        net = psutil.net_io_counters()
        await asyncio.sleep(1)
        net2 = psutil.net_io_counters()
        tx_bps = (net2.bytes_sent - net.bytes_sent) / 1.0
        rx_bps = (net2.bytes_recv - net.bytes_recv) / 1.0
        return tx_bps, rx_bps
    except Exception:
        return 0.0, 0.0
