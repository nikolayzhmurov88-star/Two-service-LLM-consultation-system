from pydantic import BaseModel, EmailStr

# Модель запроса на регистрацию
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

# Модель возврата токена
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"