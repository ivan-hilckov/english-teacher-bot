"""
Simple application configuration.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Required settings
    bot_token: str = Field(default="", description="Telegram Bot Token from BotFather")
    database_url: str = Field(
        default="postgresql+asyncpg://english_teacher_bot_user:password@localhost:5432/english_teacher_bot_db",
        description="Database connection URL",
    )

    # Environment settings
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Optional webhook for production
    webhook_url: str | None = Field(default=None, description="Webhook URL for production")

    # Server port configuration
    server_port: int = Field(default=8021, description="Server port for webhook mode")

    # Project settings
    project_name: str = Field(
        default="English Teacher Bot", description="Project name for greetings and display"
    )

    # OpenAI settings
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Rate limiting settings
    max_requests_per_hour: int = Field(default=60, description="Rate limit per user")
    max_tokens_per_request: int = Field(default=4000, description="Token limit per request")


# Global settings instance
settings = Settings()
