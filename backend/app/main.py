"""NetScope FastAPI application."""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app import __version__
from app.api.v1.router import api_router
from app.config import get_settings
from app.schemas.common import HealthResponse

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    yield
    from app.services.threat_intel import ThreatIntelService
    # Cleanup any async clients if needed


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI-powered network observability and security platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok", version=__version__)

    @app.get("/")
    async def root():
        return {"name": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
