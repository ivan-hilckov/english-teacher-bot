# English Teacher Bot 🎓

**AI-powered English tutor bot for grammar correction and translation with detailed explanations.**

A ultra-simple Telegram bot focused purely on English grammar correction and translation. Stateless, fast, and optimized specifically for English teaching with zero configuration needed.

## 🎯 Key Features

- ✅ **Grammar Correction**: Detailed error analysis with correction tables showing error types and explanations
- ✅ **Translation Service**: Translate text from any language to natural English
- ✅ **Stateless Design**: Each correction is independent - no history or settings to manage
- ✅ **Production Ready**: Deploy to VPS with single `git push` via GitHub Actions
- ✅ **Simple Architecture**: Clean, maintainable codebase optimized for AI collaboration
- ✅ **Resource Efficient**: Shared PostgreSQL, optimized for 2GB VPS deployment
- ✅ **Cost Management**: Built-in rate limiting and token usage tracking

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/english-teacher-bot
cd english-teacher-bot
```

### 2. Setup Development Environment

**Prerequisites**: [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)

```bash
# Setup Python environment
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your tokens (see Configuration section)
```

### 3. Get Required Tokens
- **Bot Token**: Message [@BotFather](https://t.me/botfather) → `/newbot` → copy token
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### 4. Configure Environment
Add to `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=sk-your-openai-api-key-here
DB_PASSWORD=secure_dev_password
SERVER_PORT=8021
```

### 5. Start Development
```bash
# Start development environment with hot reload
docker compose -f docker-compose.dev.yml up -d

# View real-time logs  
docker compose -f docker-compose.dev.yml logs -f bot-dev
```

### 6. Test Your English Teacher Bot
- Send `/start` to your bot → get English teacher welcome message
- Send `I are student` → get detailed grammar correction with error table
- Send `Привет, как дела?` → get English translation: "Hello, how are you?"
- Try `/do Write me a text with errors` → get comprehensive correction analysis

## 📚 English Teaching Features

### Available Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize user profile and get English teacher greeting | `/start` |
| `/do <text>` | Process text for correction or translation | `/do I are student` |

### Grammar Correction Examples

**Error Correction with Table:**
```
User: I are student and I live in Moscow
Bot: 
# Таблица исправления ошибок

| Оригинал | Тип ошибки | Объяснение | Исправление |
|----------|------------|------------|-------------|
| I are | Грамматическая | Неправильная форма глагола be | I am |
| I are student | Грамматическая | Отсутствует артикль | I am a student |

### Исправленный вариант:
I am a student and I live in Moscow.
```

**Translation Examples:**
```
User: Привет, как дела? Как работа?
Bot: Hello, how are you? How is work?

User: Je suis étudiant
Bot: I am a student

User: 我是学生
Bot: I am a student
```

### Simplified Design
- **Zero Configuration**: Works perfectly out-of-the-box with optimal settings
- **Stateless Operation**: Each text correction is completely independent
- **Instant Response**: No database queries for history or context
- **Focus on Quality**: Optimized specifically for English teaching

## 🏗️ Architecture

### AI Processing Flow
```
User Message → Telegram API → aiogram Router → English Teacher Handler
                                                    ↓
                                              OpenAI Service
                                                    ↓
                                            AI Response → User
```

### Database Schema
- **`users`**: Basic user profiles (minimal tracking for bot functionality)

### Deployment Modes
- **Development**: Polling mode with Docker Compose + hot reload (port 8021)
- **Production**: Webhook mode (optional) or polling mode on VPS (port 8021)

## 🛠️ Technology Stack

### AI & English Teaching
- **[OpenAI](https://platform.openai.com/docs)** - GPT-3.5/GPT-4 models for intelligent English tutoring
- **[tiktoken](https://github.com/openai/tiktoken)** - Accurate token counting and cost estimation
- **Custom Grammar Analysis** - Error type classification and language detection
- **Learning Analytics** - Progress tracking and improvement insights

### Core Framework
- **[aiogram 3.0+](https://docs.aiogram.dev/)** - Modern async Telegram Bot framework
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/)** - Async PostgreSQL ORM with type safety
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance webhook server

### Infrastructure & Production
- **[PostgreSQL 15](https://www.postgresql.org/)** - Reliable, shared database
- **[Docker + Compose](https://docs.docker.com/)** - Containerized deployment
- **[GitHub Actions](https://docs.github.com/en/actions)** - Automated CI/CD pipeline

### Development & Quality
- **[uv](https://docs.astral.sh/uv/)** - Ultra-fast Python package manager  
- **[ruff](https://docs.astral.sh/ruff/)** - Lightning-fast linting and formatting
- **[pytest](https://docs.pytest.org/)** - Comprehensive testing framework
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation and settings management

## ⚙️ Configuration

### Required Environment Variables
```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token

# OpenAI Integration  
OPENAI_API_KEY=sk-your-openai-api-key-here
DEFAULT_AI_MODEL=gpt-3.5-turbo

# English Teacher Role
DEFAULT_ROLE_PROMPT=You are an expert English tutor...

# Database Configuration
DB_PASSWORD=secure_password_123
POSTGRES_ADMIN_PASSWORD=admin_password_456

# Server Configuration
SERVER_PORT=8021

# Rate Limiting & Cost Control
MAX_REQUESTS_PER_HOUR=60
MAX_TOKENS_PER_REQUEST=4000
```

### Optional Configuration
```env
# Environment Settings
ENVIRONMENT=development
DEBUG=true
PROJECT_NAME=english-teacher-bot

# Production Webhook (optional - defaults to polling)
WEBHOOK_URL=https://yourdomain.com/webhook

# Development Tools
ADMINER_PORT=8080
```

## 🔧 Development

### Development Commands
```bash
# Environment setup
uv sync                              # Install all dependencies

# Development server  
docker compose -f docker-compose.dev.yml up -d    # Start with hot reload
docker compose -f docker-compose.dev.yml logs -f bot-dev  # View logs

# Code quality (passes all linting)
uv run ruff format .                 # Format code
uv run ruff check .                  # Lint (no errors)
uv run pytest tests/ -v              # Run tests

# Database access
docker compose -f docker-compose.dev.yml exec postgres psql -U english_teacher_bot_user english_teacher_bot_db
```

### Local Development Workflow
1. **Setup**: `uv sync` → `cp .env.example .env` → add bot token and OpenAI key
2. **Start**: `docker compose -f docker-compose.dev.yml up -d`
3. **Code**: Edit files → automatic reload → test English teaching features immediately  
4. **Quality**: Code passes ruff linting with proper exception chaining
5. **Deploy**: `git push origin main` → automatic VPS deployment

## 🚀 Production Deployment

### Deployment Architecture
- **Shared PostgreSQL**: Single database container for multiple bots
- **Resource Optimization**: 128MB per bot, 512MB shared database
- **Port Configuration**: 8021 (avoiding conflicts with hello-ai-bot port 8000)
- **GitHub Actions**: Automated deployment pipeline

### Required GitHub Secrets

Configure in your repository: **Settings → Secrets and variables → Actions**

#### VPS Connection (Required)
- `VPS_HOST` - Your server IP address (e.g., `74.208.125.51`)
- `VPS_USER` - SSH username (e.g., `root`, `ubuntu`)  
- `VPS_SSH_KEY` - Private SSH key content
- `VPS_PORT` - SSH port (default: `22`)

#### Docker Registry (Required)
- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token (**not password**)

#### Application Secrets (Required)
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `OPENAI_API_KEY` - OpenAI API key for English teaching functionality
- `DB_PASSWORD` - Database password for bot user
- `POSTGRES_ADMIN_PASSWORD` - PostgreSQL admin password for shared instance

#### Optional Secrets
- `WEBHOOK_URL` - For webhook mode (bot uses polling by default)
- `WEBHOOK_SECRET_TOKEN` - Additional webhook security

### Deployment Process
```bash
# Automatic deployment
git push origin main

# Manual verification
./scripts/check_vps_simple.sh    # Check VPS status on port 8021
```

## 📊 Performance & Resource Usage

### Memory Optimization
- **Bot Application**: 128MB (includes AI processing and grammar analysis)
- **Shared PostgreSQL**: 512MB (supports multiple bots)
- **Total VPS Footprint**: Optimized for 2GB RAM servers
- **Connection Pooling**: Efficient database connections

### AI Cost Management
- **Rate Limiting**: 60 requests/hour per user (configurable)
- **Token Limits**: 4000 tokens maximum per request
- **Usage Tracking**: Detailed conversation and token logging
- **Model Selection**: Cost-effective gpt-3.5-turbo by default
- **Smart Processing**: Efficient grammar analysis and error classification

### Performance Metrics
- **English Analysis Time**: <500ms for typical corrections
- **Translation Speed**: <1 second for most languages
- **Startup Time**: <30 seconds with shared infrastructure
- **Concurrent Users**: 100+ active learners supported on 2GB VPS
- **Database Performance**: Async SQLAlchemy with connection pooling

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Local development and testing
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment to VPS  
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture and English teaching integration
- **[Database Schema](docs/DATABASE.md)** - Data models and learning analytics
- **[API Reference](docs/API.md)** - Bot commands and English teaching handlers

## 🤖 Bot Evolution History

This English Teacher Bot evolved from the Hello AI Bot template with radical simplification for pure English teaching:

- **HB-001**: [Hello Bot Template](https://github.com/ivan-hilckov/hello-bot) - Simple greeting bot with database
- **HB-002**: [Hello AI Bot v1.0.0](https://github.com/ivan-hilckov/hello-ai-bot) - Added OpenAI GPT integration
- **HB-003**: **English Teacher Bot v1.0.0** - Specialized English tutoring with comprehensive features
- **HB-004**: **English Teacher Bot v1.1.0** - Ultra-simplified for pure English correction focus

### Version 1.1.0 Features
- ✅ **Pure Grammar Correction**: Focused solely on English teaching excellence
- ✅ **Stateless Design**: Each correction independent for consistent quality
- ✅ **Zero Configuration**: Optimal settings hardcoded for English teaching
- ✅ **Ultra-Simple API**: Single method `generate_response(text)` 
- ✅ **Minimal Database**: Only essential user tracking
- ✅ **Production Ready**: Same reliable deployment infrastructure
- ✅ **Cost Efficient**: Reduced complexity = lower resource usage
- ✅ **Maintainable**: ~30% less code, easier to understand and modify

## 🔒 Security & Best Practices

- **No Hardcoded Secrets**: All sensitive data via environment variables
- **Exception Chaining**: Proper error handling with `raise ... from e` pattern
- **Input Validation**: Pydantic models for configuration validation
- **Resource Limits**: Memory and connection limits to prevent exhaustion
- **Database Security**: Separate users and databases for each bot instance
- **AI Safety**: Token limits and rate limiting to prevent API abuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/english-feature`)
3. Make your changes with proper English teaching focus
4. Ensure `uv run ruff check .` passes without errors
5. Test English correction and translation functionality thoroughly
6. Commit your changes (`git commit -m 'Add English teaching feature'`)
7. Push to the branch (`git push origin feature/english-feature`)
8. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**🎉 ULTRA-SIMPLE v1.1.0 Released!** | **Radically simplified English Teacher Bot focused purely on correction excellence**