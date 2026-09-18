"""Central environment-driven application settings."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    project_name: str = "RAG Knowledge Platform API"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+psycopg://rag_platform:change-me-in-local-env@postgres:5432/rag_platform"
    )
    redis_url: str = "redis://redis:6379/0"
    embedding_dimensions: int = Field(default=1536, ge=1)
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret_key: str = "replace-with-a-long-random-secret"
    jwt_access_token_minutes: int = Field(default=15, ge=1, le=60)
    jwt_refresh_token_days: int = Field(default=30, ge=1, le=90)

    @model_validator(mode="after")
    def prevent_placeholder_production_secret(self) -> "Settings":
        """Reject the documented placeholder secret in production environments."""

        if self.app_env == "production" and self.jwt_secret_key == "replace-with-a-long-random-secret":
            raise ValueError("JWT_SECRET_KEY must be changed for production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide, immutable settings instance."""

    return Settings()
