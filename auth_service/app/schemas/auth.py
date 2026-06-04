from pydantic import BaseModel, EmailStr, Field

# Модель запроса на регистрацию
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="Пароль не может быть пустым")

# Модель возврата токена
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"