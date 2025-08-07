Мы успешно реализовали самый просто бот который взаимодействует AI через api и зафиксировали версию. 

Мне нужно что бы ты проанализировал изменения которые были произведены в следющих файлах:

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

проведя анализ составь план создания следующего бота который будет создан на основе текущего hello-ai-bot

для шаблона возьми файл prompts/START.md 

Название следующего бота: english-teacher-bot

Функция бота (коротко): откорректировать или перевести на английский запрос пользователя

Требования:
- на команду /start бот рассказывает какая его функция 
- /do текст после и просто текст в чат пропускаеться через чат gpt с ролью репититор
- деплой на тот же VPS на котором сейчас запущен hello-bot и hello-ai-bot

Пример как я понимаю смысл слова "откорректировать":

Пользователь: "In the past someware in 90-s my grandfather give me are book, something about basic programing language, this book has are text of game whre two gorilas threw banana in ethch other. Can you find this game and code of them?"

Бот: Думаю...

Бот: Ошибки и исправления: 

# Таблица исправления ошибок

| Оригинал | Тип ошибки | Объяснение | Исправление |
|----------|------------|------------|-------------|
| someware | Орфографическая | Неправильное написание слова | somewhere |
| 90-s | Орфографическая/стилистическая | Так годы не пишутся | the 90s |
| give | Грамматическая | Прошедшее время → неправильный глагол | gave |
| are book | Грамматическая | Должен быть притяжательный падеж + артикль | a book |
| basic programing | Орфографическая | Название языка → заглавные буквы + опечатка в "programming" | BASIC programming |
| has are text | Грамматическая | Ошибка в глаголе + "are" лишнее | had the text или included the code |
| whre | Орфографическая | Опечатка в слове | where |
| gorilas | Орфографическая | Опечатка в слове | gorillas |
| threw banana in ethch other | Грамматическая и стилистическая | "threw bananas at each other" — правильная конструкция | threw bananas at each other |
| code of them | Грамматическая | Неловкая конструкция | the code for it или its source code |

---

### Исправленный вариант:

Somewhere in the 90s, my grandfather gave me a book about the BASIC programming language. It included the code for a game where two gorillas threw bananas at each other.

Can you help me find this game and its source code?

⸻

### Если хочешь более неформальный/дружелюбный стиль — вот пример:

Back in the 90s, my grandfather gave me a book about BASIC. It had the code for a game where two gorillas threw bananas at each other. Do you know what game that was — and where I can find its code?

Пример как я понимаю смысл слова "перевести":

---

Пользователь: "Подскажи рецепт котлет из шуки?"

Бот: "tell me a recipe for pike cutlets"

план сформируй с учетом команд для AI агента в следующем репозитории

