"""Process ingested flows: IDS checks, anomaly scoring, threat intel, alerts."""
import asyncio
from typing import Any

from app.services.ids_engine import IDSEngine
from app.services.anomaly_detector import AnomalyDetector
from app.services.alerting import AlertingService
from app.services.auto_response import AutoResponseService
from app.services.threat_intel import ThreatIntelService
from app.schemas.common import Severity

_ids = IDSEngine()
_anomaly = AnomalyDetector()
_alerting = AlertingService()
_auto_response = AutoResponseService(dry_run=True)
_threat_intel = ThreatIntelService()


def _on_ids_alert(alert):
    asyncio.create_task(_alerting.send_alert(alert))


_ids.set_alerts_callback(_on_ids_alert)


async def process_flow(agent_id: str, flow: dict) -> None:
    """Run IDS, anomaly, and optionally threat intel on a flow."""
    src_ip = flow.get("src_ip")
    dst_ip = flow.get("dst_ip")
    dst_port = flow.get("dst_port", 0)
    if src_ip and dst_ip and dst_port:
        _ids.on_connection(str(src_ip), str(dst_ip), int(dst_port))
    score = await _anomaly.add_sample(flow)
    if score is not None and score > 0.5:
        from app.schemas.alerts import AlertCreate
        a = AlertCreate(
            title="Anomaly detected",
            message=f"Flow {src_ip} -> {dst_ip}:{dst_port} anomaly score {score:.2f}",
            severity=Severity.MEDIUM,
            source="anomaly",
            ip=str(src_ip) if src_ip else None,
            metadata={"score": score, "flow": flow},
        )
        await _alerting.send_alert(a)
