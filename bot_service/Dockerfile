FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev
ENV PATH="/app/.venv/bin:$PATH"   
# CMD может быть любым, так как в docker-compose вы переопределяете команду для worker
# Но для бота тоже нужен PATH, если он запускает скрипт через python
CMD ["python", "-m", "app.bot.dispatcher"]