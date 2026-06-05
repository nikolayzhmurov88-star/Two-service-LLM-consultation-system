from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    app_name: str = "bot-service"
    env: str = "local"
    
    telegram_bot_token: str
    jwt_secret: str
    jwt_alg: str = "HS256"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "stepfun/step-3.5-flash:free"
    openrouter_site_url: str = "https://example.com"
    openrouter_app_name: str = "bot-service"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()