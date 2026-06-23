from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from app.core.config import get_settings

SeedApiKey = Callable[..., Awaitable[str]]


async def test_rate_limit_blocks_after_quota(
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Tighten the limit to 1/minute for this test (restored automatically).
    monkeypatch.setattr(get_settings(), "rate_limit", "1/minute")
    headers = {"X-API-Key": await seed_api_key()}

    first = await client_with_db.post("/v1/conversations", json={}, headers=headers)
    second = await client_with_db.post("/v1/conversations", json={}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 429
