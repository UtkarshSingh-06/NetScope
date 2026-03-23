"""Threat intelligence API."""
from fastapi import APIRouter, Depends

from app.core.deps import require_auth
from app.services.threat_intel import ThreatIntelService, ThreatReport

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])
_threat_intel = ThreatIntelService()


@router.get("/lookup/{ip}")
async def lookup_ip(
    ip: str,
    _user=Depends(require_auth),
) -> dict:
    """Lookup IP across AbuseIPDB, VirusTotal, Shodan and return risk score."""
    report = await _threat_intel.lookup_ip(ip)
    return {
        "ip": report.ip,
        "risk_score": report.risk_score,
        "abuseipdb_score": report.abuseipdb_score,
        "virustotal_malicious": report.virustotal_malicious,
        "shodan": report.shodan_data,
        "sources": report.sources,
    }
