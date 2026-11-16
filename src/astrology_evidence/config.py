"""Typed settings with explicit external-service and production gates."""

from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_env: Literal["development", "test", "production"] = "development"
    app_public_origin: str = "http://127.0.0.1:8000"
    database_url: str = "sqlite:///./data/app.db"
    ai_enabled: bool = False
    provider_reviewed: bool = False
    openai_api_key: SecretStr | None = None
    ai_base_url: str = "https://freegg.app/v1"
    ai_model: str = "gpt-6.1-sol"
    google_client_id: str = ""
    google_client_secret: SecretStr | None = None
    authentication_enabled: bool = False
    dev_login_enabled: bool = False
    session_cookie: str = "ae_session"
    secure_cookies: bool = False
    privacy_executor_ready: bool = False
    ephemeris_license_reviewed: bool = False
    ephemeris_mode: Literal["moshier", "swiss"] = "moshier"
    ephemeris_path: str | None = None
    calculation_python: str | None = None
    calculation_pythonpath: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: SecretStr | None = None
    qdrant_path: str = "./data/qdrant"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_revision: str | None = None
    embedding_enabled: bool = False
    answer_deadline_seconds: int = 150
    answer_daily_limit: int = 10
    answer_global_limit: int = 5
    answer_global_daily_limit: int = 100
    guest_workspace_global_limit_per_minute: int = 60

    @model_validator(mode="after")
    def validate_gates(self) -> "Settings":
        if self.ai_base_url != "https://freegg.app/v1" or self.ai_model != "gpt-6.1-sol":
            raise ValueError("Unsupported provider configuration")
        if not 1 <= self.answer_deadline_seconds <= 150:
            raise ValueError("Answer deadline must be at most 150 seconds")
        if not 1 <= self.answer_global_daily_limit <= 100_000:
            raise ValueError("Global daily reading limit must be between 1 and 100000")
        if not 1 <= self.guest_workspace_global_limit_per_minute <= 100_000:
            raise ValueError("Guest workspace limit must be between 1 and 100000")
        if self.ai_enabled and not (self.openai_api_key and self.provider_reviewed):
            raise ValueError("AI requires a runtime credential and provider review")
        if self.embedding_enabled and not self.embedding_revision:
            raise ValueError("Embedding revision must be pinned")
        if self.app_env == "production":
            if self.dev_login_enabled or not self.secure_cookies:
                raise ValueError("Production requires secure cookies and no development login")
            if not self.app_public_origin.startswith("https://"):
                raise ValueError("Production requires HTTPS")
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL")
            if self.authentication_enabled and not (
                self.google_client_id and self.google_client_secret
            ):
                raise ValueError("Production requires Google identity configuration")
            if not (self.privacy_executor_ready and self.ephemeris_license_reviewed):
                raise ValueError("Production privacy and license gates are unresolved")
            if self.ephemeris_mode != "swiss" or not self.ephemeris_path:
                raise ValueError("Production requires reviewed ephemeris files")
            self.session_cookie = "__Host-session"
        return self
