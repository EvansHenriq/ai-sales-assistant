"""OpenAI embeddings client (lazy: no API key needed until first use)."""

from openai import AsyncOpenAI

from app.core.config import get_settings


class OpenAIEmbedder:
    def __init__(self, client: AsyncOpenAI | None = None, *, model: str | None = None) -> None:
        self._client = client
        self._model = model or get_settings().openai_embedding_model

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            settings = get_settings()
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                timeout=settings.openai_timeout,
                max_retries=settings.openai_max_retries,
            )
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._get_client().embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    async def embed_one(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]
