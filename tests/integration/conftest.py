"""Fixtures for tests that require a real PostgreSQL + pgvector database.

Enabled when ``DATABASE_URL`` points at PostgreSQL (e.g. in CI); skipped
otherwise so the default local run stays database-free.
"""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base

_DATABASE_URL = os.environ.get("DATABASE_URL", "")


@pytest.fixture
async def pg_sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    if "postgresql" not in _DATABASE_URL:
        pytest.skip("PostgreSQL DATABASE_URL not configured")

    engine = create_async_engine(_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
