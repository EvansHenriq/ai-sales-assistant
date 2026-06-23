"""Reusable test doubles."""

from app.agent.types import ChatMessage, LLMResult, LLMUsage


class FakeLLMClient:
    """In-memory LLM client for tests; records calls and returns a canned reply."""

    def __init__(self, reply: str = "Hello from Aria.") -> None:
        self.reply = reply
        self.calls: list[dict[str, object]] = []

    async def generate(
        self, *, system: str, messages: list[ChatMessage], model: str | None = None
    ) -> LLMResult:
        self.calls.append({"system": system, "messages": list(messages), "model": model})
        return LLMResult(
            text=self.reply,
            usage=LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            model=model or "fake-model",
        )
