import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from jose import ExpiredSignatureError
from datetime import timedelta

def test_password_hashing():
    pwd = "secret"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_create_and_decode():
    data = {"sub": "1", "role": "user"}
    token = create_access_token(data, expires_delta=timedelta(minutes=1))
    decoded = decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["role"] == "user"
    assert "exp" in decoded
    assert "iat" in decoded

def test_jwt_expired():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredSignatureError):
        decode_token(token)