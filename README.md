# Hello AI Bot 🤖

**AI-powered Telegram bot with OpenAI integration for intelligent conversations.**

A production-ready Telegram bot that combines the simplicity of Hello Bot template with the power of OpenAI GPT models. Chat with AI, customize roles, and maintain conversation history.

## 🎯 Key Features

- ✅ **AI-Powered Conversations**: Full OpenAI GPT integration with intelligent responses
- ✅ **Production Ready**: Deploy to VPS with single `git push` via GitHub Actions
- ✅ **Simple Architecture**: Clean, maintainable codebase optimized for AI collaboration
- ✅ **Resource Efficient**: Shared PostgreSQL, optimized for 2GB VPS deployment
- ✅ **Cost Management**: Built-in rate limiting and token usage tracking
- ✅ **Exception Handling**: Production-grade error handling with proper exception chaining

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/hello-ai-bot
cd hello-ai-bot
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
```

### 5. Start Development
```bash
# Start development environment with hot reload
docker compose -f docker-compose.dev.yml up -d

# View real-time logs  
docker compose -f docker-compose.dev.yml logs -f bot-dev
```

### 6. Test Your AI Bot
- Send `/start` to your bot → get personalized greeting
- Send `/do Tell me a joke` → AI responds with a joke
- Try `/do Write a Python function to reverse a string` → get code examples

## 🤖 AI Commands & Features

### Available Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize user profile and get greeting | `/start` |
| `/do <message>` | Send message to AI assistant | `/do Explain quantum physics simply` |

### AI Conversation Examples

**Code Generation:**
```
User: /do Write a Python function to calculate factorial
Bot: Here's a Python function to calculate factorial:

def factorial(n):
    """Calculate factorial of a non-negative integer."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

# Example usage:
print(factorial(5))  # Output: 120
```

**Explanations:**
```
User: /do What is machine learning?
Bot: Machine learning is a subset of artificial intelligence (AI) where computers learn to make decisions or predictions by finding patterns in data, without being explicitly programmed for each specific task...
```

## 🏗️ Architecture

### AI Processing Flow
```
User Message → Telegram API → aiogram Router → AI Handler
                                                    ↓
Database Session ← User Role ← OpenAI Service ← Message Processing
    ↓              ↓              ↓              ↓
Conversation Log → Token Count → AI Response → User Response
```

### Database Schema
- **`users`**: User profiles and settings
- **`user_roles`**: AI role preferences per user  
- **`conversations`**: Complete chat history with token usage tracking

### Deployment Modes
- **Development**: Polling mode with Docker Compose + hot reload
- **Production**: Webhook mode (optional) or polling mode on VPS

## 🛠️ Technology Stack

### AI & Core Framework
- **[OpenAI](https://platform.openai.com/docs)** - GPT-3.5/GPT-4 models for intelligent responses
- **[tiktoken](https://github.com/openai/tiktoken)** - Accurate token counting and cost estimation
- **[aiogram 3.0+](https://docs.aiogram.dev/)** - Modern async Telegram Bot framework
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/)** - Async PostgreSQL ORM with type safety

### Infrastructure & Production
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance webhook server
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
DEFAULT_ROLE_PROMPT=You are a helpful AI assistant.

# Database Configuration
DB_PASSWORD=secure_password_123
POSTGRES_ADMIN_PASSWORD=admin_password_456

# Rate Limiting & Cost Control
MAX_REQUESTS_PER_HOUR=60
MAX_TOKENS_PER_REQUEST=4000
```

### Optional Configuration
```env
# Environment Settings
ENVIRONMENT=development
DEBUG=true
PROJECT_NAME=hello-ai-bot

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
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres hello_ai_bot
```

### Local Development Workflow
1. **Setup**: `uv sync` → `cp .env.example .env` → add bot token and OpenAI key
2. **Start**: `docker compose -f docker-compose.dev.yml up -d`
3. **Code**: Edit files → automatic reload → test AI responses immediately  
4. **Quality**: Code passes ruff linting with proper exception chaining
5. **Deploy**: `git push origin main` → automatic VPS deployment

## 🚀 Production Deployment

### Deployment Architecture
- **Shared PostgreSQL**: Single database container for multiple bots
- **Resource Optimization**: 150MB per bot, 512MB shared database
- **Dual Mode Support**: Automatic polling mode (default) or webhook mode
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
- `OPENAI_API_KEY` - OpenAI API key for AI functionality
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
./scripts/check_vps_simple.sh    # Check VPS status
```

## 📊 Performance & Resource Usage

### Memory Optimization
- **Bot Application**: 150MB (includes AI processing)
- **Shared PostgreSQL**: 512MB (supports multiple bots)
- **Total VPS Footprint**: Optimized for 2GB RAM servers
- **Connection Pooling**: Efficient database connections

### AI Cost Management
- **Rate Limiting**: 60 requests/hour per user (configurable)
- **Token Limits**: 4000 tokens maximum per request
- **Usage Tracking**: Detailed conversation and token logging
- **Model Selection**: Cost-effective gpt-3.5-turbo by default
- **Exception Handling**: Proper API error handling with cost control

### Performance Metrics
- **AI Response Time**: <500ms for typical queries
- **Startup Time**: <30 seconds with shared infrastructure
- **Concurrent Users**: 100+ active users supported on 2GB VPS
- **Database Performance**: Async SQLAlchemy with connection pooling

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Local development and testing
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment to VPS  
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture and AI integration
- **[Database Schema](docs/DATABASE.md)** - Data models and relationships
- **[API Reference](docs/API.md)** - Bot commands and handlers
- **[Technology Stack](docs/TECHNOLOGIES.md)** - Complete tech stack reference

## 🤖 Bot Evolution History

This AI bot evolved from the Hello Bot template with systematic enhancements:

- **HB-001**: [Hello Bot Template](https://github.com/ivan-hilckov/hello-bot) - Simple greeting bot with database
- **HB-002**: **Hello AI Bot v1.0.0** - Added OpenAI GPT integration, role system, conversation history, production-grade error handling

### Version 1.0.0 Features
- ✅ **Stable Release**: Production-ready OpenAI integration
- ✅ **Full AI Capabilities**: GPT-3.5/GPT-4 models with `/do` command  
- ✅ **Role System**: Customizable AI personalities and contexts
- ✅ **Conversation Management**: Complete chat history with token tracking
- ✅ **Production Deployment**: One-command VPS deployment via GitHub Actions
- ✅ **Shared Infrastructure**: Optimized PostgreSQL for multiple bots
- ✅ **Cost Control**: Rate limiting and comprehensive usage tracking
- ✅ **Enterprise Grade**: Exception handling, security, monitoring

## 🔒 Security & Best Practices

- **No Hardcoded Secrets**: All sensitive data via environment variables
- **Exception Chaining**: Proper error handling with `raise ... from e` pattern
- **Input Validation**: Pydantic models for configuration validation
- **Resource Limits**: Memory and connection limits to prevent exhaustion
- **Database Security**: Separate users and databases for each bot instance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper exception handling
4. Ensure `uv run ruff check .` passes without errors
5. Test AI functionality thoroughly
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**🎉 STABLE v1.0.0 Released!** | **Production-ready AI bot with OpenAI integration**