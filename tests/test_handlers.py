"""
Tests for bot handlers.
"""

from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import User
from app.handlers import (
    count_errors_in_response,
    detect_correction_type,
    detect_language,
    start_handler,
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
