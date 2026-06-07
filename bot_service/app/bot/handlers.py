from aiogram import Router, types
from aiogram.filters import Command
from app.infra.redis import get_redis
from app.core.jwt import decode_and_validate
from app.tasks.llm_tasks import llm_request
import asyncio
import uuid

def _get_bot():
    from app.bot.dispatcher import bot
    return bot

router = Router()

@router.message(Command("token"))
async def cmd_token(message: types.Message):
    bot = _get_bot()
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await bot.send_message(message.chat.id, "🔐 Использование: /token <ваш_jwt_токен>")
        return
    
    jwt_token = parts[1].strip()
    
    try:
        payload = decode_and_validate(jwt_token)
        user_id = payload.get("sub")
        
        redis = await get_redis()
        await redis.set(f"token:{message.from_user.id}", jwt_token, ex=3600 * 24)
        
        await bot.send_message(
            message.chat.id,
            f"✅ Токен сохранён для пользователя ID {user_id}.\nТеперь вы можете задавать вопросы боту."
        )
    except ValueError as e:
        await bot.send_message(message.chat.id, f"❌ Ошибка валидации токена: {e}")

async def wait_for_result(bot, chat_id: int, task_id: str, timeout: int = 120):
    redis = await get_redis()
    key = f"llm_result:{task_id}"
    
    for _ in range(timeout):
        result = await redis.get(key)
        if result:
            await bot.send_message(chat_id, result)
            await redis.delete(key)
            return
        await asyncio.sleep(1)
    
    await bot.send_message(chat_id, "❌ Ответа от LLM до сих пор нет. Попробуйте позже.")

@router.message()
async def handle_text(message: types.Message):
    bot = _get_bot()
    redis = await get_redis()
    jwt_token = await redis.get(f"token:{message.from_user.id}")
    
    if not jwt_token:
        await bot.send_message(
            message.chat.id,
            "🔐 Вы не авторизованы.\n\nПожалуйста, получите JWT-токен в сервисе аутентификации "
            "и отправьте его командой:\n/token <ваш_jwt_токен>"
        )
        return
    
    try:
        decode_and_validate(jwt_token)
        task_id = str(uuid.uuid4())
        llm_request.delay(message.chat.id, message.text, task_id)
        await bot.send_message(message.chat.id, "⏳ Запрос отправлен. Я уведомлю вас, когда ответ будет готов.")
        asyncio.create_task(wait_for_result(bot, message.chat.id, task_id))
    except ValueError as e:
        await bot.send_message(
            message.chat.id,
            f"❌ Ошибка авторизации: {e}\n\nПожалуйста, получите новый токен и отправьте его командой:\n/token <ваш_jwt_токен>"
        )