"""
OpenAI API integration service - simplified.
"""

import logging

import openai
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Hardcoded model parameters for English Teacher Bot
MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.3
MAX_TOKENS = 1200
TOP_P = 1.0
PRESENCE_PENALTY = 0.0
FREQUENCY_PENALTY = 0.0

# English teacher system prompt
SYSTEM_PROMPT = """You are an expert English tutor. Your job is to:

1. CORRECTION MODE: If text is in English with errors, provide:
   - Detailed error table: | Original | Error Type | Explanation | Correction |
   - Complete corrected version
   - Error types: Grammar, Spelling, Style, Vocabulary

2. TRANSLATION MODE: If text is in another language:
   - Detect language
   - Translate to natural English
   - Provide only the English translation

Be precise, educational, and helpful. Decide: correction or translation. For corrections, use error table format."""


class OpenAIService:
    """Simple OpenAI service for chat completions."""

    def __init__(self) -> None:
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(self, user_message: str) -> tuple[str, int]:
        """Generate AI response for English correction/translation."""
        try:
            response = await self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                presence_penalty=PRESENCE_PENALTY,
                frequency_penalty=FREQUENCY_PENALTY,
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
