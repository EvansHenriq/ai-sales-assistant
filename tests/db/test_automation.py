import uuid
from collections.abc import Awaitable, Callable

from httpx import AsyncClient

SeedApiKey = Callable[..., Awaitable[str]]


async def _create_conversation(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.post("/v1/conversations", json={}, headers=headers)
    return str(response.json()["id"])


async def test_capture_lead_links_conversation(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = await _create_conversation(client_with_db, headers)

    created = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/lead",
        json={"name": "Dana", "email": "dana@acme.com", "company": "Acme"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["email"] == "dana@acme.com"

    conversation = await client_with_db.get(f"/v1/conversations/{conversation_id}", headers=headers)
    assert conversation.json()["lead_id"] == created.json()["id"]


async def test_capture_lead_upserts_by_email(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = await _create_conversation(client_with_db, headers)

    first = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/lead",
        json={"email": "sam@acme.com"},
        headers=headers,
    )
    second = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/lead",
        json={"email": "sam@acme.com", "name": "Sam", "company": "Acme"},
        headers=headers,
    )
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["name"] == "Sam"


async def test_capture_lead_requires_a_field(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = await _create_conversation(client_with_db, headers)
    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/lead", json={}, headers=headers
    )
    assert response.status_code == 422


async def test_schedule_demo_requires_lead(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = await _create_conversation(client_with_db, headers)
    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/schedule-demo",
        json={"requested_time": "next Tuesday 2pm"},
        headers=headers,
    )
    assert response.status_code == 409


async def test_schedule_demo_after_lead_capture(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = await _create_conversation(client_with_db, headers)
    await client_with_db.post(
        f"/v1/conversations/{conversation_id}/lead",
        json={"email": "lee@acme.com"},
        headers=headers,
    )

    booking = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/schedule-demo",
        json={"requested_time": "next Tuesday 2pm", "notes": "Wants a security overview"},
        headers=headers,
    )
    assert booking.status_code == 201
    body = booking.json()
    assert body["requested_time"] == "next Tuesday 2pm"
    assert body["status"] == "requested"
    assert body["conversation_id"] == conversation_id


async def test_lead_on_missing_conversation_returns_404(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    response = await client_with_db.post(
        f"/v1/conversations/{uuid.uuid4()}/lead",
        json={"email": "x@y.com"},
        headers=headers,
    )
    assert response.status_code == 404
