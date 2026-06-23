import uuid
from collections.abc import Awaitable, Callable

from httpx import AsyncClient

SeedApiKey = Callable[..., Awaitable[str]]


async def test_create_and_get_conversation(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}

    created = await client_with_db.post("/v1/conversations", json={}, headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "active"
    conversation_id = body["id"]

    fetched = await client_with_db.get(f"/v1/conversations/{conversation_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == conversation_id
    assert fetched.json()["messages"] == []


async def test_get_missing_conversation_returns_404(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    response = await client_with_db.get(f"/v1/conversations/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


async def test_invalid_api_key_returns_401(client_with_db: AsyncClient) -> None:
    response = await client_with_db.post(
        "/v1/conversations", json={}, headers={"X-API-Key": "not-a-real-key"}
    )
    assert response.status_code == 401
