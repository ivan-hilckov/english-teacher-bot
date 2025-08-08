"""
OpenAI API integration service - simplified.
"""

import logging

import openai
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Hardcoded model parameters for English Teacher Bot - GPT-5 Nano optimized
MODEL = "gpt-4o-mini"  # Fallback to available model for testing
TEMPERATURE = 0.7  # Lower for more focused responses
MAX_TOKENS = 1000  # Reduced for cost efficiency
TOP_P = 0.9  # Slightly focused sampling
PRESENCE_PENALTY = 0.1  # Small penalty to avoid repetition
FREQUENCY_PENALTY = 0.1  # Small penalty for token efficiency
REASONING_EFFORT = "low"  # GPT-5 specific - low effort for speed/cost efficiency

# English teacher system prompt - GPT-5 Nano optimized for cost efficiency
SYSTEM_PROMPT = """You are a friendly and enthusiastic English teacher who helps students feel comfortable while learning the language. You create a supportive atmosphere and make learning interesting.
Let me see...

Original: `[original]`

**Correction:**

```
[corrected]
```

**Correction in formal English:**

```
[corrected - formal]
```

**Correction in simple English:**

```
[corrected - simple]
```
Explanations:

[explanations]


<context_gathering>
Goal: Get enough context fast. Stop as soon as you can act.
- Brief explanations
- Keep under 3000 chars total
</context_gathering>

Be encouraging, explain "why", make errors normal."""


class OpenAIService:
    """Simple OpenAI service for chat completions."""

    def __init__(self) -> None:
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(self, user_message: str) -> tuple[str, int]:
        """Generate AI response for English correction/translation."""
        logger.debug("Starting OpenAI request | model=%s", MODEL)
        logger.debug("User message length: %d chars", len(user_message))

        try:
            # Log request parameters
            request_params = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "presence_penalty": PRESENCE_PENALTY,
                "frequency_penalty": FREQUENCY_PENALTY,
                # "reasoning_effort": REASONING_EFFORT,  # GPT-5 specific - disabled
            }

            user_message = f"""
                Correct this text: `{user_message}`
            """

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
                # reasoning_effort=REASONING_EFFORT,  # GPT-5 specific parameter - disabled for gpt-4o-mini
                # timeout=30.0,
            )

            logger.debug("OpenAI API response received successfully")
            logger.debug("Response model: %s", getattr(response, "model", "unknown"))

            ai_response = response.choices[0].message.content
            if not ai_response:
                logger.error("Empty response content from OpenAI")
                raise ValueError("Empty response from OpenAI")

            logger.debug("AI response length: %d chars", len(ai_response))

            # Convert AI response to Telegram-safe markdown
            markdown_response = self._format_for_telegram(ai_response)
            logger.debug("Formatted response length: %d chars", len(markdown_response))

            total_tokens = response.usage.total_tokens if response.usage else 0
            logger.info("OpenAI usage | total_tokens=%d", total_tokens)

            return markdown_response, total_tokens

        except openai.RateLimitError as e:
            logger.exception("OpenAI Rate limit error")
            raise ValueError("Rate limit exceeded. Please try again later.") from e
        except openai.APIError as e:
            logger.exception("OpenAI API error")
            raise ValueError("OpenAI API error. Please try again later.") from e
        except openai.AuthenticationError as e:
            logger.exception("OpenAI Authentication error")
            raise ValueError("Authentication error. Please check API key.") from e
        except openai.PermissionDeniedError as e:
            logger.exception("OpenAI Permission error")
            raise ValueError("Permission denied. Please check API access.") from e
        except openai.BadRequestError as e:
            logger.exception("OpenAI Bad Request error")
            raise ValueError("Bad request to OpenAI API. Please try again.") from e
        except Exception as e:
            logger.exception("Unexpected OpenAI service error")
            raise ValueError("An error occurred. Please try again.") from e

    def _format_for_telegram(self, text: str) -> str:
        """Convert AI response to Telegram-safe HTML format."""
        # AI response already uses <b></b> tags for HTML formatting
        # Keep emojis and basic structure
        # No need to escape anything for HTML mode

        return text
