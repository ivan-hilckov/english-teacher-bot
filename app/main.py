"""
Simple main application entry point.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.database import create_tables
from app.handlers import router
from app.middleware import DataLayerMiddleware


def configure_logging():
    """Simple logging setup."""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

    # Silence noisy libraries
    for logger_name in ["aiogram", "openai", "uvicorn"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


async def main():
    """Main application function."""
    configure_logging()
    await create_tables()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Redis client
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    data_layer_mw = DataLayerMiddleware(redis)
    dp.message.middleware(data_layer_mw)
    dp.callback_query.middleware(data_layer_mw)
    dp.include_router(router)

    if settings.webhook_url:
        app = FastAPI()

        @app.post("/webhook")
        async def webhook(update: dict):
            await dp.feed_update(bot, Update(**update))
            return {"ok": True}

        await bot.set_webhook(url=settings.webhook_url)

        import uvicorn

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=settings.server_port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        try:
            await dp.start_polling(bot)
        finally:
            await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
