"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token, get_password_hash
from app.schemas.common import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""

    username: str
    password: str


# In-memory user store for demo. Replace with DB in production.
DEMO_USERS = {
    "admin": get_password_hash("admin"),  # Default admin/admin
}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Exchange username/password for JWT."""
    from app.config import get_settings

    hashed = DEMO_USERS.get(req.username)
    if not hashed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    from app.core.security import verify_password

    if not verify_password(req.password, hashed):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    settings = get_settings()
    token = create_access_token(subject=req.username)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )
