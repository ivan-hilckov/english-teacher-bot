# План архитектурных изменений: Разделение сессий и пользователей

## Текущая архитектура и проблемы

### 1. Смешение ответственностей
- **SQLAlchemy сессии** (транзакции БД) + **пользовательские сессии** (состояние чата)
- Двойное управление транзакциями в middleware и handlers
- Отсутствие персистентного состояния между запросами

### 2. Ограничения для платежной системы
- Нет хранения состояния платежа между запросами
- Нет возможности отслеживать многошаговые операции
- Пользовательские данные смешаны с техническими

### 3. Производительность
- Каждый запрос создает новую DB-сессию через middleware
- Нет кэширования пользовательских данных
- Лишние запросы к PostgreSQL для получения базовой информации

## Новая архитектура: Разделение на слои

### Слой 1: PostgreSQL - Постоянные данные пользователей
```python
# app/database.py - только постоянные данные
class User(Base, TimestampMixin):
    """Persistent user data in PostgreSQL."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Платежные данные
    subscription_status: Mapped[str] = mapped_column(String(50), default="free")
    subscription_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    total_messages: Mapped[int] = mapped_column(default=0)
    payment_provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

### Слой 2: Redis - Временные сессии и состояния
```python
# app/session.py - новый модуль для работы с сессиями
from redis import Redis
import json
from typing import Dict, Any, Optional

class UserSession:
    """User session stored in Redis."""
    
    def __init__(self, redis_client: Redis, user_id: int, ttl: int = 3600):
        self.redis = redis_client
        self.user_id = user_id
        self.ttl = ttl
        self.key = f"session:{user_id}"
    
    async def get(self, field: str) -> Optional[Any]:
        """Get field from user session."""
        data = await self.redis.hget(self.key, field)
        return json.loads(data) if data else None
    
    async def set(self, field: str, value: Any) -> None:
        """Set field in user session."""
        await self.redis.hset(self.key, field, json.dumps(value))
        await self.redis.expire(self.key, self.ttl)
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all session data."""
        data = await self.redis.hgetall(self.key)
        return {k: json.loads(v) for k, v in data.items()}
    
    async def clear(self) -> None:
        """Clear user session."""
        await self.redis.delete(self.key)

# Типичные поля сессии:
# - "payment_state": "waiting_card" | "processing" | "completed"
# - "payment_amount": 1000  # в копейках
# - "payment_provider": "stripe" | "tinkoff"
# - "conversation_context": {...}  # контекст диалога
# - "current_lesson": {"id": 123, "step": 2}
```

### Слой 3: Unified Service - Объединение данных
```python
# app/services/user_service.py
class UserService:
    """Service to work with user data from both storages."""
    
    def __init__(self, db_session: AsyncSession, redis_client: Redis):
        self.db = db_session
        self.redis = redis_client
    
    async def get_user_context(self, telegram_user_id: int) -> UserContext:
        """Get complete user context (DB + Redis)."""
        # Получаем постоянные данные из PostgreSQL
        user = await self._get_or_create_user(telegram_user_id)
        
        # Получаем временные данные из Redis
        session = UserSession(self.redis, telegram_user_id)
        session_data = await session.get_all()
        
        return UserContext(
            user_id=user.id,
            telegram_id=user.telegram_id,
            display_name=user.display_name,
            subscription_status=user.subscription_status,
            is_premium=user.subscription_status != "free",
            session_data=session_data,
            session=session
        )
    
    async def _get_or_create_user(self, telegram_user_id: int) -> User:
        """Get or create user in PostgreSQL (без коммитов!)."""
        stmt = select(User).where(User.telegram_id == telegram_user_id)
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=telegram_user_id)
            self.db.add(user)
            await self.db.flush()  # Только flush для получения ID
        
        return user

@dataclass
class UserContext:
    """Complete user context from all storages."""
    user_id: int
    telegram_id: int
    display_name: str
    subscription_status: str
    is_premium: bool
    session_data: Dict[str, Any]
    session: UserSession
```

## Обновленный Middleware для работы с двумя хранилищами

```python
# app/middleware.py
class UnifiedMiddleware(BaseMiddleware):
    """Middleware для инъекции DB сессии и Redis клиента."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def __call__(self, handler, event, data) -> Any:
        async with AsyncSessionLocal() as db_session:
            try:
                # Инъектируем сервис пользователя в хендлеры
                user_service = UserService(db_session, self.redis)
                data["user_service"] = user_service
                data["db_session"] = db_session  # На случай прямого доступа
                
                result = await handler(event, data)
                await db_session.commit()  # Единственный commit
                return result
            except Exception:
                await db_session.rollback()
                raise
```

## Примеры использования в handlers

### Payment Handler - Многошаговый платеж
```python
@router.message(Command("subscribe"))
async def subscribe_handler(message: types.Message, user_service: UserService) -> None:
    """Handle subscription command."""
    context = await user_service.get_user_context(message.from_user.id)
    
    if context.is_premium:
        await message.answer("✅ Вы уже подписаны!")
        return
    
    # Начинаем процесс оплаты - сохраняем в Redis
    await context.session.set("payment_state", "selecting_plan")
    await context.session.set("payment_started_at", time.time())
    
    await message.answer(
        "💳 Выберите план:\n"
        "1. Месячный - 299₽\n"
        "2. Годовой - 2999₽ (скидка 17%)",
        reply_markup=payment_keyboard
    )

@router.callback_query(F.data.startswith("plan_"))
async def select_plan_handler(callback: CallbackQuery, user_service: UserService) -> None:
    """Handle plan selection."""
    context = await user_service.get_user_context(callback.from_user.id)
    
    # Проверяем состояние
    payment_state = await context.session.get("payment_state")
    if payment_state != "selecting_plan":
        await callback.answer("❌ Сессия истекла")
        return
    
    plan_id = callback.data.split("_")[1]
    amount = 299 if plan_id == "monthly" else 2999
    
    # Сохраняем выбор в Redis
    await context.session.set("selected_plan", plan_id)
    await context.session.set("payment_amount", amount)
    await context.session.set("payment_state", "waiting_payment")
    
    # Создаем платеж через провайдера
    payment_url = await create_payment(
        amount=amount,
        user_id=context.telegram_id,
        description=f"Подписка {plan_id}"
    )
    
    await callback.message.edit_text(
        f"💳 К оплате: {amount}₽\n"
        f"📱 Перейдите по ссылке: {payment_url}"
    )
```

### Lesson Handler - Контекст урока
```python
@router.message(Command("lesson"))
async def lesson_handler(message: types.Message, user_service: UserService) -> None:
    """Handle lesson command."""
    context = await user_service.get_user_context(message.from_user.id)
    
    if not context.is_premium:
        await message.answer("🔒 Уроки доступны только по подписке")
        return
    
    # Получаем текущий урок из сессии
    current_lesson = await context.session.get("current_lesson")
    
    if not current_lesson:
        # Начинаем новый урок
        lesson_id = await get_next_lesson_for_user(context.user_id)
        current_lesson = {"id": lesson_id, "step": 1}
        await context.session.set("current_lesson", current_lesson)
    
    lesson_data = await get_lesson_step(
        current_lesson["id"], 
        current_lesson["step"]
    )
    
    await message.answer(
        f"📚 Урок {current_lesson['id']}, шаг {current_lesson['step']}\n\n"
        f"{lesson_data['content']}"
    )
```

## Преимущества новой архитектуры

### ✅ Разделение ответственностей
- **PostgreSQL**: Постоянные данные (профиль, подписка, статистика)
- **Redis**: Временные данные (сессия, состояние платежа, контекст)
- **UserService**: Единая точка доступа к пользователю

### ✅ Платежная система
- Многошаговые платежи с сохранением состояния
- Откат к любому шагу при ошибке
- Таймауты сессий для безопасности
- Независимость от SQL транзакций

### ✅ Производительность
- Кэширование пользователей в Redis
- Меньше запросов к PostgreSQL
- Быстрый доступ к контексту сессии

### ✅ Масштабируемость  
- Redis можно кластеризовать
- PostgreSQL только для критичных данных
- Простое добавление новых полей сессии

## План поэтапной реализации

### Этап 1: Подготовка инфраструктуры
1. Добавить Redis в docker-compose.yml и requirements
2. Добавить Redis конфигурацию в settings
3. Создать модуль app/session.py с классом UserSession

### Этап 2: Расширение User модели
1. Добавить поля для платежей в User модель
2. Создать миграцию для новых полей
3. Обновить тесты для новой модели

### Этап 3: UserService
1. Создать app/services/user_service.py  
2. Реализовать UserContext и UserService
3. Написать тесты для сервиса

### Этап 4: Новый Middleware
1. Создать UnifiedMiddleware 
2. Заменить старый DatabaseMiddleware
3. Обновить main.py для инъекции Redis

### Этап 5: Рефакторинг handlers
1. Обновить существующие хендлеры для работы с UserService
2. Убрать прямую работу с session из хендлеров  
3. Добавить примеры платежных хендлеров

### Этап 6: Тестирование
1. E2E тесты для платежного флоу
2. Тесты для сессий в Redis
3. Нагрузочные тесты

## Конфигурация

### Docker Compose
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Settings
```python
# app/config.py
class Settings(BaseSettings):
    # Существующие настройки...
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_session_ttl: int = Field(default=3600)  # 1 час
    
    # Payment
    payment_session_ttl: int = Field(default=1800)  # 30 минут
    payment_provider: str = Field(default="stripe")
```

### Requirements
```
# Добавить в pyproject.toml
redis>=5.0.0
```

## Безопасность

### 🔒 Сессии
- TTL для всех сессий (1 час по умолчанию)
- Очистка просроченных платежных сессий  
- Шифрование чувствительных данных в Redis

### 🔒 Платежи
- Короткий TTL для платежных сессий (30 минут)
- Валидация состояния на каждом шаге
- Логирование всех платежных операций

### 🔒 Данные
- Разделение критичных и временных данных
- Бэкапы только PostgreSQL
- Redis как кэш с возможностью полной очистки

## Результат

Гибкая двухслойная архитектура:
- **Быстрые сессии** в Redis для интерактивности
- **Надежные данные** в PostgreSQL для долгосрочного хранения  
- **Простая интеграция** платежных систем
- **Масштабируемость** под рост пользователей