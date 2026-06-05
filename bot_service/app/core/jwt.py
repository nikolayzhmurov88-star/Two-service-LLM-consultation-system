from jose import jwt, ExpiredSignatureError, JWTError
from .config import settings

def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        # дополнительная проверка exp не нужна – jwt.decode уже проверяет
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except JWTError:
        raise ValueError("Invalid token")