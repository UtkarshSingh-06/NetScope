"""Alert delivery: email, Slack, Discord."""
import asyncio
from typing import Optional

import httpx
from structlog import get_logger

from app.config import get_settings
from app.schemas.alerts import AlertCreate

log = get_logger(__name__)


class AlertingService:
    """Send alerts to configured channels (email, Slack, Discord)."""

    def __init__(self):
        self._settings = get_settings()

    async def send_alert(self, alert: AlertCreate) -> None:
        """Dispatch alert to all configured channels."""
        tasks = []
        if self._settings.slack_webhook_url:
            tasks.append(self._send_slack(alert))
        if self._settings.discord_webhook_url:
            tasks.append(self._send_discord(alert))
        if self._settings.smtp_host and self._settings.alert_email_from:
            tasks.append(self._send_email(alert))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    log.warning("alert_send_failed", error=str(r))

    async def _send_slack(self, alert: AlertCreate) -> None:
        """Send to Slack incoming webhook."""
        color = {"low": "#36a64f", "medium": "#ffcc00", "high": "#ff9900", "critical": "#ff0000"}.get(
            alert.severity.value, "#808080"
        )
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                    ],
                }
            ]
        }
        if alert.ip:
            payload["attachments"][0]["fields"].append({"title": "IP", "value": alert.ip, "short": True})
        async with httpx.AsyncClient() as client:
            r = await client.post(self._settings.slack_webhook_url, json=payload)
            r.raise_for_status()

    async def _send_discord(self, alert: AlertCreate) -> None:
        """Send to Discord webhook."""
        color = {"low": 0x36A64F, "medium": 0xFFCC00, "high": 0xFF9900, "critical": 0xFF0000}.get(
            alert.severity.value, 0x808080
        )
        payload = {
            "embeds": [
                {
                    "title": alert.title,
                    "description": alert.message,
                    "color": color,
                    "fields": [
                        {"name": "Severity", "value": alert.severity.value, "inline": True},
                        {"name": "Source", "value": alert.source, "inline": True},
                    ],
                }
            ]
        }
        if alert.ip:
            payload["embeds"][0]["fields"].append({"name": "IP", "value": alert.ip, "inline": True})
        async with httpx.AsyncClient() as client:
            r = await client.post(self._settings.discord_webhook_url, json=payload)
            r.raise_for_status()

    async def _send_email(self, alert: AlertCreate) -> None:
        """Send email via SMTP (simplified; use aiosmtplib for production)."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["Subject"] = f"[NetScope {alert.severity.value.upper()}] {alert.title}"
        msg["From"] = self._settings.alert_email_from
        body = f"{alert.message}\n\nSeverity: {alert.severity.value}\nSource: {alert.source}"
        if alert.ip:
            body += f"\nIP: {alert.ip}"
        msg.attach(MIMEText(body, "plain"))
        # For async, run in executor
        def _sync_send():
            with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as s:
                s.starttls()
                if self._settings.smtp_user and self._settings.smtp_password:
                    s.login(self._settings.smtp_user, self._settings.smtp_password)
                # Would need recipient list from config
                s.send_message(msg)

        await asyncio.to_thread(_sync_send)
