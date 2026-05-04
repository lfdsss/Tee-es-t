"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # France Travail
    france_travail_client_id: str = ""
    france_travail_client_secret: str = ""

    # Adzuna (official public API, free tier)
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "fr"

    # Jooble (official public API, single free key)
    jooble_api_key: str = ""
    jooble_location: str = "France"

    # Agents
    scraper_interval_seconds: int = Field(default=900, ge=10)
    matcher_interval_seconds: int = Field(default=60, ge=5)
    notifier_interval_seconds: int = Field(default=30, ge=5)
    match_score_threshold: float = Field(default=0.6, ge=0.0, le=1.0)

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Public base URL used to build accept/decline links embedded in emails.
    # In prod, set this to the API's public hostname (e.g. https://api.studentflow.fr).
    public_base_url: str = "http://localhost:8000"

    # Notifications — webhook (fallback / bridge to Make/Zapier/n8n)
    notification_webhook_url: str = ""

    # Notifications — SMTP email (preferred channel, direct to student)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def france_travail_configured(self) -> bool:
        return bool(self.france_travail_client_id and self.france_travail_client_secret)

    @property
    def adzuna_configured(self) -> bool:
        return bool(self.adzuna_app_id and self.adzuna_app_key)

    @property
    def jooble_configured(self) -> bool:
        return bool(self.jooble_api_key)

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
