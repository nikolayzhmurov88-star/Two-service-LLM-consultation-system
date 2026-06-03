from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Класс конфигурации приложения

class Settings(BaseSettings):
    app_name: str = "auth-service"
    env: str = "local"
    
    jwt_secret: str
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60
    
    sqlite_path: str = "./auth.db"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()