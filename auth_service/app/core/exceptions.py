from fastapi import HTTPException, status

# Базовый класс
class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

# Ошибка пользователь уже существует
class UserAlreadyExistsError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует")

# Ошибка неверная почта или пароль
class InvalidCredentialsError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверная почта или пароль")

# Ошибка неверный токен
class InvalidTokenError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен")

# Ошибка срок действия токена истек
class TokenExpiredError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Срок действия токена истёк")

# Ошибка пользователь не найден
class UserNotFoundError(BaseHTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")