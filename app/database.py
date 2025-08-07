"""
Simple database module combining models, session, and engine.
"""

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


# Base class for all models
class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""

    __abstract__: bool = True


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    """Telegram user model."""

    __tablename__: str = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Telegram user information
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # User state
    is_active: Mapped[bool] = mapped_column(default=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    @property
    def display_name(self) -> str:
        """Get the best display name for the user."""
        return self.username or self.full_name or f"User{self.telegram_id}"

    @property
    def full_name(self) -> str:
        """Get full name from first_name and last_name."""
        parts = [self.first_name, self.last_name]
        return " ".join(part for part in parts if part)


class UserRole(Base, TimestampMixin):
    """User's AI assistant role preference."""

    __tablename__: str = "user_roles"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    # Role information
    role_name: Mapped[str] = mapped_column(String(50), default="helpful_assistant")
    role_prompt: Mapped[str] = mapped_column(Text, default="You are a helpful AI assistant.")


class Conversation(Base, TimestampMixin):
    """User conversation history."""

    __tablename__: str = "conversations"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Conversation data
    user_message: Mapped[str] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(50))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    role_used: Mapped[str] = mapped_column(String(50))


class CorrectionHistory(Base, TimestampMixin):
    """Track user's English correction and translation history."""

    __tablename__: str = "correction_history"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Correction data
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    correction_type: Mapped[str] = mapped_column(String(20))  # 'correction' or 'translation'
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Learning analytics
    errors_grammar: Mapped[int] = mapped_column(Integer, default=0)
    errors_spelling: Mapped[int] = mapped_column(Integer, default=0)
    errors_vocabulary: Mapped[int] = mapped_column(Integer, default=0)
    errors_style: Mapped[int] = mapped_column(Integer, default=0)


# Create engine and session with optimized pool for shared PostgreSQL
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=2,  # Reduced per bot (shared instance)
    max_overflow=3,  # Reduced overflow
    pool_timeout=30,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Helper functions for AI functionality
async def get_or_create_user_role(session: AsyncSession, user_id: int) -> UserRole:
    """Get or create user role with default settings."""
    stmt = select(UserRole).where(UserRole.user_id == user_id)
    result = await session.execute(stmt)
    user_role = result.scalar_one_or_none()

    if not user_role:
        user_role = UserRole(
            user_id=user_id,
            role_name="helpful_assistant",
            role_prompt=settings.default_role_prompt,
        )
        session.add(user_role)
        await session.commit()

    return user_role


async def get_conversation_history(
    session: AsyncSession, user_id: int, limit: int = 5
) -> list[Conversation]:
    """Get recent conversation history for a user."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def save_correction_history(
    session: AsyncSession,
    user_id: int,
    original_text: str,
    corrected_text: str,
    correction_type: str,
    error_count: int = 0,
    detected_language: str | None = None,
    errors_grammar: int = 0,
    errors_spelling: int = 0,
    errors_vocabulary: int = 0,
    errors_style: int = 0,
) -> CorrectionHistory:
    """Save correction history for learning analytics."""
    correction_history = CorrectionHistory(
        user_id=user_id,
        original_text=original_text,
        corrected_text=corrected_text,
        error_count=error_count,
        correction_type=correction_type,
        detected_language=detected_language,
        errors_grammar=errors_grammar,
        errors_spelling=errors_spelling,
        errors_vocabulary=errors_vocabulary,
        errors_style=errors_style,
    )
    session.add(correction_history)
    await session.commit()
    return correction_history


async def get_user_progress(session: AsyncSession, user_id: int) -> dict[str, int]:
    """Get user's learning progress statistics."""
    stmt = select(CorrectionHistory).where(CorrectionHistory.user_id == user_id)
    result = await session.execute(stmt)
    corrections = list(result.scalars().all())

    if not corrections:
        return {
            "total_corrections": 0,
            "total_translations": 0,
            "total_errors": 0,
            "grammar_errors": 0,
            "spelling_errors": 0,
            "vocabulary_errors": 0,
            "style_errors": 0,
        }

    return {
        "total_corrections": len([c for c in corrections if c.correction_type == "correction"]),
        "total_translations": len([c for c in corrections if c.correction_type == "translation"]),
        "total_errors": sum(c.error_count for c in corrections),
        "grammar_errors": sum(c.errors_grammar for c in corrections),
        "spelling_errors": sum(c.errors_spelling for c in corrections),
        "vocabulary_errors": sum(c.errors_vocabulary for c in corrections),
        "style_errors": sum(c.errors_style for c in corrections),
    }
