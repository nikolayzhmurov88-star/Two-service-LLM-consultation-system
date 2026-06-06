import pytest
from unittest.mock import AsyncMock, patch
from fakeredis import aioredis as fakeredis

@pytest.fixture
async def fake_redis():
    """Подменяет реальный Redis на фейковый."""
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    with patch("app.bot.handlers.get_redis", return_value=fake_redis_client):
        with patch("app.infra.redis.get_redis", return_value=fake_redis_client):
            yield fake_redis_client

@pytest.fixture(autouse=True)
def mock_celery():
    """Отключает Celery – задачи не отправляются в RabbitMQ."""
    with patch("app.tasks.llm_tasks.llm_request.delay") as mock:
        yield mock

@pytest.fixture
def mock_bot():
    """Возвращает мок-бота и автоматически подменяет _get_bot во всех тестах."""
    mock = AsyncMock()
    with patch("app.bot.handlers._get_bot", return_value=mock):
        yield mock
