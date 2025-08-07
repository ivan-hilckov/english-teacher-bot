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
        default="postgresql+asyncpg://hello_user:password@localhost:5432/hello_ai_bot",
        description="Database connection URL",
    )

    # Environment settings
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Optional webhook for production
    webhook_url: str | None = Field(default=None, description="Webhook URL for production")

    # Server port configuration
    server_port: int = Field(default=8000, description="Server port for webhook mode")

    # Project settings
    project_name: str = Field(
        default="Hello AI Bot", description="Project name for greetings and display"
    )

    # OpenAI settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    default_ai_model: str = Field(default="gpt-3.5-turbo", description="Default AI model")
    default_role_prompt: str = Field(
        default="You are a helpful AI assistant.", description="Default role prompt"
    )

    # Rate limiting settings
    max_requests_per_hour: int = Field(default=60, description="Rate limit per user")
    max_tokens_per_request: int = Field(default=4000, description="Token limit per request")


# Global settings instance
settings = Settings()
