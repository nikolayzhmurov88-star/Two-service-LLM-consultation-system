import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.core.exceptions import TokenExpiredError 

def test_password_hashing():
    pwd = "secret"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_create_and_decode():
    data = {"sub": "1", "role": "user"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["role"] == "user"
    assert "exp" in decoded
    assert "iat" in decoded

def test_jwt_expired():
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    payload = {"sub": "1", "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    with pytest.raises(TokenExpiredError): 
        decode_token(token)