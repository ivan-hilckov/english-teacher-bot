"""
OpenAI API integration service with tuning, short-context, and agent-like tool support.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, TypedDict

import openai
import tiktoken
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None


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
        *,
        context_messages: list[ChatMessage] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        max_response_tokens: int | None = None,
        agent_mode: bool | None = None,
        meta_instructions: str | None = None,
    ) -> tuple[str, int]:
        """Generate AI response with role enhancement and optional tool use.

        Args:
            user_message: User's input message.
            role_prompt: Long-lived system role prompt for the assistant.
            model: Optional OpenAI model override.
            context_messages: Optional recent chat history (old→new order).
            temperature: Sampling temperature override.
            top_p: Nucleus sampling override.
            presence_penalty: Presence penalty override.
            frequency_penalty: Frequency penalty override.
            max_response_tokens: Hard cap tokens for completion.
            agent_mode: Enable one-step tool calling loop.
            meta_instructions: Optional short operational guardrails appended to system.

        Returns:
            (AI response text, total tokens used)
        """
        if not user_message.strip():
            raise ValueError("User message cannot be empty")
        if not role_prompt.strip():
            raise ValueError("Role prompt cannot be empty")

        model = model or self.default_model

        # Build messages with system, optional meta, optional context, and final user
        messages: list[dict[str, Any]] = [{"role": "system", "content": role_prompt}]
        if meta_instructions and meta_instructions.strip():
            messages.append({"role": "system", "content": meta_instructions.strip()})
        if context_messages:
            for m in context_messages:
                # Exclude tool messages from external context; assistant/user only
                if m["role"] in ("user", "assistant"):
                    messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": user_message})

        # Count input tokens to ensure we don't exceed limits
        flattened_input = "\n\n".join(m["content"] for m in messages)
        input_tokens = self.count_tokens(flattened_input, model)
        if input_tokens > settings.max_tokens_per_request:
            raise ValueError(
                f"Input too long: {input_tokens} tokens > {settings.max_tokens_per_request} limit"
            )

        max_resp_tokens = (
            max_response_tokens
            if max_response_tokens is not None
            else settings.ai_max_response_tokens
        )
        # Leave safety buffer for tool round-trip
        max_response_tokens_budget = min(
            settings.max_tokens_per_request - input_tokens - 100, max_resp_tokens
        )
        if max_response_tokens_budget < 50:
            raise ValueError("Input too long, no room for response")

        # Sampling params
        temperature = settings.ai_temperature if temperature is None else temperature
        top_p = settings.ai_top_p if top_p is None else top_p
        presence_penalty = (
            settings.ai_presence_penalty if presence_penalty is None else presence_penalty
        )
        frequency_penalty = (
            settings.ai_frequency_penalty if frequency_penalty is None else frequency_penalty
        )

        # Tools (agent-like): language detection utility
        tools_enabled = settings.agent_mode_enabled if agent_mode is None else agent_mode
        tools: list[dict[str, Any]] | None = None
        if tools_enabled:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "detect_language",
                        "description": "Detect probable language code of input text (e.g., en, ru, es, fr, de, zh, ar).",
                        "parameters": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"],
                        },
                    },
                }
            ]

        try:
            logger.info(
                f"Generating response with {model}, input tokens: {input_tokens}, tools: {bool(tools)}"
            )

            # First call
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_response_tokens_budget,
                temperature=temperature,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                tools=tools,
                timeout=30.0,
            )

            choice = response.choices[0]
            msg = choice.message

            # Handle tool calls (single round)
            if tools and getattr(msg, "tool_calls", None):
                tool_messages: list[dict[str, Any]] = []
                for tool_call in msg.tool_calls or []:
                    if tool_call.function.name == "detect_language":
                        args = json.loads(tool_call.function.arguments or "{}")
                        detected = self._tool_detect_language(args.get("text", ""))
                        tool_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": "detect_language",
                                "content": json.dumps({"language": detected}),
                            }
                        )

                # Second call including model output and tool results
                messages_with_tools = messages + [msg.model_dump(exclude_none=True)] + tool_messages
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages_with_tools,
                    max_tokens=max_response_tokens_budget,
                    temperature=temperature,
                    top_p=top_p,
                    presence_penalty=presence_penalty,
                    frequency_penalty=frequency_penalty,
                    timeout=30.0,
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
        """Count tokens in text for specified model."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            logger.warning(f"Unknown model {model}, using cl100k_base encoding")
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4

    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        supported_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
        ]
        return model in supported_models

    @staticmethod
    def _tool_detect_language(text: str) -> str | None:
        """Lightweight heuristic detector mirrored from handlers for tool-use."""
        if any("\u0400" <= c <= "\u04ff" for c in text):
            return "ru"
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            return "zh"
        if any("\u0600" <= c <= "\u06ff" for c in text):
            return "ar"
        if any(ch in "ñáéíóúü¿¡" for ch in text.lower()):
            return "es"
        if any(ch in "àâäéèêëïîôöùûüÿç" for ch in text.lower()):
            return "fr"
        if any(ch in "äöüß" for ch in text.lower()):
            return "de"
        if all(ord(ch) < 256 for ch in text):
            return "en"
        return None
