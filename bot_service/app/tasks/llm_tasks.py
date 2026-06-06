from celery import shared_task
from app.services.openrouter_client import ask_llm
from aiogram import Bot
from app.core.config import settings

bot = Bot(token=settings.telegram_bot_token)


@shared_task
async def llm_request(chat_id: int, prompt: str):
    try:
        answer = await ask_llm(prompt)  
        await bot.send_message(chat_id, answer)
    except Exception as e:
        print(f"Error: {e}")