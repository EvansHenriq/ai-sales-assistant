"""Output moderation via the OpenAI moderation endpoint (mockable)."""

from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import get_settings


@dataclass(frozen=True)
class ModerationResult:
    flagged: bool
    categories: list[str]


class ModerationClient(Protocol):
    async def moderate(self, text: str) -> ModerationResult: ...


class OpenAIModerationClient:
    def __init__(self, client: AsyncOpenAI | None = None, *, model: str | None = None) -> None:
        self._client = client
        self._model = model or get_settings().openai_moderation_model

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            settings = get_settings()
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                timeout=settings.openai_timeout,
                max_retries=settings.openai_max_retries,
            )
        return self._client

    async def moderate(self, text: str) -> ModerationResult:
        response = await self._get_client().moderations.create(model=self._model, input=text)
        result = response.results[0]
        categories = [name for name, value in result.categories.model_dump().items() if value]
        return ModerationResult(flagged=result.flagged, categories=categories)
