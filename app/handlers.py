"""
All bot handlers in one file.
"""

import logging

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import Conversation, User, get_or_create_user_role
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Create router
router = Router()


# Predefined responses for specific queries
PREDEFINED_RESPONSES = {
    "creator": (
        "🧑‍💻 <b>My Creator:</b>\n"
        "Ivan Hilkov (@ivan-hilckov)\n"
        "Lead Frontend Engineer with 17+ years experience\n\n"
        "🔗 <b>GitHub:</b> https://github.com/ivan-hilckov\n"
        "📱 <b>Telegram:</b> @mrbzzz\n"
        "📸 <b>Instagram:</b> @helios_m42"
    ),
    "repository": (
        "📂 <b>Source Code:</b>\n"
        "https://github.com/ivan-hilckov/hello-ai-bot\n\n"
        "🛠 <b>Tech Stack:</b>\n"
        "• Python 3.12+ with aiogram 3.0\n"
        "• SQLAlchemy 2.0 async + PostgreSQL\n"
        "• OpenAI API integration\n"
        "• Docker containerization"
    ),
}


def check_predefined_response(user_message: str) -> str | None:
    """Check if user message matches predefined responses."""
    message_lower = user_message.lower()

    # Creator-related keywords
    creator_keywords = [
        "создатель",
        "creator",
        "автор",
        "author",
        "разработчик",
        "developer",
        "кто тебя",
        "who created",
    ]
    if any(keyword in message_lower for keyword in creator_keywords):
        return PREDEFINED_RESPONSES["creator"]

    # Repository-related keywords
    repo_keywords = ["репозиторий", "repository", "исходный код", "source code", "github", "код"]
    if any(keyword in message_lower for keyword in repo_keywords):
        return PREDEFINED_RESPONSES["repository"]

    return None


async def process_ai_message(message: types.Message, session: AsyncSession, text: str) -> None:
    """Process message through AI service with predefined responses check."""
    if not message.from_user:
        await message.reply("Authentication required")
        return

    # Check for predefined responses first
    predefined_response = check_predefined_response(text)
    if predefined_response:
        await message.reply(predefined_response, parse_mode=ParseMode.HTML)
        logger.info(f"Sent predefined response to {message.from_user.id}")
        return

    # Get or create user
    telegram_user = message.from_user
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Create new user if not exists
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
        )
        session.add(user)
        await session.commit()
        logger.info(f"Created new user for AI interaction: {user.display_name}")

    try:
        # Send typing indicator
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Get user role
        user_role = await get_or_create_user_role(session, user.id)

        # Initialize OpenAI service
        openai_service = OpenAIService()

        # Generate AI response
        ai_response, tokens = await openai_service.generate_response(
            user_message=text, role_prompt=user_role.role_prompt, model=settings.default_ai_model
        )

        # Save conversation to database
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

        # Send AI response to user
        await message.reply(ai_response, parse_mode=ParseMode.HTML)

        logger.info(f"AI response sent to {user.display_name}, tokens used: {tokens}")

    except ValueError as e:
        # User-friendly error (from our service)
        await message.reply(f"❌ {str(e)}")
        logger.warning(f"AI service error for {telegram_user.id}: {e}")

    except Exception as e:
        # Unexpected error
        await message.reply(
            "❌ Sorry, I'm having trouble processing your request. Please try again later."
        )
        logger.error(f"Unexpected error in AI handler: {e}")


@router.message(Command("start"))
async def start_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle /start command."""
    if not message.from_user:
        await message.answer(
            f"Hello! Welcome to {settings.project_name}, <b>Unknown</b>", parse_mode=ParseMode.HTML
        )
        return

    telegram_user = message.from_user

    # Get or create user
    stmt = select(User).where(User.telegram_id == telegram_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.language_code = telegram_user.language_code
        logger.info(f"Updated user: {user.display_name}")
    else:
        # Create new user
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
        )
        session.add(user)
        logger.info(f"Created new user: {user.display_name}")

    await session.commit()

    # Send enhanced greeting with bot info
    greeting = (
        f"Hello! Welcome to {settings.project_name}, 😎 <b>{user.display_name}</b>\n\n"
        f"🤖 <b>What I can do:</b>\n"
        f"• Answer questions and have conversations\n"
        f"• Help with various tasks using AI\n"
        f"• Process any text message you send\n\n"
        f"📋 <b>Commands:</b>\n"
        f"• /start - Show this welcome message\n"
        f"• /do &lt;message&gt; - Chat with AI (optional)\n"
        f"• Just type any message - I'll respond with AI\n\n"
        f"🔗 <b>Source code:</b> https://github.com/ivan-hilckov/hello-ai-bot\n"
        f"💡 Built with aiogram 3.0 + OpenAI API"
    )
    await message.answer(greeting, parse_mode=ParseMode.HTML)


@router.message(Command("do"))
async def do_ai_handler(message: types.Message, session: AsyncSession) -> None:
    """Process user text through OpenAI API via /do command."""
    # Extract text after /do command
    if not message.text:
        await message.reply("Usage: /do <your message>\nExample: /do Explain quantum physics")
        return

    text = message.text.replace("/do ", "", 1).strip()
    if not text:
        await message.reply("Usage: /do <your message>\nExample: /do Explain quantum physics")
        return

    # Use the common AI processing function
    await process_ai_message(message, session, text)


@router.message(F.text)
async def default_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle all other text messages through AI service."""
    if not message.text:
        return

    # Process any text message through AI
    await process_ai_message(message, session, message.text)

    if message.from_user:
        logger.info(
            f"Processed text message from {message.from_user.username or message.from_user.first_name}: {message.text[:50]}..."
        )
