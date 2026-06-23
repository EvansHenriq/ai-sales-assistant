from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from httpx import AsyncClient

from app.agent.openai_client import get_llm_client
from tests.fakes import FakeLLMClient, FakeModeration

SeedApiKey = Callable[..., Awaitable[str]]


async def test_message_endpoint_moderates_flagged_output(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
    fake_moderation: FakeModeration,
) -> None:
    fake_llm.reply = "disallowed content"
    fake_moderation.flagged = True
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}

    conversation_id = (
        await client_with_db.post("/v1/conversations", json={}, headers=headers)
    ).json()["id"]
    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "hello"},
        headers=headers,
    )

    assert response.status_code == 200
    assert "can't help" in response.json()["reply"].lower()
    assert fake_moderation.calls  # moderation was invoked
