from fastapi import HTTPException, status
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


# Пайдентик исключения

def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        msg = err['msg']
        
        if msg == "value is not a valid email address: An email address must have an @-sign.":
            msg = "Некорректный email: адрес должен содержать символ @"

        elif msg == "value is not a valid email address: The part after the @-sign is not valid. It should have a period.":
            msg = "Некорректный email: после @ должен идти домен с точкой (например, domain.com)"

        elif msg == "String should have at least 1 character":
            msg = "Пароль не может быть пустым"

        else:
            msg = "Некорректный ввод данных"
        
        errors.append(msg)
    
    detail = "; ".join(errors)
    return JSONResponse(status_code=422, content={"detail": detail})