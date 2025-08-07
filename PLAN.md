# English Teacher Bot Transformation Plan

Complete step-by-step plan to transform hello-ai-bot into english-teacher-bot following the specifications in `prompts/START.md`.

## Overview

**Source Bot**: hello-ai-bot (HB-002) v1.0.0
**Target Bot**: english-teacher-bot (HB-003)
**Purpose**: AI-powered English tutor for grammar correction and translation
**Architecture**: Keep simplified hello-ai-bot structure (~320 lines)

## Phase 1: Configuration and Project Setup

### 1.1 Project Identification Changes

- [ ] **app/config.py**:
  - Update `project_name` from "Hello AI Bot" to "English Teacher Bot"
  - Update `server_port` from 8000 to 8021
  - Update `database_url` to use "english_teacher_bot_db" and "english_teacher_bot_user"
  - Update `default_role_prompt` to English teacher role

- [ ] **pyproject.toml**:
  - Update `name` from "hello-ai-bot" to "english-teacher-bot"
  - Update `description` to English teacher functionality
  - Keep all dependencies (no changes needed)

- [ ] **.env.example**:
  - Update `PROJECT_NAME` from "hello-ai-bot" to "english-teacher-bot"
  - Update comments and descriptions for English teacher bot
  - Add `SERVER_PORT=8021` example

### 1.2 Docker Configuration Updates

- [ ] **docker-compose.yml**:
  - Update container name from `${PROJECT_NAME}_app` to use "english_teacher_bot_app"
  - Update port mapping from 8000 to 8021
  - Update `SERVER_PORT` environment variable to 8021
  - Keep memory limits (128M) and other settings

- [ ] **docker-compose.dev.yml**:
  - Update port mappings to 8021
  - Update container names
  - Update volume mounts and service names

- [ ] **Dockerfile** and **Dockerfile.dev**:
  - Update `EXPOSE` port from 8000 to 8021
  - Keep all other settings unchanged

## Phase 2: Database Model Enhancement

### 2.1 Add CorrectionHistory Model

- [ ] **app/database.py**:
  - Add new `CorrectionHistory` model with fields:
    - `id`: Primary key
    - `user_id`: Foreign key to users table
    - `original_text`: User's input text
    - `corrected_text`: AI-corrected version
    - `error_count`: Number of errors found
    - `correction_type`: 'correction' or 'translation'
    - `detected_language`: Source language (for translations)
    - `created_at`, `updated_at`: Timestamps
  - Add helper functions for English teaching operations

### 2.2 Database Helper Functions

- [ ] Add functions to **app/database.py**:
  - `save_correction_history()`: Save correction/translation to database
  - `get_user_progress()`: Get user's learning statistics
  - `count_user_errors()`: Count errors by type for analytics

## Phase 3: AI Service Customization

### 3.1 English Teacher Role Prompt

- [ ] **app/config.py** - Update `default_role_prompt`:
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

### 3.2 Response Processing Functions

- [ ] **app/handlers.py** - Add helper functions:
  - `count_errors_in_response()`: Parse AI response to count errors
  - `detect_correction_type()`: Determine if correction or translation
  - `detect_language()`: Basic language detection
  - `format_correction_table()`: Format markdown tables for Telegram

## Phase 4: Handler Implementation

### 4.1 Update Start Handler

- [ ] **app/handlers.py** - Update `start_handler()`:
  - Change welcome message to English teacher introduction
  - Explain correction and translation features
  - Update command examples for English learning
  - Remove hello-ai-bot specific references

### 4.2 Update AI Processing Handler

- [ ] **app/handlers.py** - Update `process_ai_message()`:
  - Add CorrectionHistory saving after AI response
  - Implement error counting and classification
  - Add language detection logic
  - Format responses for educational purposes

### 4.3 Update Command Handlers

- [ ] **app/handlers.py** - Update predefined responses:
  - Remove hello-ai-bot creator/repository references
  - Add English teacher bot specific information
  - Update GitHub repository links
  - Add English learning tips and features

## Phase 5: Project Documentation Updates

### 5.1 Main Documentation

- [ ] **README.md**:
  - Update title to "English Teacher Bot 🎓"
  - Update description to English tutoring features
  - Update examples with grammar correction and translation
  - Update GitHub repository URLs
  - Update port references (8000 → 8021)
  - Update bot genealogy section

### 5.2 Technical Documentation

- [ ] **docs/ARCHITECTURE.md**:
  - Update for English teaching flow
  - Add CorrectionHistory model documentation
  - Update AI processing pipeline for education

- [ ] **docs/DATABASE.md**:
  - Add CorrectionHistory table schema
  - Update relationship diagrams
  - Add English learning analytics queries

- [ ] **docs/API.md**:
  - Update command descriptions for English teaching
  - Add correction and translation examples
  - Update response format documentation

- [ ] **docs/DEPLOYMENT.md**:
  - Update port configuration (8021)
  - Update environment variables
  - Update GitHub secrets for English teacher bot

- [ ] **docs/DEVELOPMENT.md**:
  - Update local development instructions
  - Update testing commands for English features
  - Update Docker commands with new ports

## Phase 6: Testing Updates

### 6.1 Test Configuration

- [ ] **tests/conftest.py**:
  - Update test database configuration
  - Add fixtures for CorrectionHistory model
  - Update test settings for English teacher bot

### 6.2 Handler Tests

- [ ] **tests/test_handlers.py**:
  - Update start handler tests for new welcome message
  - Add tests for correction processing
  - Add tests for translation functionality
  - Add tests for CorrectionHistory saving
  - Update mock AI responses for English teaching

### 6.3 New Test Cases

- [ ] Add new test files:
  - Test error counting and classification
  - Test language detection logic
  - Test markdown table formatting
  - Test correction history analytics

## Phase 7: Scripts and Deployment

### 7.1 Development Scripts

- [ ] **scripts/start_dev_simple.sh**:
  - Update port references to 8021
  - Update container names
  - Keep all other functionality

- [ ] **scripts/check_vps_simple.sh**:
  - Update port checks to 8021
  - Update container name checks
  - Update health check URLs

### 7.2 Database Scripts

- [ ] **scripts/init_db.sql**:
  - Update database name to "english_teacher_bot_db"
  - Update user name to "english_teacher_bot_user"
  - Keep same permissions and structure

### 7.3 PostgreSQL Configuration

- [ ] **scripts/postgresql.conf**:
  - Keep existing optimizations
  - No changes needed for English teacher bot

## Phase 8: Final Integration and Testing

### 8.1 Environment Configuration

- [ ] Create new **.env** file:
  - Copy from .env.example
  - Set PROJECT_NAME=english-teacher-bot
  - Set SERVER_PORT=8021
  - Add new BOT_TOKEN for @english_teacher_bot
  - Keep same OPENAI_API_KEY

### 8.2 Local Testing

- [ ] **Functionality Tests**:
  - Test `/start` command shows English teacher welcome
  - Test grammar correction: "I are student" → proper correction table
  - Test translation: "Привет, как дела?" → English translation
  - Test CorrectionHistory database saves
  - Test port 8021 accessibility

### 8.3 Production Preparation

- [ ] **GitHub Secrets**:
  - Add `ENGLISH_TEACHER_BOT_TOKEN`
  - Update deployment workflow if needed
  - Verify VPS resource allocation for port 8021

## Implementation Priority Order

### Critical Changes (Must Complete):
1. **Configuration** (`app/config.py`) - Project name, port, database, AI role
2. **Database Model** (`app/database.py`) - Add CorrectionHistory model
3. **Handlers** (`app/handlers.py`) - English teaching welcome and processing
4. **Docker Config** (`docker-compose.yml`) - Port 8021 configuration
5. **Project Info** (`pyproject.toml`, `README.md`) - Basic identification

### Important Changes (Should Complete):
6. **AI Integration** - Error counting, language detection, formatting
7. **Tests** (`tests/`) - Update for English teaching functionality
8. **Documentation** (`docs/`) - Update technical specifications
9. **Scripts** (`scripts/`) - Update development and deployment tools

### Optional Enhancements (If Time Permits):
10. **Advanced Analytics** - User progress tracking, learning insights
11. **Enhanced Formatting** - Better correction table display
12. **Multiple Languages** - Improved language detection
13. **Performance Optimization** - Response time improvements

## Success Criteria

The transformation is complete when:
- [ ] Bot responds to `/start` with English teacher welcome message
- [ ] Bot corrects English text with detailed error tables
- [ ] Bot translates foreign text to English
- [ ] CorrectionHistory model saves learning data to database
- [ ] All configuration uses port 8021 and english_teacher_bot names
- [ ] Local development works with `./scripts/start_dev_simple.sh`
- [ ] All tests pass with `uv run pytest tests/ -v`
- [ ] README.md accurately describes English Teacher Bot functionality

## File-by-File Transformation Checklist

### Core Application Files:
- [ ] `app/config.py` - Project settings, port 8021, English teacher role
- [ ] `app/database.py` - Add CorrectionHistory model + helper functions
- [ ] `app/handlers.py` - English teaching handlers and AI processing
- [ ] `app/main.py` - Port configuration (minimal changes)
- [ ] `app/middleware.py` - No changes needed
- [ ] `app/services/openai_service.py` - No changes needed

### Project Configuration:
- [ ] `pyproject.toml` - Project name and description
- [ ] `.env.example` - Project name and port references
- [ ] `README.md` - Complete rewrite for English Teacher Bot
- [ ] `docker-compose.yml` - Port 8021 and container names
- [ ] `docker-compose.dev.yml` - Development port configuration
- [ ] `Dockerfile` - Expose port 8021
- [ ] `Dockerfile.dev` - Development port configuration

### Documentation:
- [ ] `docs/ARCHITECTURE.md` - English teaching architecture
- [ ] `docs/DATABASE.md` - CorrectionHistory schema
- [ ] `docs/API.md` - English teaching commands
- [ ] `docs/DEPLOYMENT.md` - Port 8021 deployment
- [ ] `docs/DEVELOPMENT.md` - Updated development guide
- [ ] `docs/GITHUB_SECRETS.md` - English teacher bot secrets
- [ ] `docs/TECHNOLOGIES.md` - Updated tech stack info

### Tests:
- [ ] `tests/conftest.py` - Test configuration updates
- [ ] `tests/test_handlers.py` - English teaching handler tests
- [ ] `tests/test_webhook.py` - Port 8021 webhook tests

### Scripts:
- [ ] `scripts/start_dev_simple.sh` - Port 8021 development
- [ ] `scripts/check_vps_simple.sh` - Port 8021 health checks
- [ ] `scripts/deploy_simple.sh` - Updated deployment
- [ ] `scripts/init_db.sql` - English teacher bot database
- [ ] `scripts/manage_postgres.sh` - Database management
- [ ] `scripts/postgresql.conf` - No changes needed
- [ ] `scripts/README.md` - Updated script documentation

## Estimated Timeline

- **Phase 1-2 (Config + Database)**: 45 minutes
- **Phase 3-4 (AI + Handlers)**: 60 minutes  
- **Phase 5-6 (Docs + Tests)**: 45 minutes
- **Phase 7-8 (Scripts + Testing)**: 30 minutes
- **Total**: ~3 hours for complete transformation

## Notes

- Keep simplified architecture from hello-ai-bot (~320 lines total)
- Maintain all existing hello-ai-bot optimizations and patterns
- Focus on core English teaching functionality over advanced features
- Ensure compatibility with shared PostgreSQL VPS deployment
- Preserve all production-ready aspects of original template
