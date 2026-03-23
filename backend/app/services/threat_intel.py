"""Threat intelligence integration: AbuseIPDB, VirusTotal, Shodan."""
import asyncio
from dataclasses import dataclass, field
from typing import Optional

import httpx
from structlog import get_logger

from app.config import get_settings

log = get_logger(__name__)


@dataclass
class ThreatReport:
    """Aggregated threat intelligence report for an IP."""

    ip: str
    risk_score: float = 0.0  # 0-100 composite
    abuseipdb_score: Optional[int] = None
    virustotal_malicious: Optional[int] = None
    shodan_data: Optional[dict] = None
    sources: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


class ThreatIntelService:
    """Lookup IP reputation across AbuseIPDB, VirusTotal, Shodan."""

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def lookup_ip(self, ip: str) -> ThreatReport:
        """Query all configured threat intel sources and compute risk score."""
        report = ThreatReport(ip=ip)
        tasks = []
        if self._settings.abuseipdb_api_key:
            tasks.append(self._abuseipdb_lookup(ip, report))
        if self._settings.virustotal_api_key:
            tasks.append(self._virustotal_lookup(ip, report))
        if self._settings.shodan_api_key:
            tasks.append(self._shodan_lookup(ip, report))
        if tasks:
            await asyncio.gather(*tasks)
            report.risk_score = self._compute_risk(report)
        return report

    async def _abuseipdb_lookup(self, ip: str, report: ThreatReport):
        """Query AbuseIPDB."""
        client = await self._client_get()
        url = "https://api.abuseipdb.com/api/v2/check"
        try:
            r = await client.get(
                url,
                params={"ipAddress": ip, "maxAgeInDays": 90},
                headers={"Key": self._settings.abuseipdb_api_key, "Accept": "application/json"},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                report.abuseipdb_score = score
                report.sources.append("abuseipdb")
                report.raw["abuseipdb"] = data
        except Exception as e:
            log.warning("abuseipdb_lookup_failed", ip=ip, error=str(e))

    async def _virustotal_lookup(self, ip: str, report: ThreatReport):
        """Query VirusTotal IP report."""
        client = await self._client_get()
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        try:
            r = await client.get(
                url,
                headers={"x-apikey": self._settings.virustotal_api_key},
            )
            if r.status_code == 200:
                data = r.json().get("data", {}).get("attributes", {})
                stats = data.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                report.virustotal_malicious = malicious
                report.sources.append("virustotal")
                report.raw["virustotal"] = data
        except Exception as e:
            log.warning("virustotal_lookup_failed", ip=ip, error=str(e))

    async def _shodan_lookup(self, ip: str, report: ThreatReport):
        """Query Shodan host info."""
        client = await self._client_get()
        url = f"https://api.shodan.io/shodan/host/{ip}"
        try:
            r = await client.get(url, params={"key": self._settings.shodan_api_key})
            if r.status_code == 200:
                data = r.json()
                report.shodan_data = {
                    "ports": data.get("ports", []),
                    "vulns": data.get("vulns", []),
                    "tags": data.get("tags", []),
                    "org": data.get("org"),
                }
                report.sources.append("shodan")
                report.raw["shodan"] = data
        except Exception as e:
            log.warning("shodan_lookup_failed", ip=ip, error=str(e))

    def _compute_risk(self, report: ThreatReport) -> float:
        """Compute composite risk score 0-100."""
        scores = []
        if report.abuseipdb_score is not None:
            scores.append(report.abuseipdb_score * 0.5)  # AbuseIPDB 0-100
        if report.virustotal_malicious is not None:
            vt_score = min(100, report.virustotal_malicious * 10)
            scores.append(vt_score * 0.3)
        if report.shodan_data:
            vulns = len(report.shodan_data.get("vulns", []))
            shodan_score = min(100, vulns * 20)
            scores.append(shodan_score * 0.2)
        if not scores:
            return 0.0
        return min(100.0, sum(scores))
