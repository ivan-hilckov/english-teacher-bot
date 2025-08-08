# Redis Session + PostgreSQL User Architecture Plan

## Strategic Architecture Overview

### **Core Separation Strategy**
Implement dual-layer data architecture optimized for payment system integration:

- **Redis**: Fast session state, conversation context, payment flows, temporary data
- **PostgreSQL**: Persistent user profiles, transaction history, subscription data
- **Clean Interface**: Repository pattern with clear data boundaries

### **Payment Integration Benefits**
- **Session Isolation**: Payment flows don't affect user data integrity
- **Fast State Management**: Redis handles rapid payment state transitions
- **Atomic Operations**: PostgreSQL ensures payment transaction consistency  
- **Scalability**: Independent scaling of session vs user data layers

## Current Architecture Issues

### 1. **Mixed Concerns in Single Database**
Current PostgreSQL stores both:
- Persistent user data (should stay in PostgreSQL)
- Temporary session state (should move to Redis)

### 2. **Payment System Challenges**
- No conversation state management for multi-step payment flows
- User data mixed with transaction state creates complexity
- Difficult to implement payment timeouts and cleanup

### 3. **Session Management Problems**
- No persistent conversation context between messages
- Limited ability to track user journey states
- Poor separation for concurrent user interactions

## Proposed Architecture

### **Redis Session Layer**
```python
# Session data structure in Redis
{
    f"session:{telegram_id}": {
        "conversation_state": "payment_amount_input",
        "payment_flow": {
            "product_id": "premium_subscription",
            "amount": 999,
            "currency": "RUB",
            "step": "confirm_payment",
            "expires_at": "2024-01-01T12:00:00Z"
        },
        "ai_context": {
            "last_correction": "...",
            "learning_topic": "grammar",
            "message_count": 15
        },
        "temp_data": {},
        "created_at": "2024-01-01T10:00:00Z",
        "expires_at": "2024-01-01T18:00:00Z"  # 8 hour TTL
    }
}
```

### **PostgreSQL User Layer**
```python
# Enhanced User model for payments
class User(Base, TimestampMixin):
    # Core user data (unchanged)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    
    # Payment-related persistent data
    subscription_status: Mapped[str] = mapped_column(String(50), default="free")
    subscription_expires_at: Mapped[datetime | None] = mapped_column()
    total_paid: Mapped[int] = mapped_column(default=0)  # kopecks
    
    # Learning analytics
    lessons_completed: Mapped[int] = mapped_column(default=0)
    accuracy_score: Mapped[float] = mapped_column(default=0.0)

class PaymentTransaction(Base, TimestampMixin):
    """Persistent payment records"""
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column()  # kopecks
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(50))
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255))
```

## Implementation Plan

### **Phase 1: Redis Integration (Week 1)**

#### 1.1 Add Redis Dependencies
```python
# pyproject.toml additions
redis = "^5.0.0"
pydantic-redis = "^0.4.0"
```

#### 1.2 Redis Configuration
```python
# app/config.py
class Settings(BaseSettings):
    # Existing settings...
    redis_url: str = Field(default="redis://localhost:6379/0")
    session_ttl: int = Field(default=28800)  # 8 hours
```

#### 1.3 Session Service Layer
```python
# app/services/session_service.py
from redis.asyncio import Redis
from typing import Any

class SessionService:
    def __init__(self, redis: Redis):
        self.redis = redis
        
    async def get_session(self, telegram_id: int) -> dict[str, Any]:
        """Get user session data"""
        
    async def set_session(self, telegram_id: int, data: dict) -> None:
        """Set session data with TTL"""
        
    async def update_session(self, telegram_id: int, updates: dict) -> None:
        """Partial session update"""
        
    async def clear_session(self, telegram_id: int) -> None:
        """Clear user session"""
```

### **Phase 2: Payment Flow Architecture (Week 2)**

#### 2.1 Payment State Machine
```python
# app/services/payment_service.py
from enum import Enum

class PaymentState(Enum):
    IDLE = "idle"
    SELECTING_PRODUCT = "selecting_product"
    CONFIRMING_AMOUNT = "confirming_amount"
    PROCESSING_PAYMENT = "processing_payment"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"

class PaymentFlow:
    def __init__(self, session_service: SessionService):
        self.session = session_service
        
    async def start_payment_flow(self, telegram_id: int, product_id: str):
        """Initialize payment session"""
        
    async def handle_payment_step(self, telegram_id: int, user_input: str):
        """Process payment flow steps"""
```

#### 2.2 Enhanced Middleware
```python
# app/middleware.py
class DataLayerMiddleware(BaseMiddleware):
    """Inject both PostgreSQL session and Redis session"""
    
    async def __call__(self, handler, event, data):
        # PostgreSQL session (existing)
        async with AsyncSessionLocal() as pg_session:
            # Redis session (new)
            async with redis_pool.get_connection() as redis:
                session_service = SessionService(redis)
                
                data["pg_session"] = pg_session
                data["session_service"] = session_service
                
                try:
                    result = await handler(event, data)
                    await pg_session.commit()
                    return result
                except Exception:
                    await pg_session.rollback()
                    raise
```

### **Phase 3: Repository Pattern Implementation (Week 3)**

#### 3.1 User Repository (PostgreSQL)
```python
# app/repositories/user_repository.py
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_or_create_user(self, telegram_user) -> User:
        """Handle persistent user data only"""
        
    async def update_subscription(self, user_id: int, status: str, expires_at: datetime):
        """Update subscription data"""
        
    async def record_payment(self, user_id: int, amount: int, transaction_id: str):
        """Record completed payment"""
```

#### 3.2 Session Repository (Redis)
```python
# app/repositories/session_repository.py
class SessionRepository:
    def __init__(self, session_service: SessionService):
        self.session = session_service
        
    async def get_conversation_state(self, telegram_id: int) -> str:
        """Get current conversation state"""
        
    async def set_payment_context(self, telegram_id: int, context: dict):
        """Set payment flow context"""
        
    async def get_ai_context(self, telegram_id: int) -> dict:
        """Get AI conversation context"""
```

### **Phase 4: Handler Refactoring (Week 4)**

#### 4.1 Payment Handlers
```python
# app/handlers/payment_handlers.py
@router.message(Command("subscribe"))
async def subscribe_handler(
    message: types.Message, 
    pg_session: AsyncSession,
    session_service: SessionService
):
    user_repo = UserRepository(pg_session)
    session_repo = SessionRepository(session_service)
    
    user = await user_repo.get_or_create_user(message.from_user)
    await session_repo.set_conversation_state(user.telegram_id, "payment_product_selection")
    
    # Show payment options...
```

#### 4.2 Enhanced AI Handlers
```python
# app/handlers/ai_handlers.py
async def process_ai_message(
    message: types.Message,
    pg_session: AsyncSession, 
    session_service: SessionService,
    text: str
):
    session_repo = SessionRepository(session_service)
    
    # Get conversation context from Redis
    ai_context = await session_repo.get_ai_context(message.from_user.id)
    
    # Process with context...
    # Update context in Redis...
```

## Technology Integration

### **Docker Compose Updates**
```yaml
# docker-compose.yml additions
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
      
volumes:
  redis_data:
```

### **Configuration Management**
```python
# Environment variables
REDIS_URL=redis://localhost:6379/0
SESSION_TTL=28800  # 8 hours
PAYMENT_SESSION_TTL=1800  # 30 minutes for payment flows
```

## Benefits for Payment Integration

### **1. Isolated Payment Flows**
- Payment state independent of user profile data
- Easy to implement payment timeouts and cleanup
- Concurrent payment flows don't interfere

### **2. Fast State Transitions**
- Redis provides microsecond response times for state updates
- Payment confirmation flows feel instant to users
- Real-time payment status updates

### **3. Data Integrity**
- PostgreSQL ensures payment transaction ACID properties
- Redis handles temporary state that can be safely lost
- Clear separation prevents data corruption

### **4. Scalability**
- Redis sessions can be sharded by user ID
- PostgreSQL optimized for complex payment queries
- Independent scaling of each layer

## Migration Strategy

### **Week 1: Infrastructure Setup**
- Add Redis to development environment
- Create session service layer
- Basic session CRUD operations

### **Week 2: Session Integration** 
- Update middleware to inject session service
- Migrate conversation state to Redis
- Test dual-layer data access

### **Week 3: Payment Foundation**
- Implement payment state machine
- Create payment flow repositories
- Add subscription management

### **Week 4: Handler Migration**
- Refactor existing handlers
- Implement payment handlers
- Full integration testing

## Success Metrics

### **Performance**
- Session operations < 10ms (Redis)
- User queries < 100ms (PostgreSQL)
- Payment flows < 500ms end-to-end

### **Reliability**
- Zero session data loss during Redis restarts
- Payment transaction integrity maintained
- Graceful degradation when Redis unavailable

### **Maintainability**
- Clear separation between persistent and temporary data
- Easy to add new payment providers
- Simple testing of individual layers

---

**Priority**: HIGH - Essential for payment system integration
**Effort**: 4 weeks full implementation
**Risk**: MEDIUM - Requires careful data migration and testing
