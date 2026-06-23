from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, KnowledgeChunk
from app.rag.ingest import ingest_path
from tests.fakes import FakeEmbedder


async def test_ingest_path_creates_documents_and_chunks(
    db_session: AsyncSession, tmp_path: Path
) -> None:
    (tmp_path / "a.md").write_text(
        "# Title A\n\nHello world.\n\nSecond paragraph.", encoding="utf-8"
    )
    (tmp_path / "b.md").write_text("# Title B\n\nAnother document.", encoding="utf-8")

    count = await ingest_path(db_session, FakeEmbedder(), tmp_path)
    await db_session.commit()

    documents = (await db_session.execute(select(Document))).scalars().all()
    assert {d.title for d in documents} == {"Title A", "Title B"}

    chunks = (await db_session.execute(select(KnowledgeChunk))).scalars().all()
    assert len(chunks) == count
    assert count >= 2
    # Embeddings round-trip as a list (JSON column under SQLite).
    assert all(isinstance(chunk.embedding, list) for chunk in chunks)
    assert all(chunk.source in {"Title A", "Title B"} for chunk in chunks)
