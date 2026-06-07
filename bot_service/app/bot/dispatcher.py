from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.core.config import settings
from .handlers import router

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode=None)
)
dp = Dispatcher()

dp.include_router(router)

async def start_bot():
    await dp.start_polling(bot)
