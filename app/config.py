"""
Simple application configuration.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

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
    # Optional webhook for production
    webhook_url: str | None = Field(default=None, description="Webhook URL for production")

    # Server port configuration
    server_port: int = Field(default=8021, description="Server port for webhook mode")


# Global settings instance
settings = Settings()
