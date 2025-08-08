Мне надо что бы ты проанализировал эти файлы.  

очень важный prompts/START.md - этот файл проанализировать в первую очердь

```
app/services/__init__.py
app/services/openai_service.py
app/__init__.py
app/config.py
app/database.py
app/handlers.py
app/main.py
app/middleware.py

документация: 

docs/API.md
docs/ARCHITECTURE.md
docs/DATABASE.md
docs/DEPLOYMENT.md
docs/DEVELOPMENT.md
docs/GITHUB_SECRETS.md
docs/TECHNOLOGIES.md

тесты:

tests/__init__.py
tests/conftest.py
tests/test_handlers.py
tests/test_webhook.py

деплой и девелопмент:

scripts/postgresql.conf
scripts/README.md
scripts/check_shared_postgres.sh
scripts/check_vps_simple.sh
scripts/deploy_simple.sh
scripts/manage_postgres.sh
scripts/start_dev_simple.sh
scripts/stop_dev.sh
scripts/init_db.sql
pyproject.toml
docker-compose.dev.yml
docker-compose.postgres.yml
docker-compose.yml
Dockerfile.dev
Dockerfile
.env.example
```

Раньше это был бот https://github.com/ivan-hilckov/hello-ai-bot, я создал на основе него копию https://github.com/ivan-hilckov/english-teacher-bot

В предыдушей итерации с помощбю AI был сгененрирован план создания english-teacher-bot в файле `prompts/START.md`

Тебе нужно составить подробный пошаговый план того переделки hello-ai-bot в english-teacher-bot. Учти все места где надо будет переименовать hello-ai-bot в english-teacher-bot. Продумай реализациию AI части. Обновление документации. Обновление тестов. Операйся на START.md

Сохрани план в PLAN.md в корне проекта. 

Начни вполнять план шаг за шагом. 

Макисимально закончи создание english-teacher-bot из hello-ai-bot.

Остановись на моменте запустить локально для проверки

