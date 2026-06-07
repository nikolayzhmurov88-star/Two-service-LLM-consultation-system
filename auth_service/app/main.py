from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.router import router
from app.db.session import engine
from app.db.base import Base
from app.core.exceptions import BaseHTTPException, validation_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Закрытие ресурсов при остановке
    await engine.dispose()

app = FastAPI(title="Auth Service", lifespan=lifespan)

# Обработчик кастомных исключений (наследников BaseHTTPException)
@app.exception_handler(BaseHTTPException)
async def custom_http_exception_handler(request: Request, exc: BaseHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Обработчик ошибок валидации Pydantic (RequestValidationError)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Подключение роутера 
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}