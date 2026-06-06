import pytest
from jose import jwt
from app.core.config import settings
from app.core.jwt import decode_and_validate
from datetime import datetime, timedelta, timezone

# Проверка правильного токена
def test_decode_valid_token():
    token = jwt.encode({"sub": "123", "role": "user"}, settings.jwt_secret, algorithm=settings.jwt_alg)
    payload = decode_and_validate(token)
    assert payload["sub"] == "123"
    assert payload["role"] == "user"

# Проверка не правильного токена 
def test_decode_invalid_token():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_and_validate("garbage")

# Просроченный токен
def test_decode_expired_token():
    # Создаём токен, который истекает через -1 секунду (уже просрочен)
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    token = jwt.encode(
        {"sub": "123", "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_alg
    )
    
    with pytest.raises(ValueError, match="Token expired"):
        decode_and_validate(token)

# С неправильным секретом
def test_wrong_signature():
    # Создаём токен с другим секретом
    token = jwt.encode(
        {"sub": "123"},
        "wrong_secret", 
        algorithm=settings.jwt_alg
    )
    
    with pytest.raises(ValueError, match="Invalid token"):
        decode_and_validate(token)