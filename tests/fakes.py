"""Reusable test doubles."""

from typing import Any

from pydantic import BaseModel

from app.agent.types import ChatMessage, LLMResult, LLMUsage, StructuredResult
from app.guardrails.moderation import ModerationResult
from app.rag.types import RetrievedChunk


class FakeLLMClient:
    """In-memory LLM client for tests; records calls and returns canned output.

    Set ``parsed`` to control what ``parse`` returns (structured outputs).
    """

    def __init__(self, reply: str = "Hello from Aria.", parsed: Any = None) -> None:
        self.reply = reply
        self.parsed = parsed
        self.calls: list[dict[str, object]] = []
        self.parse_calls: list[dict[str, object]] = []

    async def generate(
        self, *, system: str, messages: list[ChatMessage], model: str | None = None
    ) -> LLMResult:
        self.calls.append({"system": system, "messages": list(messages), "model": model})
        return LLMResult(
            text=self.reply,
            usage=LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            model=model or "fake-model",
        )

    async def parse[T: BaseModel](
        self,
        *,
        system: str,
        messages: list[ChatMessage],
        schema: type[T],
        model: str | None = None,
    ) -> StructuredResult[T]:
        self.parse_calls.append(
            {"system": system, "messages": list(messages), "schema": schema, "model": model}
        )
        return StructuredResult(
            parsed=self.parsed,
            usage=LLMUsage(input_tokens=8, output_tokens=4, total_tokens=12),
            model=model or "fake-model",
        )


class FakeEmbedder:
    """Deterministic embedder for tests (no network)."""

    def __init__(self, dim: int = 8) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # +1 avoids the all-zero vector (cosine distance is undefined for it).
        return [[float(len(text) % 7 + 1)] * self.dim for text in texts]

    async def embed_one(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]


class FakeRetriever:
    """Returns preconfigured chunks; records the queries it received."""

    def __init__(self, chunks: list[RetrievedChunk] | None = None) -> None:
        self.chunks = chunks or []
        self.queries: list[str] = []

    async def search(self, query: str, *, k: int = 4) -> list[RetrievedChunk]:
        self.queries.append(query)
        return list(self.chunks[:k])


class FakeModeration:
    """Moderation client that returns a preconfigured verdict."""

    def __init__(self, flagged: bool = False, categories: list[str] | None = None) -> None:
        self.flagged = flagged
        self.categories = categories or []
        self.calls: list[str] = []

    async def moderate(self, text: str) -> ModerationResult:
        self.calls.append(text)
        return ModerationResult(flagged=self.flagged, categories=self.categories)
