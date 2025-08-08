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
from app.database import (
    Conversation,
    User,
    get_conversation_history,
    get_or_create_user_role,
    save_correction_history,
)
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Create router
router = Router()


# Helper functions for English teaching
def count_errors_in_response(ai_response: str) -> dict[str, int]:
    """Parse AI response to count different types of errors."""
    response_lower = ai_response.lower()

    # Count error types based on keywords in AI response
    grammar_errors = response_lower.count("grammar") + response_lower.count("грамматическ")
    spelling_errors = response_lower.count("spelling") + response_lower.count("орфографическ")
    vocabulary_errors = response_lower.count("vocabulary") + response_lower.count("словарн")
    style_errors = response_lower.count("style") + response_lower.count("стилистическ")

    total_errors = response_lower.count("| ") - 1 if "| " in response_lower else 0
    if total_errors < 0:
        total_errors = 0

    return {
        "total": total_errors,
        "grammar": grammar_errors,
        "spelling": spelling_errors,
        "vocabulary": vocabulary_errors,
        "style": style_errors,
    }


def detect_correction_type(original_text: str, ai_response: str) -> str:
    """Detect if this was correction or translation."""
    # Simple heuristic: if AI response contains table format, it's likely a correction
    if "|" in ai_response and ("error" in ai_response.lower() or "ошибк" in ai_response.lower()):
        return "correction"

    # Check if original text contains non-Latin characters (indicating translation needed)
    has_non_latin = any(ord(char) > 127 for char in original_text)
    if has_non_latin and len(original_text) < len(ai_response) * 2:
        return "translation"

    return "correction"


def detect_language(text: str) -> str | None:
    """Basic language detection using character patterns."""
    # Cyrillic characters - Russian/Ukrainian/Bulgarian
    if any("\u0400" <= char <= "\u04ff" for char in text):
        return "ru"

    # Chinese characters
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return "zh"

    # Arabic characters
    if any("\u0600" <= char <= "\u06ff" for char in text):
        return "ar"

    # Spanish-specific characters
    if any(char in "ñáéíóúü¿¡" for char in text.lower()):
        return "es"

    # French-specific characters
    if any(char in "àâäéèêëïîôöùûüÿç" for char in text.lower()):
        return "fr"

    # German-specific characters
    if any(char in "äöüß" for char in text.lower()):
        return "de"

    # Default to English if mostly Latin characters
    if all(ord(char) < 256 for char in text):
        return "en"

    return None


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
        "https://github.com/ivan-hilckov/english-teacher-bot\n\n"
        "🛠 <b>Tech Stack:</b>\n"
        "• Python 3.12+ with aiogram 3.0\n"
        "• SQLAlchemy 2.0 async + PostgreSQL\n"
        "• OpenAI API for English tutoring\n"
        "• Grammar correction & translation\n"
        "• Docker containerization"
    ),
    "help": (
        "🎓 <b>English Teacher Bot Help</b>\n\n"
        "📚 <b>What I do:</b>\n"
        "• Correct English grammar and spelling\n"
        "• Translate text from any language to English\n"
        "• Provide detailed error explanations\n"
        "• Track your learning progress\n\n"
        "💡 <b>Examples:</b>\n"
        "• Send: 'I are student' → Get correction table\n"
        "• Send: 'Привет, как дела?' → Get English translation\n"
        "• Use /do command for explicit requests"
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

    # Help-related keywords
    help_keywords = ["help", "помощь", "что ты умеешь", "what can you do", "команды", "commands"]
    if any(keyword in message_lower for keyword in help_keywords):
        return PREDEFINED_RESPONSES["help"]

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

        # Prepare short conversation context
        recent = await get_conversation_history(
            session=session, user_id=user.id, limit=settings.ai_context_messages
        )
        context_messages = []
        for c in reversed(recent):  # old -> new
            context_messages.append(
                {"role": "user", "content": c.user_message, "tool_call_id": None}
            )
            context_messages.append(
                {"role": "assistant", "content": c.ai_response, "tool_call_id": None}
            )

        # Generate AI response with tuning and agent mode
        print(f"Generating response for {text}")
        ai_response, tokens = await openai_service.generate_response(
            user_message=text,
            role_prompt=user_role.role_prompt,
            model=settings.default_ai_model,
            context_messages=context_messages,
            temperature=settings.ai_temperature,
            top_p=settings.ai_top_p,
            presence_penalty=settings.ai_presence_penalty,
            frequency_penalty=settings.ai_frequency_penalty,
            max_response_tokens=settings.ai_max_response_tokens,
            agent_mode=settings.agent_mode_enabled,
            meta_instructions=(
                "Always decide: correction vs translation."
                " If translation, output only natural English translation."
                " If correction, include a Markdown table with columns: | Original | Error Type | Explanation | Correction |,"
                " then provide the corrected sentence. Keep responses concise."
            ),
        )

        # Analyze response for correction history
        error_counts = count_errors_in_response(ai_response)
        correction_type = detect_correction_type(text, ai_response)
        detected_language = detect_language(text)

        # Save correction history for learning analytics
        await save_correction_history(
            session=session,
            user_id=user.id,
            original_text=text,
            corrected_text=ai_response,
            correction_type=correction_type,
            error_count=error_counts["total"],
            detected_language=detected_language,
            errors_grammar=error_counts["grammar"],
            errors_spelling=error_counts["spelling"],
            errors_vocabulary=error_counts["vocabulary"],
            errors_style=error_counts["style"],
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

    # Send enhanced greeting with English teacher info
    greeting = (
        f"🎓 Welcome to <b>{settings.project_name}</b>, {user.display_name}!\n\n"
        f"📚 <b>What I can do:</b>\n"
        f"• Correct English grammar and spelling errors\n"
        f"• Translate text from any language to English\n"
        f"• Provide detailed error explanations\n"
        f"• Track your English learning progress\n\n"
        f"📋 <b>Commands:</b>\n"
        f"• /start - Show this welcome message\n"
        f"• /do &lt;text&gt; - Process text for correction/translation\n"
        f"• Just send any text - I'll automatically help!\n\n"
        f"📊 <b>Example correction:</b>\n"
        f"You: 'I are student'\n"
        f"Me: Grammar error table + 'I am a student'\n\n"
        f"🌍 <b>Example translation:</b>\n"
        f"You: 'Привет, как дела?'\n"
        f"Me: 'Hello, how are you?'\n\n"
        f"🔗 <b>Source:</b> https://github.com/ivan-hilckov/english-teacher-bot\n"
        f"💡 AI-powered English tutor with OpenAI"
    )
    await message.answer(greeting, parse_mode=ParseMode.HTML)


@router.message(Command("do"))
async def do_ai_handler(message: types.Message, session: AsyncSession) -> None:
    """Process user text for English correction or translation via /do command."""
    # Extract text after /do command
    if not message.text:
        await message.reply(
            "Usage: /do <your text>\n"
            "Examples:\n"
            "• /do I are student (for correction)\n"
            "• /do Привет, как дела? (for translation)"
        )
        return

    text = message.text.replace("/do ", "", 1).strip()
    if not text:
        await message.reply(
            "Usage: /do <your text>\n"
            "Examples:\n"
            "• /do I are student (for correction)\n"
            "• /do Привет, как дела? (for translation)"
        )
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
