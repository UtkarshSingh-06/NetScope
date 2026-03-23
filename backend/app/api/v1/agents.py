"""Agent registration and management."""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.core.deps import require_auth
from app.config import get_settings

router = APIRouter(prefix="/agents", tags=["agents"])

_registered_agents: dict[str, dict] = {}


class AgentRegister(BaseModel):
    agent_id: str


@router.post("/register")
async def register_agent(
    body: AgentRegister,
    _user=Depends(require_auth),
    x_agent_token: str | None = Header(None),
):
    """Register scanning agent with central server."""
    settings = get_settings()
    if settings.agent_registration_token and x_agent_token != settings.agent_registration_token:
        raise HTTPException(status_code=403, detail="Invalid agent token")
    _registered_agents[body.agent_id] = {"id": body.agent_id, "status": "active"}
    return {"registered": True, "agent_id": body.agent_id}


@router.get("")
async def list_agents(_user=Depends(require_auth)):
    """List registered agents."""
    return list(_registered_agents.values())
