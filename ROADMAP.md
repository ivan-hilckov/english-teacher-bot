## Goal

- Separate chat/session state to Redis.
- Store user crystals balance in PostgreSQL with an immutable transactions journal.
- Grant 100 crystals to every new user on first start.
- Spend 1 crystal per correction request.
- Simple admin top-up via bot command: `/add <telegram_id> [amount=10]`.

## Deliverables

- PostgreSQL: `users.balance` (int, default 100) and `transactions` table.
- Redis: session service with TTL for ephemeral conversation state.
- Services: `BalanceService` (credit/debit with transaction record), `SessionService` (Redis CRUD).
- Handlers: `/start`, `/profile`, `/do` debit flow, admin `/add`.
- Config: `REDIS_URL`, `ADMIN_IDS`.

## Step 0 — Dependencies & Config

1. pyproject.toml
   - Add: `redis>=5.0.0`.
2. Settings (`app/config.py`)
   - Fields: `redis_url: str = "redis://localhost:6379/0"`, `redis_session_ttl: int = 28800`, `admin_ids: list[int] = []` (parse comma-separated env).
3. Docker Compose
   - Add Redis service (memory friendly):
     ```yaml
     services:
       redis:
         image: redis:7-alpine
         ports: ["6379:6379"]
         command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
     ```
4. .env.example
   - Add: `REDIS_URL=redis://redis:6379/0`, `ADMIN_IDS=123456789`.

## Step 1 — Database Schema

1. Extend `User` model (`app/database.py`)
   - Add `balance: Mapped[int] = mapped_column(default=100)`.
2. New model `Transaction` (`app/database.py`)
   - Columns:
     - `id` PK
     - `user_id` FK → users.id (index, ondelete=CASCADE)
     - `telegram_id` BigInteger (index)
     - `amount` Integer (kopecks/crystals; positive=credit, negative=debit; not zero)
     - `reason` String(50) — e.g. `welcome_bonus`, `admin_credit`, `correction_debit`, `purchase_credit`, `refund_credit`
     - `description` String(255) | None
     - `meta` JSON | None
     - `created_at` (TimestampMixin)
3. Migration note
   - Dev: drop DB or run ALTERs; Prod: add column and create table manually (no alembic here).

## Step 2 — Redis Session Layer

1. Create `app/services/session_service.py`
   - Async Redis client wrapper with methods:
     - `get_session(telegram_id) -> dict`
     - `set_session(telegram_id, data: dict) -> None` (set with TTL)
     - `update_session(telegram_id, updates: dict) -> None`
     - `clear_session(telegram_id) -> None`
   - Key: `session:{telegram_id}`, TTL: `settings.redis_session_ttl`.
2. Middleware `DataLayerMiddleware` (new) or extend existing `DatabaseMiddleware`
   - Create Redis client at app startup, inject into middleware.
   - For each update: open DB session; attach `session` (DB) and `session_service` (Redis) to `data`.

## Step 3 — BalanceService (Atomic credits/debits)

Create `app/services/balance_service.py`:

- `async def ensure_initial_bonus(session: AsyncSession, user: User) -> None`:
  - If user just created (no transactions), add `Transaction(amount=+100, reason="welcome_bonus")` and set `user.balance = 100`.
- `async def credit(session: AsyncSession, user: User, amount: int, reason: str, description: str | None = None) -> None`:
  - Validate `amount > 0`; add transaction; `user.balance += amount`.
- `async def debit(session: AsyncSession, user: User, amount: int, reason: str, description: str | None = None) -> bool`:
  - Validate `amount > 0`; if `user.balance < amount` → return False; add transaction with `-amount`; `user.balance -= amount`; return True.

Notes:
- Wrap each call in a single DB transaction (already in middleware). For high contention: use `SELECT ... FOR UPDATE` on `User` row.

## Step 4 — Handlers

1. `/start`
   - `get_or_create_user`; if new → call `ensure_initial_bonus`.
   - Reply:
     - "привет…"
     - "У тебя {balance} 💎 кристалов"
     - "💎 (один кристал) - это один запрос на коррекцию"
     - Inline button: `[Купить 10 💎]` → callback `buy_10` (stub for now).
2. `/do <text>` and text flow
   - Before AI call: `ok = await debit(..., amount=1, reason="correction_debit")`.
   - If not ok → reply: "Недостаточно кристаллов. Нажмите 'Купить 10 💎'".
   - On success → process AI; append "+ {balance} = 💎"-style message.
3. `/profile`
   - Show current balance and the same buy button.
4. Admin `/add <telegram_id> [amount]`
   - Check `message.from_user.id in settings.admin_ids`.
   - Find or create user by `telegram_id`; `credit(..., amount or 10, reason="admin_credit")`.
   - Confirm message with new balance.

## Step 5 — Wiring in `app/main.py`

1. Create Redis client at startup:
   - `from redis.asyncio import Redis`
   - `redis = Redis.from_url(settings.redis_url, decode_responses=True)`
2. Replace/extend middleware to inject Redis alongside DB session.
3. Ensure graceful shutdown: `await redis.close()`.

## Step 6 — UI Texts & Buttons

- InlineKeyboard builder for:
  - `[Купить 10 💎]` → callback `buy_10` (MVP action: show instructions or stub credit in dev).
- Output examples (target UX):
  - Start:
    - "привет…" + balance + buy button.
  - Correction flow:
    - Before: debit 1; After: send correction and show remaining: `+ {balance} = 💎`.
  - Profile:
    - Show balance and buy button.

## Step 7 — Minimal Tests

- Unit tests for `BalanceService` credit/debit edge cases.
- Handler tests:
  - `/start` grants 100 on first contact and idempotent on repeat.
  - `/do` debits 1 when balance > 0; blocks when balance == 0.
  - Admin `/add` credits amount and requires admin.

## Step 8 — Logging & Safety

- Log every transaction: user, amount, reason.
- Validate amounts: non-zero ints; max per op (e.g., 10_000).
- Prevent negative balances.
- No secrets in code; read admins from env.

## Step 9 — Rollout Notes

- Dev: run `docker compose -f docker-compose.dev.yml up -d redis`.
- Initialize DB (drop/create) to add `balance` and `transactions`.
- Verify admin IDs in `.env`.

## Data Model (reference)

- Transaction reasons:
  - `welcome_bonus`, `admin_credit`, `purchase_credit`, `refund_credit`, `correction_debit`.
- Suggested table: `transactions(user_id, telegram_id, amount, reason, description, meta, created_at)`.

## Future (out of scope now)

- Real payments for buy button; separate Purchase table and provider webhooks.
- Rate limiting and per-chat throttling in Redis.
- Alembic migrations.


