import pytest
import respx
from httpx import Response
from app.services.openrouter_client import ask_llm

@respx.mock
@pytest.mark.asyncio
async def test_openrouter_success():
    mock_route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"message": {"content": "Hello from LLM"}}]})
    )
    answer = await ask_llm("test prompt")
    assert answer == "Hello from LLM"
    assert mock_route.called