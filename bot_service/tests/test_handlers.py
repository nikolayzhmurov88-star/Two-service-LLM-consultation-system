import pytest
import uuid
from unittest.mock import patch
from aiogram.types import Message, Chat, User
from jose import jwt
from app.core.config import settings
from app.bot.handlers import cmd_token, handle_text

def make_message(text: str, user_id: int = 456, chat_id: int = 123):
    return Message(
        message_id=1,
        date=0,
        chat=Chat(id=chat_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        text=text
    )


@pytest.mark.asyncio
async def test_token_saves_to_redis_and_sends_message(fake_redis, mock_bot):
    real_token = jwt.encode({"sub": "999"}, settings.jwt_secret, algorithm=settings.jwt_alg)
    message = make_message(f"/token {real_token}")
    
    await cmd_token(message)
    
    mock_bot.send_message.assert_called_once()
    assert "✅" in mock_bot.send_message.call_args[0][1]
    
    saved = await fake_redis.get("token:456")
    assert saved == real_token


@pytest.mark.asyncio
async def test_token_invalid_jwt_does_not_save_and_sends_error(fake_redis, mock_bot):
    message = make_message("/token garbage_token")
    
    await cmd_token(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Ошибка" in mock_bot.send_message.call_args[0][1]
    
    saved = await fake_redis.get("token:456")
    assert saved is None


@pytest.mark.asyncio
async def test_text_without_token_no_celery_and_sends_warning(fake_redis, mock_bot):
    message = make_message("hello")
    
    with patch("app.tasks.llm_tasks.llm_request.delay") as mock_delay:
        await handle_text(message)
        
        mock_bot.send_message.assert_called_once()
        assert "не авторизованы" in mock_bot.send_message.call_args[0][1]
        mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_text_with_valid_token_calls_celery_and_sends_confirmation(fake_redis, mock_bot):
    real_token = jwt.encode({"sub": "999"}, settings.jwt_secret, algorithm=settings.jwt_alg)
    await fake_redis.set("token:456", real_token, ex=3600)
    
    message = make_message("Привет, как дела?")
    
    with patch("app.tasks.llm_tasks.llm_request.delay") as mock_delay:
        await handle_text(message)
        
        mock_bot.send_message.assert_called_once()
        assert "Запрос отправлен" in mock_bot.send_message.call_args[0][1]
        
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert args[0] == 123
        assert args[1] == "Привет, как дела?"
        
        # Проверяем, что task_id — валидный UUID
        task_id = args[2]
        assert isinstance(task_id, str)
        # Проверяем формат UUID
        try:
            uuid.UUID(task_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid, f"task_id '{task_id}' не является валидным UUID"



@pytest.mark.asyncio
async def test_text_with_expired_token_no_celery_and_sends_error(fake_redis, mock_bot):
    from datetime import datetime, timedelta, timezone
    expire = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_token = jwt.encode(
        {"sub": "999", "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_alg
    )
    await fake_redis.set("token:456", expired_token, ex=3600)
    
    message = make_message("hello")
    
    with patch("app.tasks.llm_tasks.llm_request.delay") as mock_delay:
        await handle_text(message)
        
        mock_bot.send_message.assert_called_once()
        assert "Ошибка" in mock_bot.send_message.call_args[0][1]
        mock_delay.assert_not_called()
