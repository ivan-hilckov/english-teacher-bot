Мы создали нового бота english-teacher-bot на основе hello-ai-bot (https://github.com/ivan-hilckov/hello-ai-bot)

сейчас если проанализировать файл app/handlers.py то можно понять что промт котрый улетает в openai_service c очень бедным содержимым

```py
        print(f"Generating response for {text}")
        ai_response, tokens = await openai_service.generate_response(
            user_message=text, role_prompt=user_role.role_prompt, model=settings.default_ai_model
        )
```

также отсутствует более точная настройка движка `default_ai_model: str = Field(default="gpt-3.5-turbo", description="Default AI model")`: температура


https://openai.github.io/openai-agents-python/agents/ - тут описано как работают агенты
https://openai.github.io/openai-agents-python/running_agents/ - тут как их запускать 
https://openai.github.io/openai-agents-python/tools/ - тут дополнительные возоможности 
https://openai.github.io/openai-agents-python/context/ - тут как работать с контекстом

Можешь улучишить взаимодействие бота с пользователем (добавить нужные промты, реализовать режим агенат, добавить настройки тюнинка запроса) 