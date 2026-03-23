"""Auto-response: block IPs, terminate connections (iptables/nftables)."""
import asyncio
import platform
import subprocess
from typing import Optional

from structlog import get_logger

log = get_logger(__name__)


class AutoResponseService:
    """Execute response actions: block IP, log only (no-op on Windows)."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._blocked_ips: set[str] = set()

    async def block_ip(self, ip: str, duration_sec: Optional[int] = None) -> bool:
        """Block IP via iptables (Linux) or nft. No-op on Windows or if dry_run."""
        if self.dry_run:
            log.info("auto_response_dry_run", action="block_ip", ip=ip)
            self._blocked_ips.add(ip)
            return True
        if platform.system() != "Linux":
            log.warning("auto_response_unsupported_platform", platform=platform.system())
            self._blocked_ips.add(ip)
            return False
        try:
            cmd = [
                "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP",
            ]
            await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._blocked_ips.add(ip)
            log.info("auto_response_blocked_ip", ip=ip)
            if duration_sec:
                asyncio.create_task(self._unblock_after(ip, duration_sec))
            return True
        except Exception as e:
            log.error("auto_response_block_failed", ip=ip, error=str(e))
            return False

    async def _unblock_after(self, ip: str, duration_sec: int):
        await asyncio.sleep(duration_sec)
        if platform.system() == "Linux" and not self.dry_run:
            try:
                await asyncio.create_subprocess_exec(
                    "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP",
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                self._blocked_ips.discard(ip)
                log.info("auto_response_unblocked_ip", ip=ip)
            except Exception as e:
                log.warning("auto_response_unblock_failed", ip=ip, error=str(e))

    def is_blocked(self, ip: str) -> bool:
        return ip in self._blocked_ips
