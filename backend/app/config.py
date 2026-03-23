"""Application configuration with validation."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from env and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    app_name: str = Field(default="NetScope API", description="Application name")
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")

    # JWT
    jwt_secret_key: str = Field(default="change-me-in-production", description="JWT signing key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=60, description="JWT token expiry")

    # Prometheus
    prometheus_url: str = Field(default="http://localhost:9090", description="Prometheus base URL")

    # Redis (optional)
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching/sessions")

    # Threat intel
    abuseipdb_api_key: Optional[str] = Field(default=None, description="AbuseIPDB API key")
    virustotal_api_key: Optional[str] = Field(default=None, description="VirusTotal API key")
    shodan_api_key: Optional[str] = Field(default=None, description="Shodan API key")

    # Alerting
    smtp_host: Optional[str] = Field(default=None, description="SMTP host for email alerts")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    alert_email_from: Optional[str] = Field(default=None, description="From address for alerts")
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack incoming webhook URL")
    discord_webhook_url: Optional[str] = Field(default=None, description="Discord webhook URL")

    # Central server (for distributed agents)
    central_server_url: Optional[str] = Field(default=None, description="Central NetScope server URL")
    agent_registration_token: Optional[str] = Field(default=None, description="Token for agent registration")

    # Backend URL (for agents pushing data)
    backend_base_url: str = Field(default="http://localhost:8000", description="Backend API base URL")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
