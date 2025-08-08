"""
Simple application configuration.
"""

import os

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Load from OS env and .env file
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Required settings
    bot_token: str = Field(default="", description="Telegram Bot Token from BotFather")

    # OpenAI settings
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Environment settings
    project_name: str = Field(
        default="English Teacher Bot", description="Project name for greetings and display"
    )
    environment: str = Field(default="development", description="Environment")
    database_url: str = Field(
        default="postgresql+asyncpg://english_teacher_bot_user:password@localhost:5432/english_teacher_bot_db",
        description="Database connection URL",
    )

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_session_ttl: int = Field(default=28800, description="Session TTL in seconds (8h)")

    # Admins (comma-separated IDs in env)
    admin_ids: list[int] = Field(
        default_factory=list,
        description="Admin Telegram IDs",
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids"),
    )

    # Optional webhook for production
    webhook_url: str | None = Field(default=None, description="Webhook URL for production")

    # Server port configuration
    server_port: int = Field(default=8021, description="Server port for webhook mode")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> list[int]:
        # Prefer explicit environment variable
        raw = os.getenv("ADMIN_IDS", "")
        if raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return [int(p) for p in parts]
        # Otherwise parse provided value
        if isinstance(value, list):
            return [int(v) for v in value]
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return [int(p) for p in parts]
        return []


# Global settings instance
settings = Settings()
