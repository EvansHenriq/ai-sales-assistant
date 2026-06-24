"""LLM client over the Chat Completions API.

Chat Completions is supported by OpenAI and by OpenAI-compatible providers such
as a local Ollama, so the same client works against either (selected via
``OPENAI_BASE_URL``). Token usage, latency and estimated cost are logged on every
call (lightweight observability).
"""

import time
from functools import lru_cache
from typing import cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from pydantic import BaseModel

from app.agent.pricing import estimate_cost_usd
from app.agent.types import AgentLLM, ChatMessage, LLMResult, LLMUsage, StructuredResult
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_usage(response: ChatCompletion) -> LLMUsage:
    usage = response.usage
    if usage is None:
        return LLMUsage(input_tokens=0, output_tokens=0, total_tokens=0)
    return LLMUsage(
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )


def _build_messages(system: str, messages: list[ChatMessage]) -> list[ChatCompletionMessageParam]:
    payload: list[dict[str, str]] = [{"role": "system", "content": system}]
    payload.extend({"role": m.role, "content": m.content} for m in messages)
    return cast(list[ChatCompletionMessageParam], payload)


class OpenAIClient:
    """Chat Completions client (OpenAI or any compatible provider)."""

    def __init__(
        self, client: AsyncOpenAI | None = None, *, default_model: str | None = None
    ) -> None:
        settings = get_settings()
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout,
            max_retries=settings.openai_max_retries,
        )
        self._default_model = default_model or settings.openai_model

    async def generate(
        self, *, system: str, messages: list[ChatMessage], model: str | None = None
    ) -> LLMResult:
        model = model or self._default_model
        start = time.perf_counter()
        response = await self._client.chat.completions.create(
            model=model, messages=_build_messages(system, messages)
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
        return LLMResult(text=response.choices[0].message.content or "", usage=usage, model=model)

    async def parse[T: BaseModel](
        self,
        *,
        system: str,
        messages: list[ChatMessage],
        schema: type[T],
        model: str | None = None,
    ) -> StructuredResult[T]:
        model = model or self._default_model
        start = time.perf_counter()
        response = await self._client.chat.completions.parse(
            model=model,
            messages=_build_messages(system, messages),
            response_format=schema,
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        usage = _extract_usage(response)
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("Structured parse returned no parsed output")
        logger.info(
            "llm.parse",
            model=model,
            schema=schema.__name__,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_ms,
            estimated_cost_usd=estimate_cost_usd(model, usage.input_tokens, usage.output_tokens),
        )
        return StructuredResult(parsed=parsed, usage=usage, model=model)


@lru_cache
def get_llm_client() -> AgentLLM:
    """Return a process-wide LLM client (reuses the underlying HTTP client)."""
    return OpenAIClient()
