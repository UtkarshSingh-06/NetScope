"""Aggregate API v1 routes."""
from fastapi import APIRouter

from app.api.v1 import agents, alerts, auth, devices, flows, metrics, threat_intel, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(agents.router)
api_router.include_router(devices.router)
api_router.include_router(flows.router)
api_router.include_router(alerts.router)
api_router.include_router(threat_intel.router)
api_router.include_router(metrics.router)
api_router.include_router(ws.router)
