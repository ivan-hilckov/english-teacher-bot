# Create English Teacher Bot from Hello AI Bot Template

You are helping create English Teacher Bot based on the Hello AI Bot template (v1.0.0). This template uses a simplified architecture (~320 lines) optimized for rapid development and AI collaboration.

## Bot Specification

**English Teacher Bot - Detailed Implementation Plan**

### Basic Information
- **Bot Name**: English Teacher Bot
- **Bot Username**: @english_teacher_bot (to be created via @BotFather)
- **Description**: AI-powered English tutor that corrects grammar/spelling errors and translates text to English with detailed explanations
- **Bot ID**: HB-003 (third bot in Hello Bot genealogy after hello-ai-bot v1.0.0)
- **Port**: 8001 (avoiding hello-ai-bot port 8000)
- **Database**: english_teacher_bot_db

### Core Functionality
**Primary Features**:
1. **Error Correction**: Analyze English text and provide detailed correction tables with error types and explanations
2. **Translation**: Translate text from any language to natural English with language detection
3. **Learning Analytics**: Track user's correction history and English learning progress

**Commands**:
- `/start` - Welcome message explaining English teaching functionality and user registration
- `/do <text>` - Process text through AI English tutor for correction or translation
- Direct text messages - Automatically process any text for English improvement

### Example Correction Output Format
```
# Таблица исправления ошибок

| Оригинал | Тип ошибки | Объяснение | Исправление |
|----------|------------|------------|-------------|
| someware | Орфографическая | Неправильное написание слова | somewhere |
| give | Грамматическая | Прошедшее время → неправильный глагол | gave |
| are book | Грамматическая | Должен быть притяжательный падеж + артикль | a book |

### Исправленный вариант:
Somewhere in the 90s, my grandfather gave me a book about the BASIC programming language.
```

### Technical Requirements
- **Database Tables**: User + UserRole + Conversation + CorrectionHistory (new table for tracking progress)
- **External APIs**: OpenAI GPT API for English tutoring intelligence
- **Special Dependencies**: tiktoken (token counting), openai (AI client) - already included in hello-ai-bot template
- **Deployment**: VPS alongside Hello Bot and hello-ai-bot using shared PostgreSQL architecture

## Development Roadmap

### Phase 1: Repository Setup (30 minutes)

#### 1.1 Clone and Initialize
```bash
# Clone template repository
git clone https://github.com/your-username/hello-ai-bot english-teacher-bot
cd english-teacher-bot

# Setup Python environment
uv sync
```

#### 1.2 Configuration Updates
- [ ] **Update `app/config.py`**:
  - `project_name: str = "English Teacher Bot"`
  - `server_port: int = 8001`
  - `database_url: str = "postgresql+asyncpg://english_teacher_bot_user:password@localhost:5432/english_teacher_bot_db"`

- [ ] **Update `docker-compose.yml`**:
  - Container name: `english_teacher_bot_app`
  - Port mapping: `"8001:8001"`
  - Database name: `english_teacher_bot_db`
  - Environment variable: `SERVER_PORT: 8001`

- [ ] **Create new bot token**:
  - Message @BotFather → `/newbot` → @english_teacher_bot
  - Add `BOT_TOKEN` to `.env` file

- [ ] **Update `README.md`**:
  - Title: "English Teacher Bot"
  - Description: AI-powered English tutor
  - Port information: 8001

### Phase 2: Core English Teaching Features (2 hours)

#### 2.1 Database Enhancement (`app/database.py`)
Add new model for tracking corrections:
```python
class CorrectionHistory(Base, TimestampMixin):
    """Track user's English correction history."""
    __tablename__ = "correction_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    correction_type: Mapped[str] = mapped_column(String(20))  # 'correction' or 'translation'
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
```

#### 2.2 AI Role Customization (`app/config.py`)
Update default role prompt:
```python
default_role_prompt: str = Field(
    default="""You are an expert English tutor. Your job is to:

1. CORRECTION MODE: If text is in English with errors, provide:
   - Detailed error table: | Original | Error Type | Explanation | Correction |
   - Complete corrected version
   - Error types: Grammar, Spelling, Style, Vocabulary

2. TRANSLATION MODE: If text is in another language:
   - Detect language
   - Translate to natural English
   - Provide only the English translation

Be precise, educational, and helpful.""",
    description="English teacher role prompt"
)
```

#### 2.3 Enhanced Handlers (`app/handlers.py`)

**Update start handler:**
```python
@router.message(Command("start"))
async def start_handler(message: types.Message, session: AsyncSession) -> None:
    """English Teacher Bot welcome message."""
    greeting = (
        f"🎓 Welcome to <b>English Teacher Bot</b>, {user.display_name}!\n\n"
        f"📚 <b>What I can do:</b>\n"
        f"• Correct English grammar and spelling errors\n"
        f"• Translate text from any language to English\n"
        f"• Provide detailed error explanations\n\n"
        f"📋 <b>Commands:</b>\n"
        f"• /do &lt;text&gt; - Process text for correction/translation\n"
        f"• Just send any text - I'll automatically help!\n\n"
        f"📊 <b>Example correction:</b>\n"
        f"You: 'I are student'\n"
        f"Me: Grammar error: 'I am a student'"
    )
```

**Add correction processing function:**
```python
async def process_english_teaching(message: types.Message, session: AsyncSession, text: str) -> None:
    """Process text for English correction or translation."""
    # Get or create user
    user = await get_or_create_user(session, message.from_user)
    
    # Get user role for English teaching
    user_role = await get_or_create_user_role(session, user.id)
    
    # Generate AI response with English teaching role
    openai_service = OpenAIService()
    ai_response, tokens = await openai_service.generate_response(
        user_message=text,
        role_prompt=user_role.role_prompt,
        model=settings.default_ai_model
    )
    
    # Save to CorrectionHistory
    correction_history = CorrectionHistory(
        user_id=user.id,
        original_text=text,
        corrected_text=ai_response,
        error_count=count_errors_in_response(ai_response),
        correction_type=detect_correction_type(text, ai_response),
        detected_language=detect_language(text)
    )
    session.add(correction_history)
    
    # Save conversation
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
    
    # Send response
    await message.reply(ai_response, parse_mode=ParseMode.HTML)
```

### Phase 3: Enhancement and Optimization (1 hour)

#### 3.1 Error Classification System
- [ ] Implement error type detection (Grammar, Spelling, Style, Vocabulary)
- [ ] Add error counting logic for progress tracking
- [ ] Create language detection helper functions

#### 3.2 Response Formatting
- [ ] Optimize markdown table formatting for Telegram
- [ ] Add clear separation between original and corrected text
- [ ] Implement educational explanations for each error type

#### 3.3 Learning Analytics
- [ ] Add user statistics tracking (errors per session, improvement over time)
- [ ] Implement correction history queries
- [ ] Create progress reporting functionality

#### 3.4 Helper Functions
```python
def count_errors_in_response(ai_response: str) -> int:
    """Count errors mentioned in AI response."""
    # Logic to parse error table and count errors
    
def detect_correction_type(original: str, response: str) -> str:
    """Detect if this was correction or translation."""
    # Return 'correction' or 'translation'
    
def detect_language(text: str) -> str | None:
    """Basic language detection."""
    # Simple heuristics or integration with language detection
```

### Phase 4: Production Deployment (30 minutes)

#### 4.1 Docker Configuration
Update `docker-compose.yml` for production:
```yaml
services:
  english-teacher-bot:
    image: ${BOT_IMAGE}
    container_name: english_teacher_bot_app
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://english_teacher_bot_user:${DB_PASSWORD}@postgres-shared:5432/english_teacher_bot_db
      BOT_TOKEN: ${ENGLISH_TEACHER_BOT_TOKEN}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SERVER_PORT: 8001
    ports:
      - "8001:8001"
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 64M
    restart: unless-stopped
    networks:
      - shared_network
```

#### 4.2 GitHub Secrets Configuration
Add to repository secrets:
- `ENGLISH_TEACHER_BOT_TOKEN` - New bot token from @BotFather
- Update deployment workflow to include english-teacher-bot

#### 4.3 VPS Deployment
- [ ] Deploy to VPS with port 8001 (avoiding hello-ai-bot port 8000)
- [ ] Configure shared PostgreSQL with english_teacher_bot_db database
- [ ] Test production deployment with multiple bots running
- [ ] Verify health checks and resource limits

#### 4.4 Testing and Verification
```bash
# Test deployment
git push origin main  # Automated deployment via GitHub Actions

# Verify bot functionality
# 1. Send /start command
# 2. Test English correction: "I are student"
# 3. Test translation: "Привет, как дела?"
# 4. Check database for CorrectionHistory entries
```

## Template Customization Checklist

### Required Changes (Must Do):
- [ ] **Project Name**: Update to "English Teacher Bot" in `app/config.py`
- [ ] **Repository Name**: Rename to "english-teacher-bot" 
- [ ] **Bot Token**: Get new token from @BotFather for @english_teacher_bot
- [ ] **Database Name**: Update to "english_teacher_bot_db" in environment variables
- [ ] **Port Configuration**: Change SERVER_PORT to 8001 in all configs
- [ ] **README.md**: Update title, description, and features list
- [ ] **docker-compose.yml**: Update container names and port mappings

### Core Implementation Changes:
- [ ] **Database Model**: Add CorrectionHistory model in `app/database.py`
- [ ] **AI Role Prompt**: Customize for English tutoring in `app/config.py`
- [ ] **Start Handler**: Update welcome message in `app/handlers.py`
- [ ] **Processing Logic**: Implement english teaching functions
- [ ] **Error Classification**: Add helper functions for error detection

### Enhancement Features:
- [ ] **Correction Tables**: Format error tables for Telegram markdown
- [ ] **Language Detection**: Basic language identification logic  
- [ ] **Learning Analytics**: Track user progress and error patterns
- [ ] **Response Formatting**: Optimize for educational explanations
- [ ] **Progress Tracking**: Implement correction history queries

### Deployment Configuration:
- [ ] **GitHub Secrets**: Add ENGLISH_TEACHER_BOT_TOKEN
- [ ] **VPS Setup**: Configure for port 8001 alongside existing bots
- [ ] **Database Migration**: Setup english_teacher_bot_db
- [ ] **Health Checks**: Verify bot functionality and resource limits

## AI Collaboration Instructions

When working with AI assistants on this bot:

### Context to Provide:
```
This is English Teacher Bot built from Hello AI Bot template (v1.0.0):
- ~320 total lines of code across 5 main files (hello-ai-bot base)
- Direct database operations (no service layer)
- Async SQLAlchemy 2.0 with PostgreSQL
- aiogram 3.0+ for Telegram API  
- OpenAI API integration with role-based prompting
- Simple middleware for database sessions
- Production deployment via Docker and GitHub Actions
- Shared PostgreSQL architecture for multiple bots

Bot purpose: AI-powered English tutor that corrects grammar errors and translates text
Core features: Error correction tables, translation, learning progress tracking
Deployment: VPS port 8001 alongside hello-ai-bot (port 8000)
```

### Effective Prompts:
- "Generate detailed correction table showing Original | Error Type | Explanation | Correction"
- "Add language detection to translate non-English text to English"  
- "Create CorrectionHistory model to track user's English learning progress"
- "Implement error type classification (grammar, spelling, style, vocabulary)"
- "Format markdown tables for Telegram with proper escaping"
- "Add educational explanations for English grammar rules"

### Architecture Constraints:
- Keep total codebase under 400 lines (following hello-ai-bot pattern)
- Use direct database operations in handlers
- No service layer or complex abstractions
- Simple error handling with standard logging
- One file per major component
- Memory limit: 128MB per bot instance
- Port 8001 for english-teacher-bot (avoiding conflicts)

## File Structure After Customization

```
english-teacher-bot/
├── app/
│   ├── config.py          # English teacher settings, port 8001, AI role prompt
│   ├── database.py        # User + UserRole + Conversation + CorrectionHistory
│   ├── handlers.py        # English correction and translation handlers
│   ├── middleware.py      # Database middleware (unchanged from hello-ai-bot)
│   ├── main.py           # Entry point with port 8001
│   └── services/
│       ├── __init__.py   # Services package
│       └── openai_service.py  # OpenAI integration (unchanged from hello-ai-bot)
├── prompts/              # AI collaboration templates (including this START.md)
├── tests/                # English correction and translation tests
├── docs/                 # English teaching methodology documentation
├── scripts/              # Deployment and development scripts
├── docker-compose.yml    # Production deployment with port 8001
├── docker-compose.dev.yml # Development environment
├── pyproject.toml        # Project dependencies and configuration
├── .env.example          # Environment variables template
└── README.md            # English Teacher Bot information
```

## Bot Genealogy

Add this to your new bot's README.md:

```markdown
## Bot Genealogy
- **Parent Template**: Hello AI Bot (HB-002) v1.0.0
- **Bot ID**: HB-003
- **Created**: 2025
- **Purpose**: AI-powered English tutor for grammar correction and translation
- **Port**: 8001 (shared VPS deployment)
- **GitHub**: https://github.com/your-username/english-teacher-bot
```

## Success Criteria

Your bot is ready when:
- [ ] All configuration files updated (config.py, docker-compose.yml, README.md)
- [ ] CorrectionHistory model added to database.py
- [ ] English teacher role prompt implemented in config.py
- [ ] Start handler updated with English teaching welcome message
- [ ] Error correction processing with table formatting works
- [ ] Translation functionality from various languages works
- [ ] Deploys successfully to VPS on port 8001 alongside hello-ai-bot (port 8000)
- [ ] Database english_teacher_bot_db created and accessible
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Production health checks and resource limits verified
- [ ] CorrectionHistory tracking saves user progress to database

## Testing Commands

```bash
# Development testing
./scripts/start_dev_simple.sh  # Start development environment
uv run pytest tests/ -v       # Run all tests

# Production deployment testing
git push origin main           # Deploy via GitHub Actions

# Bot functionality testing
# 1. Send /start → verify English teacher welcome message
# 2. Send "I are student" → verify grammar correction with error table
# 3. Send "Привет, как дела?" → verify translation to English
# 4. Check database for CorrectionHistory entries
# 5. Verify port 8001 accessibility and health checks
```

## Quick Reference Commands

```bash
# Setup
git clone https://github.com/your-username/hello-ai-bot english-teacher-bot
cd english-teacher-bot
uv sync
cp .env.example .env
# Edit .env with ENGLISH_TEACHER_BOT_TOKEN and other variables

# Development  
./scripts/start_dev_simple.sh
docker compose -f docker-compose.dev.yml logs -f bot-dev

# Production deployment
git push origin main

# Monitoring
docker logs english_teacher_bot_app
curl http://localhost:8001/health  # Health check endpoint
```

Ready to build your English Teacher Bot! Follow the phases step-by-step and use AI collaboration for complex implementation details.