from pydantic import BaseModel
from datetime import datetime

# Модель передачи данных пользователя без Хэша пароля
class UserPublic(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime