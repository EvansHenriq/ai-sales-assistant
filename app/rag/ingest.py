"""Ingest markdown knowledge-base files into the database with embeddings."""

# Ingestion is a batch/offline operation (run from a script, not a request),
# so synchronous file reads are intentional.
# ruff: noqa: ASYNC240

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, KnowledgeChunk
from app.rag.chunking import chunk_text
from app.rag.types import Embedder


def _title_from(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


async def ingest_path(session: AsyncSession, embedder: Embedder, path: Path) -> int:
    """Ingest every ``*.md`` file under ``path``. Returns the chunk count."""
    total_chunks = 0
    for file in sorted(path.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        title = _title_from(text, file.stem)

        document = Document(title=title, source=file.name)
        session.add(document)
        await session.flush()

        chunks = chunk_text(text)
        if not chunks:
            continue
        vectors = await embedder.embed(chunks)
        for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
            session.add(
                KnowledgeChunk(
                    document_id=document.id,
                    source=title,
                    chunk_index=index,
                    content=content,
                    embedding=vector,
                )
            )
        total_chunks += len(chunks)

    await session.flush()
    return total_chunks
