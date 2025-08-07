"""
OpenAI API integration service.
"""

import logging

import openai
import tiktoken
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration."""

    def __init__(self) -> None:
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.default_ai_model

    async def generate_response(
        self,
        user_message: str,
        role_prompt: str,
        model: str | None = None,
    ) -> tuple[str, int]:
        """
        Generate AI response with role enhancement.

        Args:
            user_message: User's input message
            role_prompt: System role prompt for AI
            model: OpenAI model to use (optional)

        Returns:
            Tuple of (AI response, total tokens used)

        Raises:
            openai.APIError: If OpenAI API request fails
            ValueError: If input validation fails
        """
        if not user_message.strip():
            raise ValueError("User message cannot be empty")

        if not role_prompt.strip():
            raise ValueError("Role prompt cannot be empty")

        model = model or self.default_model

        # Count input tokens to ensure we don't exceed limits
        input_text = f"{role_prompt}\n\n{user_message}"
        input_tokens = self.count_tokens(input_text, model)

        if input_tokens > settings.max_tokens_per_request:
            raise ValueError(
                f"Input too long: {input_tokens} tokens > {settings.max_tokens_per_request} limit"
            )

        # Calculate max response tokens (leave buffer for completion)
        max_response_tokens = min(
            settings.max_tokens_per_request - input_tokens - 100,  # 100 token buffer
            2000,  # Reasonable response length
        )

        if max_response_tokens < 50:
            raise ValueError("Input too long, no room for response")

        try:
            logger.info(f"Generating response with {model}, input tokens: {input_tokens}")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": role_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_response_tokens,
                temperature=0.7,
                timeout=30.0,  # 30 second timeout
            )

            if not response.choices:
                raise ValueError("No response received from OpenAI")

            ai_response = response.choices[0].message.content
            if not ai_response:
                raise ValueError("Empty response received from OpenAI")

            total_tokens = (
                response.usage.total_tokens
                if response.usage
                else input_tokens + self.count_tokens(ai_response, model)
            )

            logger.info(f"Response generated successfully, total tokens: {total_tokens}")
            return ai_response, total_tokens

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise ValueError(
                "AI service is currently overloaded. Please try again in a few minutes."
            ) from e

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ValueError(
                "AI service is temporarily unavailable. Please try again later."
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            raise ValueError("An unexpected error occurred. Please try again.") from e

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text for specified model.

        Args:
            text: Text to count tokens for
            model: OpenAI model name

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            # Fallback for unknown models
            logger.warning(f"Unknown model {model}, using cl100k_base encoding")
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Rough estimation: ~4 characters per token
            return len(text) // 4

    def validate_model(self, model: str) -> bool:
        """
        Validate if model is supported.

        Args:
            model: Model name to validate

        Returns:
            True if model is supported
        """
        supported_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
        ]
        return model in supported_models
