"""Prometheus HTTP API client for fetching metrics."""
from typing import Any, Optional

import httpx
from structlog import get_logger

from app.config import get_settings

log = get_logger(__name__)


class PrometheusClient:
    """Query Prometheus for network metrics."""

    def __init__(self):
        self._base = get_settings().prometheus_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def query(self, expr: str) -> list[dict]:
        """Execute PromQL and return parsed result."""
        client = await self._client_get()
        try:
            r = await client.get(f"{self._base}/api/v1/query", params={"query": expr})
            r.raise_for_status()
            data = r.json()
            if data.get("status") != "success":
                return []
            result = data.get("data", {}).get("result", [])
            return result
        except Exception as e:
            log.warning("prometheus_query_failed", expr=expr, error=str(e))
            return []

    async def query_range(self, expr: str, start: str, end: str, step: str = "15s") -> list[dict]:
        """Execute range query for charting."""
        client = await self._client_get()
        try:
            r = await client.get(
                f"{self._base}/api/v1/query_range",
                params={"query": expr, "start": start, "end": end, "step": step},
            )
            r.raise_for_status()
            data = r.json()
            if data.get("status") != "success":
                return []
            return data.get("data", {}).get("result", [])
        except Exception as e:
            log.warning("prometheus_range_query_failed", expr=expr, error=str(e))
            return []

    async def get_connection_metrics(self) -> list[dict]:
        """Fetch TCP connection metrics from NetScope agent."""
        return await self.query("network_observability_tcp_bytes_sent_total")
