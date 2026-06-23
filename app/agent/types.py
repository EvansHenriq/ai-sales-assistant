"""Provider-agnostic types and the LLM client protocol.

The orchestrator depends on the ``LLMClient`` protocol, not on the OpenAI SDK
directly, so it can be exercised with a fake in tests.
"""

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

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
