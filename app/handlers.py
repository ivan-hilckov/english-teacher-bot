"""
Bot handlers - simplified.
"""

import logging
import re

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import User
from app.services.balance_service import credit, debit, ensure_initial_bonus
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
            "Just send text"
        )

    return None


async def get_or_create_user(session: AsyncSession, telegram_user) -> User:
    """Get existing user or create/update one from Telegram user data."""
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
    else:
        # Update existing user with fresh data
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.language_code = telegram_user.language_code
        user.is_active = True
        await session.commit()

    return user


async def process_ai_message(message: types.Message, session: AsyncSession, text: str) -> None:
    """Process message through AI service."""
    if not message.from_user:
        logger.warning("No user found in message")
        return

    # Check predefined responses
    predefined = get_predefined_response(text)
    if predefined:
        await message.reply(predefined, parse_mode=ParseMode.HTML)
        return

    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

        user = await get_or_create_user(session, message.from_user)

        await message.answer(f"Let me see... {user.display_name}")
        # AI request - simple and direct
        ai_response, tokens = await OpenAIService().generate_response(text)
        logger.info(
            "AI response generated | length=%d tokens=%d",
            len(ai_response),
            tokens,
        )

        await message.reply(ai_response, parse_mode=ParseMode.MARKDOWN)

    except Exception:
        logger.exception("AI processing error")

        try:
            await message.reply("❌ Error processing request. Please try again.")
        except Exception:
            logger.exception("Failed to send error message")


@router.message(Command("start"))
async def start_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle /start command."""
    if not message.from_user:
        await message.answer("Welcome to English Teacher Bot! Unknown")
        return

    user = await get_or_create_user(session, message.from_user)
    # Ensure first-time bonus
    await ensure_initial_bonus(session, user)

    greeting = (
        f"🎓 Welcome to <b>English Teacher Bot</b>, {user.display_name}!\n\n"
        f"💎 Your balance: <b>{user.balance}</b>\n"
        f"💎 1 request = 1 crystal\n\n"
        f"📋 <b>Usage:</b>\n"
        f"• Send any text for correction/translation\n"
        f"• /profile to see your balance\n"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="Buy 10 💎", callback_data="buy_10")
    await message.answer(greeting, parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())


@router.message(F.text & ~F.text.startswith("/"))
async def text_handler(message: types.Message, session: AsyncSession) -> None:
    """Handle all text messages."""
    if not message.text:
        return

    # Charge 1 crystal before processing (same as /do)
    if not message.from_user:
        return
    user = await get_or_create_user(session, message.from_user)
    ok = await debit(session, user, amount=1, reason="correction_debit")
    if not ok:
        await message.reply("❌ Not enough crystals. Use the Buy 10 💎 button in /start.")
        return

    await process_ai_message(message, session, message.text)
    await message.answer(f"Done! Remaining balance: {user.balance} 💎")


@router.message(Command("profile"))
async def profile_handler(message: types.Message, session: AsyncSession) -> None:
    """Show user balance."""
    if not message.from_user:
        await message.reply("No user context")
        return

    user = await get_or_create_user(session, message.from_user)
    await message.answer(
        f"👤 Profile\n💎 Balance: <b>{user.balance}</b>", parse_mode=ParseMode.HTML
    )


@router.message(Command("info"))
async def info_handler(message: types.Message, session: AsyncSession) -> None:
    """Show current user's Telegram ID and basic info for admin/top-up."""
    if not message.from_user:
        await message.reply("No user context")
        return

    user = await get_or_create_user(session, message.from_user)
    is_admin = message.from_user.id in settings.admin_ids

    print("message.from_user.id", message.from_user.id)
    print("settings.admin_ids", settings.admin_ids)

    username = (
        f"@{message.from_user.username}" if getattr(message.from_user, "username", None) else "—"
    )
    text = (
        "ℹ️ <b>Your Info</b>\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"Username: {username}\n"
        f"Admin: {'Yes' if is_admin else 'No'}\n"
        f"Balance: <b>{user.balance}</b> 💎"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("add"))
async def admin_add_handler(message: types.Message, session: AsyncSession) -> None:
    """Admin command: /add <telegram_id> [amount] credits balance."""
    if not message.from_user or message.from_user.id not in settings.admin_ids:
        await message.reply("❌ Admins only")
        return

    assert message.text is not None
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /add <telegram_id> [amount=10]")
        return

    try:
        target_id = int(parts[1])
        amount = int(parts[2]) if len(parts) > 2 else 10
    except ValueError:
        await message.reply("Invalid arguments. Usage: /add <telegram_id> [amount=10]")
        return

    # Find or create target user
    class _TUser:
        id: int
        username: str | None
        first_name: str | None
        last_name: str | None
        language_code: str | None

        def __init__(self, id: int) -> None:  # noqa: A003 - align with Telegram schema
            self.id = id
            self.username = None
            self.first_name = None
            self.last_name = None
            self.language_code = None

    target_user = await get_or_create_user(session, _TUser(target_id))
    await credit(session, target_user, amount=amount, reason="admin_credit")
    await message.reply(
        f"✅ Credited {amount} 💎 to {target_id}. New balance: {target_user.balance}",
    )


@router.callback_query(F.data == "buy_10")
async def buy_10_callback(callback: types.CallbackQuery, session: AsyncSession) -> None:
    """Request 10 crystals: notify admins to approve with /add <user_id> 10."""
    if not callback.from_user:
        await callback.answer("No user", show_alert=True)
        return
    user = await get_or_create_user(session, callback.from_user)

    # Notify admins
    notified = 0
    admin_text = (
        "🔔 Crystal top-up request\n\n"
        f"User ID: <code>{user.telegram_id}</code>\n"
        f"Username: @{callback.from_user.username if callback.from_user.username else '—'}\n\n"
        "Approve: <code>/add {uid} 10</code>".format(uid=user.telegram_id)
    )
    for admin_id in settings.admin_ids:
        try:
            await callback.bot.send_message(admin_id, admin_text, parse_mode=ParseMode.HTML)
            notified += 1
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)

    await callback.message.edit_reply_markup(reply_markup=None)

    if notified == 0:
        await callback.message.answer(
            "❌ No admins configured. Please share your ID from /info to the admin manually.",
        )
        await callback.answer("No admins configured")
        return

    await callback.message.answer(
        (
            "📨 Request sent to admin(s). They will approve soon.\n"
            f"Your ID: <code>{user.telegram_id}</code> (also available via /info)"
        ),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Request sent")


# --- English teaching helper functions for tests ---


def count_errors_in_response(response_text: str) -> dict[str, int]:
    """Count error types in AI response by scanning markdown-like tables.

    Very simple heuristic suitable for tests.
    """
    totals = {"total": 0, "grammar": 0, "spelling": 0, "vocabulary": 0, "style": 0}
    for line in response_text.splitlines():
        if "|" in line and not set(line.strip()) <= {"|", "-", " "}:
            totals["total"] += 1
            low = line.lower()
            if "grammar" in low or "граммат" in low:
                totals["grammar"] += 1
            if "spelling" in low or "орфограф" in low:
                totals["spelling"] += 1
            if "vocabulary" in low or "лексик" in low:
                totals["vocabulary"] += 1
            if "style" in low or "стиль" in low:
                totals["style"] += 1
    return totals


def detect_language(text: str) -> str:
    """Very rough language detection for tests."""
    if re.search(r"[\u0400-\u04FF]", text):  # Cyrillic
        return "ru"
    if re.search(r"[\u4e00-\u9fff]", text):  # CJK Unified
        return "zh"
    if re.search(r"[¿¡]", text):
        return "es"
    return "en"


def detect_correction_type(original: str, response: str) -> str:
    """Detect whether response is a correction or translation."""
    orig_lang = detect_language(original)
    resp_lang = detect_language(response)
    if orig_lang != "en" and resp_lang == "en":
        return "translation"
    return "correction"
