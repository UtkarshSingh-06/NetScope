"""NetScope Python scanner agent - reports to central backend."""
import asyncio
import os
import sys
from datetime import datetime

import httpx

# Add parent for imports if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.device_tracker import (
    DeviceInfo,
    discover_local_devices,
    get_agent_id,
    get_bandwidth_stats,
)


BACKEND_URL = os.getenv("NETSCOPE_BACKEND_URL", "http://localhost:8000")
AGENT_TOKEN = os.getenv("NETSCOPE_AGENT_TOKEN", "")


async def report_devices(devices: list[dict]) -> bool:
    """Push device list to backend."""
    if not AGENT_TOKEN:
        return False
    async with httpx.AsyncClient() as client:
        for d in devices:
            try:
                r = await client.post(
                    f"{BACKEND_URL}/api/v1/devices",
                    json=d,
                    headers={"Authorization": f"Bearer {AGENT_TOKEN}"},
                )
                if r.status_code in (200, 201):
                    pass
                else:
                    print(f"Failed to report device: {r.status_code}")
            except Exception as e:
                print(f"Report error: {e}")
                return False
    return True


async def run_once():
    """Single scan cycle."""
    agent_id = get_agent_id()
    devices = await discover_local_devices()
    tx, rx = await get_bandwidth_stats()
    payloads = []
    for d in devices:
        payloads.append({
            "ip": d.ip,
            "mac": d.mac,
            "hostname": d.hostname,
            "agent_id": agent_id,
            "bandwidth_tx_bps": tx,
            "bandwidth_rx_bps": rx,
            "open_ports": d.open_ports,
            "last_seen": datetime.utcnow().isoformat() + "Z",
        })
    if payloads:
        await report_devices(payloads)


async def main():
    """Main loop - scan and report every 30s."""
    print(f"NetScope scanner agent starting, backend={BACKEND_URL}")
    if not AGENT_TOKEN:
        print("Warning: NETSCOPE_AGENT_TOKEN not set; will not push to backend")
    while True:
        try:
            await run_once()
        except Exception as e:
            print(f"Scan error: {e}")
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
