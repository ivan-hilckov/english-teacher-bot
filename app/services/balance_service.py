"""Balance service for credit/debit operations with immutable transactions.

Follows SQLAlchemy 2.0 async patterns and single-transaction usage provided by middleware.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Transaction, User


async def ensure_initial_bonus(session: AsyncSession, user: User) -> None:
    """Grant initial 100 crystals to brand new users once.

    If the user has no transactions, create a welcome_bonus transaction and set balance to 100.
    """

    stmt = select(Transaction.id).where(Transaction.user_id == user.id)
    existing = (await session.execute(stmt)).first()
    if existing is None:
        user.balance = 100
        session.add(
            Transaction(
                user_id=user.id,
                telegram_id=user.telegram_id,
                amount=100,
                reason="welcome_bonus",
                description="Initial bonus for new user",
            )
        )


async def credit(
    session: AsyncSession,
    user: User,
    amount: int,
    reason: str,
    description: str | None = None,
) -> None:
    """Credit user's balance by positive amount and record transaction."""
    if amount <= 0:
        raise ValueError("Credit amount must be positive")

    user.balance += amount
    session.add(
        Transaction(
            user_id=user.id,
            telegram_id=user.telegram_id,
            amount=amount,
            reason=reason,
            description=description,
        )
    )


async def debit(
    session: AsyncSession,
    user: User,
    amount: int,
    reason: str,
    description: str | None = None,
) -> bool:
    """Debit user's balance by positive amount and record transaction.

    Returns True on success, False if insufficient funds.
    """
    if amount <= 0:
        raise ValueError("Debit amount must be positive")

    if user.balance < amount:
        return False

    user.balance -= amount
    session.add(
        Transaction(
            user_id=user.id,
            telegram_id=user.telegram_id,
            amount=-amount,
            reason=reason,
            description=description,
        )
    )
    return True
