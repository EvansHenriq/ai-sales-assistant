"""pgvector similarity retriever (PostgreSQL only).

Vector search uses pgvector's cosine distance operator, so this retriever
requires a PostgreSQL database with the ``vector`` extension. Unit tests use a
fake retriever; this one is exercised by integration tests against Postgres.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeChunk
from app.rag.types import Embedder, RetrievedChunk


class PgVectorRetriever:
    def __init__(self, session: AsyncSession, embedder: Embedder) -> None:
        self._session = session
        self._embedder = embedder

    async def search(self, query: str, *, k: int = 4) -> list[RetrievedChunk]:
        query_vector = await self._embedder.embed_one(query)
        # pgvector adds `.cosine_distance` to the column at runtime; typed as Any.
        embedding_attr: Any = KnowledgeChunk.embedding
        distance = embedding_attr.cosine_distance(query_vector)

        statement = select(KnowledgeChunk, distance.label("distance")).order_by(distance).limit(k)
        result = await self._session.execute(statement)

        chunks: list[RetrievedChunk] = []
        for chunk, dist in result.all():
            chunks.append(
                RetrievedChunk(content=chunk.content, source=chunk.source, score=1.0 - float(dist))
            )
        return chunks
