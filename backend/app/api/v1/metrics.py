"""Metrics API - proxy to Prometheus or return aggregated data."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_auth
from app.services.prometheus_client import PrometheusClient

router = APIRouter(prefix="/metrics", tags=["metrics"])
_prom = PrometheusClient()


@router.get("/connections")
async def get_connections(
    _user=Depends(require_auth),
) -> list[dict]:
    """Fetch connection metrics from Prometheus."""
    return await _prom.get_connection_metrics()


@router.get("/query")
async def query_prometheus(
    expr: str = Query(..., description="PromQL expression"),
    _user=Depends(require_auth),
) -> list[dict]:
    """Execute arbitrary PromQL query."""
    return await _prom.query(expr)


@router.get("/query_range")
async def query_range(
    expr: str = Query(..., description="PromQL expression"),
    start: str = Query(..., description="Start timestamp (RFC3339 or Unix)"),
    end: str = Query(..., description="End timestamp"),
    step: str = Query("15s", description="Query step"),
    _user=Depends(require_auth),
) -> list[dict]:
    """Execute PromQL range query for charting."""
    return await _prom.query_range(expr, start, end, step)
