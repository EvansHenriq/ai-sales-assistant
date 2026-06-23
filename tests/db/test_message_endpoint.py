import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from httpx import AsyncClient

from app.agent.openai_client import get_llm_client
from tests.fakes import FakeLLMClient

SeedApiKey = Callable[..., Awaitable[str]]


async def test_post_message_returns_agent_reply(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
) -> None:
    fake_llm.reply = "Sure - FlowMetrics gives you product analytics."
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}

    created = await client_with_db.post("/v1/conversations", json={}, headers=headers)
    conversation_id = created.json()["id"]

    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "what is flowmetrics?"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Sure - FlowMetrics gives you product analytics."
    assert body["usage"]["total_tokens"] == 15
    assert body["conversation_id"] == conversation_id


async def test_post_message_to_missing_conversation_returns_404(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}

    response = await client_with_db.post(
        f"/v1/conversations/{uuid.uuid4()}/messages",
        json={"content": "hi"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_post_message_rejects_empty_content(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}

    created = await client_with_db.post("/v1/conversations", json={}, headers=headers)
    conversation_id = created.json()["id"]

    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": ""},
        headers=headers,
    )
    assert response.status_code == 422
