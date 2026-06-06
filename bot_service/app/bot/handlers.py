from aiogram import Router, types
from aiogram.filters import Command
from app.infra.redis import get_redis
from app.core.jwt import decode_and_validate
from app.tasks.llm_tasks import llm_request

def _get_bot():
    from app.bot.dispatcher import bot
    return bot

router = Router()

@router.message(Command("token"))
async def cmd_token(message: types.Message):
    bot = _get_bot()
    # Формат: /token <JWT>
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await bot.send_message(message.chat.id, "🔐 Использование: /token <ваш_jwt_токен>")
        return
    
    jwt_token = parts[1].strip()
    
    try:
        payload = decode_and_validate(jwt_token)
        user_id = payload.get("sub")
        
        if not user_id:
            await bot.send_message(message.chat.id, "❌ Неверный токен: отсутствует идентификатор пользователя (sub)")
            return
        
        redis = await get_redis()
        key = f"token:{message.from_user.id}"
        await redis.set(key, jwt_token, ex=3600 * 24)
        
        await bot.send_message(
            message.chat.id,
            f"✅ Токен сохранён для пользователя ID {user_id}.\n"
            f"Теперь вы можете задавать вопросы боту."
        )
        
    except ValueError as e:
        await bot.send_message(message.chat.id, f"❌ Ошибка валидации токена: {e}")

@router.message()
async def handle_text(message: types.Message):
    bot = _get_bot()
    redis = await get_redis()
    key = f"token:{message.from_user.id}"
    jwt_token = await redis.get(key)
    
    if not jwt_token:
        await bot.send_message(
            message.chat.id,
            "🔐 Вы не авторизованы.\n\n"
            "Пожалуйста, получите JWT-токен в сервисе аутентификации "
            "и отправьте его командой:\n"
            "/token <ваш_jwt_токен>"
        )
        return
    
    try:
        decode_and_validate(jwt_token)
        llm_request.delay(message.chat.id, message.text)
        
        await bot.send_message(
            message.chat.id,
            "⏳ Запрос отправлен на обработку. "
            "Пожалуйста, подождите, я готовлю ответ..."
        )
        
    except ValueError as e:
        await bot.send_message(
            message.chat.id,
            f"❌ Ошибка авторизации: {e}\n\n"
            f"Пожалуйста, получите новый токен и отправьте его командой:\n"
            f"/token <ваш_jwt_токен>"
        )
