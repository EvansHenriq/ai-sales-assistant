"""RAG types and protocols (provider-agnostic, mockable in tests)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    source: str
    score: float


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_one(self, text: str) -> list[float]: ...


class Retriever(Protocol):
    async def search(self, query: str, *, k: int = 4) -> list[RetrievedChunk]: ...
