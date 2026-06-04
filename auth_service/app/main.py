from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.router import router
from app.core.exceptions import BaseHTTPException
from app.db.session import engine
from app.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц (для SQLite – можно использовать create_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # закрытие ресурсов
    await engine.dispose()

app = FastAPI(title="Auth Service", lifespan=lifespan)

app.include_router(router)

@app.exception_handler(BaseHTTPException)
async def custom_http_exception_handler(request: Request, exc: BaseHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/health")
async def health():
    return {"status": "ok"}