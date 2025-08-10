"""
OpenAI API integration service - simplified.
"""

import openai
from openai import AsyncOpenAI

from app.config import settings

# Model parameters
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7
MAX_TOKENS = 1000
TOP_P = 0.9
PRESENCE_PENALTY = 0.1
FREQUENCY_PENALTY = 0.1

SYSTEM_PROMPT = """You are a friendly and enthusiastic English teacher who helps students feel comfortable while learning the language.
You create a supportive atmosphere and make learning interesting.

Original: `[original]`

**Correction:**

```
[corrected - casual]
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

Be encouraging, explain "why", make errors normal.
"""


class OpenAIService:
    """OpenAI service for English corrections."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(self, user_message: str) -> tuple[str, int]:
        """Generate English correction response."""
        try:
            response = await self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Correct this text: `{user_message}`"},
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                presence_penalty=PRESENCE_PENALTY,
                frequency_penalty=FREQUENCY_PENALTY,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            tokens = response.usage.total_tokens if response.usage else 0
            return content, tokens

        except openai.OpenAIError as e:
            raise ValueError(f"OpenAI error: {e}") from e
