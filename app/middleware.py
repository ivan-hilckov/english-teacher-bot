"""
Unified middleware to inject DB session and Redis session service.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.session_service import SessionService


class DataLayerMiddleware(BaseMiddleware):
    """Middleware to inject database and session services into handlers."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            try:
                data["session"] = session
                data["session_service"] = SessionService(
                    self.redis, ttl_seconds=settings.redis_session_ttl
                )
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class DatabaseMiddleware(BaseMiddleware):
    """Backward-compatible DB-only middleware used by tests.

    Injects SQLAlchemy session without Redis requirement.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            try:
                data["session"] = session
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
