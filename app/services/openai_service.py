"""
OpenAI API integration service - simplified.
"""

import logging

import openai
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Simple OpenAI service for chat completions."""

    def __init__(self) -> None:
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(
        self,
        user_message: str,
        role_prompt: str,
        model: str | None = None,
        *,
        context_messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        max_response_tokens: int | None = None,
        agent_mode: bool | None = None,
        meta_instructions: str | None = None,
    ) -> tuple[str, int]:
        """Generate AI response with context and tuning parameters."""
        # Build message list
        messages = [{"role": "system", "content": role_prompt}]

        if meta_instructions:
            messages.append({"role": "system", "content": meta_instructions})

        if context_messages:
            for msg in context_messages:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        # Use provided params or defaults
        model = model or settings.default_ai_model
        temperature = temperature if temperature is not None else settings.ai_temperature
        top_p = top_p if top_p is not None else settings.ai_top_p

        presence_penalty = (
            presence_penalty if presence_penalty is not None else settings.ai_presence_penalty
        )

        frequency_penalty = (
            frequency_penalty if frequency_penalty is not None else settings.ai_frequency_penalty
        )

        max_tokens = max_response_tokens or settings.ai_max_response_tokens

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                timeout=30.0,
            )

            ai_response = response.choices[0].message.content
            if not ai_response:
                raise ValueError("Empty response from OpenAI")

            total_tokens = response.usage.total_tokens if response.usage else 0
            return ai_response, total_tokens

        except openai.RateLimitError:
            raise ValueError("Rate limit exceeded. Please try again later.") from None
        except openai.APIError:
            raise ValueError("OpenAI API error. Please try again later.") from None
        except Exception as e:
            logger.error(f"OpenAI service error: {e}")
            raise ValueError("An error occurred. Please try again.") from e
