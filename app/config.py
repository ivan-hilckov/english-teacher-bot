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
    default_ai_model: str = Field(default="gpt-3.5-turbo", description="Default AI model")
    ai_temperature: float = Field(
        default=0.3, description="Sampling temperature for AI model (0.0-2.0)"
    )
    ai_top_p: float = Field(default=1.0, description="Nucleus sampling top_p (0.0-1.0)")
    ai_presence_penalty: float = Field(default=0.0, description="Presence penalty (-2.0 to 2.0)")
    ai_frequency_penalty: float = Field(default=0.0, description="Frequency penalty (-2.0 to 2.0)")
    ai_max_response_tokens: int = Field(
        default=1200, description="Hard cap for max response tokens"
    )
    ai_context_messages: int = Field(
        default=4, description="Number of recent conversation turns to include as context"
    )
    agent_mode_enabled: bool = Field(
        default=True, description="Enable agent-like tool calling inside OpenAI service"
    )
    default_role_prompt: str = Field(
        default="""You are an expert English tutor. Your job is to:

1. CORRECTION MODE: If text is in English with errors, provide:
   - Detailed error table: | Original | Error Type | Explanation | Correction |
   - Complete corrected version
   - Error types: Grammar, Spelling, Style, Vocabulary

2. TRANSLATION MODE: If text is in another language:
   - Detect language
   - Translate to natural English
   - Provide only the English translation

Be precise, educational, and helpful.""",
        description="English teacher role prompt",
    )

    # Rate limiting settings
    max_requests_per_hour: int = Field(default=60, description="Rate limit per user")
    max_tokens_per_request: int = Field(default=4000, description="Token limit per request")


# Global settings instance
settings = Settings()
