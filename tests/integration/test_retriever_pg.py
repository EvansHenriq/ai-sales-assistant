from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.rag.ingest import ingest_path
from app.rag.retriever import PgVectorRetriever
from tests.fakes import FakeEmbedder

pytestmark = pytest.mark.integration


async def test_pgvector_retriever_returns_ingested_chunks(
    pg_sessionmaker: async_sessionmaker[AsyncSession], tmp_path: Path
) -> None:
    (tmp_path / "pricing.md").write_text(
        "# Pricing\n\nGrowth is $99 per month.\n\nScale is $499 per month.",
        encoding="utf-8",
    )
    embedder = FakeEmbedder(dim=1536)

    async with pg_sessionmaker() as session:
        chunk_count = await ingest_path(session, embedder, tmp_path)
        await session.commit()

    assert chunk_count >= 1

    async with pg_sessionmaker() as session:
        retriever = PgVectorRetriever(session, embedder)
        results = await retriever.search("pricing", k=2)

    assert 1 <= len(results) <= 2
    assert all("month" in result.content for result in results)
    assert all(result.source == "Pricing" for result in results)
