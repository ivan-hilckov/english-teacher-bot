"""
Bot handlers - simplified.
"""

import logging

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import (
    Conversation,
    User,
    get_conversation_history,
    get_or_create_user_role,
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = Router()


def get_predefined_response(text: str) -> str | None:
    """Check for predefined responses."""
    lower = text.lower()

    if any(word in lower for word in ["creator", "создатель", "автор", "кто тебя"]):
        return (
            "🧑‍💻 <b>Creator:</b> Ivan Hilkov (@ivan-hilckov)\n"
            "🔗 GitHub: https://github.com/ivan-hilckov\n"
            "📱 Telegram: @mrbzzz"
        )

    if any(word in lower for word in ["repository", "github", "код", "source"]):
        return (
            "📂 <b>Source:</b> https://github.com/ivan-hilckov/english-teacher-bot\n"
            "🛠 Python 3.12+ • aiogram 3.0 • SQLAlchemy 2.0 • OpenAI API"
        )

    if any(word in lower for word in ["help", "помощь", "commands", "что ты"]):
        return (
            "🎓 <b>English Teacher Bot</b>\n\n"
            "• Grammar correction with error tables\n"
            "• Translation to English\n"
            "• Learning progress tracking\n\n"
            "Just send text or use /do <text>"
        )

    return None


async def get_or_create_user(session: AsyncSession, telegram_user) -> User:
    """Get existing user or create new one."""
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
        )
        session.add(user)
        await session.commit()

    return user


async def process_ai_message(message: types.Message, session: AsyncSession, text: str) -> None:
    """Process message through AI service."""
    if not message.from_user:
        return

    # Check predefined responses
    predefined = get_predefined_response(text)
    if predefined:
        await message.reply(predefined, parse_mode=ParseMode.HTML)
        return

    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        user = await get_or_create_user(session, message.from_user)
        user_role = await get_or_create_user_role(session, user.id)

        # Get conversation context
        recent = await get_conversation_history(
            session, user.id, limit=settings.ai_context_messages
        )
        context_messages = []
        for c in reversed(recent):
            context_messages.extend(
                [
                    {"role": "user", "content": c.user_message},
                    {"role": "assistant", "content": c.ai_response},
                ]
            )

        # AI request with debug params
        ai_response, tokens = await OpenAIService().generate_response(
            user_message=text,
            role_prompt=user_role.role_prompt,
            context_messages=context_messages,
            temperature=0.3,
            max_response_tokens=1200,
            meta_instructions="Decide: correction or translation. For corrections, use error table format.",
        )

        conversation = Conversation(
            user_id=user.id,
            user_message=text,
            ai_response=ai_response,
            model_used=settings.default_ai_model,
            tokens_used=tokens,
            role_used=user_role.role_name,
        )
        session.add(conversation)
        await session.commit()

        await message.reply(ai_response, parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply("❌ Error processing request. Please try again.")
        logger.error(f"AI processing error: {e}")


@router.message(Command("start"))
async def start_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle /start command."""
    if not message.from_user:
        await message.answer(f"Welcome to {settings.project_name}!")
        return

    user = await get_or_create_user(session, message.from_user)

    greeting = (
        f"🎓 Welcome to <b>{settings.project_name}</b>, {user.display_name}!\n\n"
        f"📚 <b>Features:</b>\n"
        f"• Grammar correction with error tables\n"
        f"• Translation to English\n"
        f"• Learning progress tracking\n\n"
        f"📋 <b>Usage:</b>\n"
        f"• Send any text for correction/translation\n"
        f"• Use /do &lt;text&gt; for explicit processing\n\n"
        f"🔗 Source: https://github.com/ivan-hilckov/english-teacher-bot"
    )
    await message.answer(greeting, parse_mode=ParseMode.HTML)


@router.message(Command("do"))
async def do_handler(message: types.Message, session: AsyncSession) -> None:
    """Process text via /do command."""
    if not message.text:
        await message.reply("Usage: /do <your text>")
        return

    text = message.text.replace("/do ", "", 1).strip()
    if not text:
        await message.reply("Usage: /do <your text>")
        return

    await process_ai_message(message, session, text)


@router.message(F.text)
async def text_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle all text messages."""
    if message.text:
        await process_ai_message(message, session, message.text)
