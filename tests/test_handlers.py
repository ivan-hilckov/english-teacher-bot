"""
Tests for bot handlers.
"""

from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Transaction, User
from app.handlers import (
    admin_add_handler,
    count_errors_in_response,
    detect_correction_type,
    detect_language,
    profile_handler,
    start_handler,
    text_handler,
)


class TestStartHandler:
    """Test cases for /start command handler."""

    async def test_start_handler_creates_new_user(
        self, test_session: AsyncSession, telegram_user: TelegramUser
    ) -> None:
        """Test that start handler creates new user in database."""
        # Arrange - create mock message
        from unittest.mock import AsyncMock, Mock

        message = Mock()
        message.from_user = telegram_user
        message.answer = AsyncMock()

        # Act - call start handler
        await start_handler(message, test_session)

        # Assert - user should be created
        result = await test_session.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.telegram_id == telegram_user.id
        assert db_user.username == telegram_user.username
        assert db_user.first_name == telegram_user.first_name
        assert db_user.last_name == telegram_user.last_name
        assert db_user.language_code == telegram_user.language_code
        assert db_user.is_active is True

        # Assert - message should be sent
        message.answer.assert_called_once()
        greeting_text = message.answer.call_args[0][0]
        assert "Welcome to" in greeting_text
        assert "English Teacher Bot" in greeting_text
        # Display name uses username first, then full_name
        assert telegram_user.username in greeting_text

    async def test_start_grants_welcome_bonus_transaction(
        self, test_session: AsyncSession, telegram_user: TelegramUser
    ) -> None:
        """New users receive 100 crystals and a welcome_bonus transaction is recorded."""
        from unittest.mock import AsyncMock, Mock

        message = Mock()
        message.from_user = telegram_user
        message.answer = AsyncMock()

        await start_handler(message, test_session)

        # User exists with balance 100
        user = (
            await test_session.execute(select(User).where(User.telegram_id == telegram_user.id))
        ).scalar_one()
        assert user.balance == 100

        # Transaction welcome_bonus exists
        txn = (
            await test_session.execute(
                select(Transaction).where(
                    Transaction.user_id == user.id, Transaction.reason == "welcome_bonus"
                )
            )
        ).scalar_one_or_none()
        assert txn is not None

    async def test_start_handler_updates_existing_user(
        self, test_session: AsyncSession, telegram_user: TelegramUser
    ) -> None:
        """Test that start handler updates existing user."""
        # Arrange - create existing user
        existing_user = User(
            telegram_id=telegram_user.id,
            username="old_username",
            first_name="Old",
            last_name="Name",
            language_code="ru",
            is_active=True,
        )
        test_session.add(existing_user)
        await test_session.commit()
        existing_id = existing_user.id

        # Arrange - create mock message
        from unittest.mock import AsyncMock, Mock

        message = Mock()
        message.from_user = telegram_user
        message.answer = AsyncMock()

        # Act - call start handler
        await start_handler(message, test_session)

        # Assert - user should be updated, not recreated
        result = await test_session.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.id == existing_id  # Same database ID
        assert db_user.username == telegram_user.username  # Updated
        assert db_user.first_name == telegram_user.first_name  # Updated
        assert db_user.last_name == telegram_user.last_name  # Updated
        assert db_user.language_code == telegram_user.language_code  # Updated

    async def test_start_handler_no_user(self, test_session: AsyncSession) -> None:
        """Test that start handler handles missing user gracefully."""
        # Arrange - create mock message without user
        from unittest.mock import AsyncMock, Mock

        message = Mock()
        message.from_user = None
        message.answer = AsyncMock()

        # Act - call start handler
        await start_handler(message, test_session)

        # Assert - appropriate message should be sent
        message.answer.assert_called_once()
        greeting_text = message.answer.call_args[0][0]
        assert "Welcome to" in greeting_text
        assert "English Teacher Bot" in greeting_text
        assert "Unknown" in greeting_text


class TestEnglishTeachingFunctions:
    """Test cases for English teaching helper functions."""

    def test_count_errors_in_response(self) -> None:
        """Test error counting from AI response."""
        # Test response with correction table
        response_with_errors = """
        | Original | Error Type | Explanation | Correction |
        |----------|------------|-------------|------------|
        | I are | Grammar | Wrong verb | I am |
        | someware | Spelling | Misspelled | somewhere |
        """

        result = count_errors_in_response(response_with_errors)
        assert result["total"] >= 2  # Should detect table rows
        assert result["grammar"] >= 1
        assert result["spelling"] >= 1

        # Test response without errors
        response_no_errors = "This is a perfect sentence."
        result = count_errors_in_response(response_no_errors)
        assert result["total"] == 0

    def test_detect_correction_type(self) -> None:
        """Test correction type detection."""
        # Test correction (English with errors)
        original_english = "I are student"
        correction_response = "| I are | Grammar | Wrong verb | I am |"

        result = detect_correction_type(original_english, correction_response)
        assert result == "correction"

        # Test translation (non-English input)
        original_russian = "Привет, как дела?"
        translation_response = "Hello, how are you?"

        result = detect_correction_type(original_russian, translation_response)
        assert result == "translation"

    def test_detect_language(self) -> None:
        """Test language detection."""
        # Test Russian
        russian_text = "Привет, как дела?"
        assert detect_language(russian_text) == "ru"

        # Test English
        english_text = "Hello, how are you?"
        assert detect_language(english_text) == "en"

        # Test Spanish
        spanish_text = "¿Cómo estás?"
        assert detect_language(spanish_text) == "es"

        # Test Chinese
        chinese_text = "你好吗？"
        assert detect_language(chinese_text) == "zh"


class TestBalanceAndHandlers:
    """Tests for balance debit/credit and related handlers."""

    async def test_text_handler_debits_on_message(
        self, test_session: AsyncSession, telegram_user: TelegramUser, monkeypatch
    ) -> None:
        """Text message should debit 1 crystal and call AI service."""
        from unittest.mock import AsyncMock, Mock

        # Seed user with default balance (100 via start)
        start_msg = Mock()
        start_msg.from_user = telegram_user
        start_msg.answer = AsyncMock()
        await start_handler(start_msg, test_session)

        # Mock AI response and chat action
        async def mock_generate_response(_self, _text: str):
            return ("OK", 10)

        monkeypatch.setattr(
            "app.handlers.OpenAIService.generate_response", mock_generate_response, raising=True
        )

        # We attach a dummy bot instance directly to the message, so no global monkeypatch needed

        # Text message
        msg = Mock()
        msg.from_user = telegram_user
        msg.text = "I are student"
        msg.reply = AsyncMock()
        msg.answer = AsyncMock()

        # Bot attribute required by handler
        class _DummyBot:
            async def send_chat_action(self, *args, **kwargs):
                return None

        msg.bot = _DummyBot()

        # Act
        await text_handler(msg, test_session)

        # Assert balance decreased by 1 and transaction recorded
        user = (
            await test_session.execute(select(User).where(User.telegram_id == telegram_user.id))
        ).scalar_one()
        assert user.balance == 99
        txn = (
            (
                await test_session.execute(
                    select(Transaction)
                    .where(Transaction.user_id == user.id, Transaction.reason == "correction_debit")
                    .order_by(Transaction.id.desc())
                )
            )
            .scalars()
            .first()
        )
        assert txn is not None and txn.amount == -1

    async def test_text_handler_insufficient_funds(
        self, test_session: AsyncSession, telegram_user: TelegramUser, monkeypatch
    ) -> None:
        """When balance is zero, text handler should block and show message."""
        from unittest.mock import AsyncMock, Mock

        # Create user
        start_msg = Mock()
        start_msg.from_user = telegram_user
        start_msg.answer = AsyncMock()
        await start_handler(start_msg, test_session)

        # Set balance to 0
        user = (
            await test_session.execute(select(User).where(User.telegram_id == telegram_user.id))
        ).scalar_one()
        user.balance = 0
        await test_session.commit()

        # Mock AI to ensure it won't be called if insufficient
        async def mock_generate_response(_self, _text: str):
            return ("OK", 10)

        monkeypatch.setattr(
            "app.handlers.OpenAIService.generate_response", mock_generate_response, raising=True
        )

        # Prepare message
        msg = Mock()
        msg.from_user = telegram_user
        msg.text = "Hello"
        msg.reply = AsyncMock()
        msg.answer = AsyncMock()

        class _DummyBot:
            async def send_chat_action(self, *args, **kwargs):
                return None

        msg.bot = _DummyBot()

        await text_handler(msg, test_session)

        # Should inform about insufficient crystals
        assert msg.reply.await_args is not None
        reply_text = msg.reply.await_args.args[0]
        assert "Not enough crystals" in reply_text

    async def test_admin_add_handler_credits_balance(
        self, test_session: AsyncSession, telegram_user: TelegramUser, monkeypatch
    ) -> None:
        """Admins can credit user balance via /add command."""
        from unittest.mock import AsyncMock, Mock

        # Seed calling user (admin) and target user
        start_msg = Mock()
        start_msg.from_user = telegram_user
        start_msg.answer = AsyncMock()
        await start_handler(start_msg, test_session)

        # Make the caller an admin
        monkeypatch.setattr("app.handlers.settings.admin_ids", [telegram_user.id], raising=True)

        # Prepare admin add message
        msg = Mock()
        msg.from_user = telegram_user
        msg.text = "/add 111111111 5"
        msg.reply = AsyncMock()

        await admin_add_handler(msg, test_session)

        # Target user created and credited
        target_user = (
            await test_session.execute(select(User).where(User.telegram_id == 111111111))
        ).scalar_one()
        assert target_user.balance == 105  # 100 initial + 5 credited

        # Transaction recorded
        txn = (
            await test_session.execute(
                select(Transaction).where(
                    Transaction.user_id == target_user.id, Transaction.reason == "admin_credit"
                )
            )
        ).scalar_one_or_none()
        assert txn is not None and txn.amount == 5

    async def test_profile_handler_shows_balance(
        self, test_session: AsyncSession, telegram_user: TelegramUser
    ) -> None:
        from unittest.mock import AsyncMock, Mock

        start_msg = Mock()
        start_msg.from_user = telegram_user
        start_msg.answer = AsyncMock()
        await start_handler(start_msg, test_session)

        msg = Mock()
        msg.from_user = telegram_user
        msg.answer = AsyncMock()
        await profile_handler(msg, test_session)

        text = msg.answer.await_args.args[0]
        assert "Balance" in text or "Баланс" in text
