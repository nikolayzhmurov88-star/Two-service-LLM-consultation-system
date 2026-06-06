from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.bot.dispatcher import start_bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем бота в фоне
    bot_task = asyncio.create_task(start_bot())
    yield
    # При остановке отменяем задачу бота
    bot_task.cancel()
    await bot_task

app = FastAPI(title="Bot Service", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}