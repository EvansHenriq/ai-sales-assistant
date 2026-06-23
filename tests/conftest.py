"""Shared pytest fixtures.

Database-backed tests use an in-memory SQLite database (shared via StaticPool so
every session sees the same data). The Phase 1 schema is dialect-agnostic;
Postgres/pgvector-specific behaviour is covered by tests marked ``integration``.
"""

from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.deps import get_moderation_client, get_retriever
from app.core.security import generate_api_key, hash_api_key
from app.db.models import ApiKey, Base
from app.db.session import get_session
from app.main import create_app
from tests.fakes import FakeLLMClient, FakeModeration, FakeRetriever


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    application = create_app()
    async with LifespanManager(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def db_sessionmaker(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_sessionmaker() as session:
        yield session


@pytest.fixture
async def client_with_db(
    app: FastAPI,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    fake_retriever: FakeRetriever,
    fake_moderation: FakeModeration,
) -> AsyncIterator[AsyncClient]:
    """Test client whose DB session is backed by the in-memory database.

    Retriever and moderation are overridden with fakes so endpoint tests never
    call OpenAI; the LLM client is overridden per-test where needed.
    """

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with db_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_retriever] = lambda: fake_retriever
    app.dependency_overrides[get_moderation_client] = lambda: fake_moderation
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def fake_retriever() -> FakeRetriever:
    return FakeRetriever()


@pytest.fixture
def fake_moderation() -> FakeModeration:
    return FakeModeration()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def seed_api_key(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> Callable[..., Awaitable[str]]:
    """Return an async helper that inserts an API key and returns the raw key."""

    async def _seed(name: str = "test") -> str:
        raw_key = generate_api_key()
        async with db_sessionmaker() as session:
            session.add(ApiKey(name=name, key_hash=hash_api_key(raw_key)))
            await session.commit()
        return raw_key

    return _seed
