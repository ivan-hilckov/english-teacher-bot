"""Redis-backed session service for ephemeral conversation state.

Provides simple CRUD with TTL management.
"""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


class SessionService:
    """Async Redis session helper."""

    def __init__(self, redis: Redis, ttl_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _key(self, telegram_id: int) -> str:
        return f"session:{telegram_id}"

    async def get_session(self, telegram_id: int) -> dict[str, Any]:
        data = await self.redis.get(self._key(telegram_id))
        if not data:
            return {}
        try:
            return json.loads(data)
        except Exception:
            return {}

    async def set_session(self, telegram_id: int, data: dict[str, Any]) -> None:
        await self.redis.set(self._key(telegram_id), json.dumps(data), ex=self.ttl_seconds)

    async def update_session(self, telegram_id: int, updates: dict[str, Any]) -> None:
        session = await self.get_session(telegram_id)
        session.update(updates)
        await self.set_session(telegram_id, session)

    async def clear_session(self, telegram_id: int) -> None:
        await self.redis.delete(self._key(telegram_id))


