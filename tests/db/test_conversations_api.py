import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import generate_api_key, hash_api_key
from app.db.models import ApiKey


async def _seed_api_key(sessionmaker: async_sessionmaker[AsyncSession]) -> str:
    raw_key = generate_api_key()
    async with sessionmaker() as session:
        session.add(ApiKey(name="test", key_hash=hash_api_key(raw_key)))
        await session.commit()
    return raw_key


async def test_create_and_get_conversation(
    client_with_db: AsyncClient, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    headers = {"X-API-Key": await _seed_api_key(db_sessionmaker)}

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
    client_with_db: AsyncClient, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    headers = {"X-API-Key": await _seed_api_key(db_sessionmaker)}
    response = await client_with_db.get(f"/v1/conversations/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


async def test_invalid_api_key_returns_401(client_with_db: AsyncClient) -> None:
    response = await client_with_db.post(
        "/v1/conversations", json={}, headers={"X-API-Key": "not-a-real-key"}
    )
    assert response.status_code == 401
