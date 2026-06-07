FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
CMD ["python", "-m", "app.bot.dispatcher"]