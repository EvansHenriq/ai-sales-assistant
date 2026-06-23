"""OpenAI-backed implementation of the ``LLMClient`` protocol.

Wraps the AsyncOpenAI Responses API and logs token usage, latency and estimated
cost on every call (lightweight observability).
"""

import time
from functools import lru_cache
from typing import cast

from openai import AsyncOpenAI
from openai.types.responses import Response, ResponseInputParam

from app.agent.pricing import estimate_cost_usd
from app.agent.types import ChatMessage, LLMClient, LLMResult, LLMUsage
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_usage(response: Response) -> LLMUsage:
    usage = response.usage
    if usage is None:
        return LLMUsage(input_tokens=0, output_tokens=0, total_tokens=0)
    return LLMUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )


class OpenAIClient:
    """Concrete LLM client using the OpenAI Responses API."""

    def __init__(
        self, client: AsyncOpenAI | None = None, *, default_model: str | None = None
    ) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout,
            max_retries=settings.openai_max_retries,
        )
        self._default_model = default_model or settings.openai_model

    async def generate(
        self,
        *,
        system: str,
        messages: list[ChatMessage],
        model: str | None = None,
    ) -> LLMResult:
        model = model or self._default_model
        request_input = cast(
            ResponseInputParam, [{"role": m.role, "content": m.content} for m in messages]
        )
        start = time.perf_counter()
        response = await self._client.responses.create(
            model=model,
            instructions=system,
            input=request_input,
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        usage = _extract_usage(response)
        logger.info(
            "llm.generate",
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimate_cost_usd(model, usage.input_tokens, usage.output_tokens),
        )
        return LLMResult(text=response.output_text, usage=usage, model=model)


@lru_cache
def get_llm_client() -> LLMClient:
    """Return a process-wide LLM client (reuses the underlying HTTP client)."""
    return OpenAIClient()
