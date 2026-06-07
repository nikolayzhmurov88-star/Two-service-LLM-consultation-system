from app.infra.celery_app import celery_app
from app.services.openrouter_client import ask_llm
import redis
import asyncio
from app.core.config import settings

@celery_app.task
def llm_request(chat_id: int, prompt: str, task_id: str):
    try:
        answer = asyncio.run(ask_llm(prompt))
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.setex(f"llm_result:{task_id}", 120, answer)
    except Exception as e:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.setex(f"llm_result:{task_id}", 120, f"Error: {str(e)}")
    return answer