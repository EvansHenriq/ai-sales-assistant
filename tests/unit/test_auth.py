"""The missing-API-key path must return 401 without touching the database."""

from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.db.session import get_session


async def test_missing_api_key_returns_401(app: FastAPI) -> None:
    async def _unused_session() -> AsyncIterator[None]:
        # Auth fails before any query, so the session is never used.
        yield None

    app.dependency_overrides[get_session] = _unused_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/conversations", json={})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "ApiKey"
