"""Application configuration loaded from environment variables.

Secrets are never hardcoded: they come from the environment (or a local `.env`
file that is git-ignored). `get_settings()` is cached so the environment is read
once per process.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "AI Sales Assistant"
    environment: Environment = "local"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://app:change-me-app@localhost:5432/sales_assistant"

    # --- OpenAI ---
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1"
    openai_model_cheap: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_moderation_model: str = "omni-moderation-latest"
    openai_timeout: float = 30.0
    openai_max_retries: int = 2

    # --- Security ---
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit: str = "30/minute"

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow a comma-separated string for CORS origins (env-friendly)."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def json_logs(self) -> bool:
        """Render structured JSON logs outside local development."""
        return self.environment != "local"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
