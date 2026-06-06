from aiogram import Router, types
from aiogram.filters import Command
from app.infra.redis import get_redis
from app.core.jwt import decode_and_validate
from app.tasks.llm_tasks import llm_request

router = Router()

@router.message(Command("token"))
async def cmd_token(message: types.Message):
    # Формат: /token <JWT>
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("🔐 Использование: /token <ваш_jwt_токен>")
        return
    
    jwt_token = parts[1].strip()
    
    try:
        # Валидируем токен
        payload = decode_and_validate(jwt_token)
        user_id = payload.get("sub")
        
        if not user_id:
            await message.answer("❌ Неверный токен: отсутствует идентификатор пользователя (sub)")
            return
        
        # Сохраняем токен в Redis
        redis = await get_redis()
        key = f"token:{message.from_user.id}"
        await redis.set(key, jwt_token, ex=3600 * 24)  # храним 24 часа
        
        await message.answer(
            f"✅ Токен сохранён для пользователя ID {user_id}.\n"
            f"Теперь вы можете задавать вопросы боту."
        )
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка валидации токена: {e}")

@router.message()
async def handle_text(message: types.Message):
    # Проверяем, есть ли у пользователя сохранённый токен
    redis = await get_redis()
    key = f"token:{message.from_user.id}"
    jwt_token = await redis.get(key)
    
    if not jwt_token:
        await message.answer(
            "🔐 Вы не авторизованы.\n\n"
            "Пожалуйста, получите JWT-токен в сервисе аутентификации "
            "и отправьте его командой:\n"
            "/token <ваш_jwt_токен>"
        )
        return
    
    try:
        # Валидируем токен
        payload = decode_and_validate(jwt_token)
        
        # Отправляем задачу в Celery
        llm_request.delay(message.chat.id, message.text)
        
        await message.answer(
            "⏳ Запрос отправлен на обработку. "
            "Пожалуйста, подождите, я готовлю ответ..."
        )
        
    except ValueError as e:
        await message.answer(
            f"❌ Ошибка авторизации: {e}\n\n"
            f"Пожалуйста, получите новый токен и отправьте его командой:\n"
            f"/token <ваш_jwt_токен>"
        )