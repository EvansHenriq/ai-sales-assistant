"""Seed the knowledge base: ingest data/knowledge_base/*.md with embeddings.

Run: uv run python scripts/seed_knowledge.py
Requires a PostgreSQL DATABASE_URL and an OPENAI_API_KEY.
"""

import asyncio
from pathlib import Path

from app.db.session import get_sessionmaker
from app.rag.embeddings import OpenAIEmbedder
from app.rag.ingest import ingest_path

KNOWLEDGE_BASE = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"


async def main() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        count = await ingest_path(session, OpenAIEmbedder(), KNOWLEDGE_BASE)
        await session.commit()
    print(f"Ingested {count} chunks from {KNOWLEDGE_BASE}")


if __name__ == "__main__":
    asyncio.run(main())
