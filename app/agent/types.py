"""Provider-agnostic types and the LLM client protocol.

The orchestrator depends on the ``LLMClient`` protocol, not on the OpenAI SDK
directly, so it can be exercised with a fake in tests.
"""

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class LLMResult:
    text: str
    usage: LLMUsage
    model: str


@dataclass(frozen=True)
class StructuredResult[T]:
    parsed: T
    usage: LLMUsage
    model: str


@runtime_checkable
class LLMClient(Protocol):
    """Minimal surface the agent needs from a language model provider."""

    async def generate(
        self,
        *,
        system: str,
        messages: list[ChatMessage],
        model: str | None = None,
    ) -> LLMResult: ...


class StructuredLLMClient(Protocol):
    """Provider that can return a parsed Pydantic object (structured output)."""

    async def parse[T: BaseModel](
        self,
        *,
        system: str,
        messages: list[ChatMessage],
        schema: type[T],
        model: str | None = None,
    ) -> StructuredResult[T]: ...


class AgentLLM(LLMClient, StructuredLLMClient, Protocol):
    """Both free-text generation and structured parsing."""
