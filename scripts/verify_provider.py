"""Smoke-test the configured LLM provider (OpenAI or a compatible one like
Ollama): free-text generation, structured BANT parsing, and embeddings.

Reads provider config from the environment (.env). Run:
  uv run python scripts/verify_provider.py
"""

import asyncio

from app.agent.openai_client import OpenAIClient
from app.agent.types import ChatMessage
from app.core.config import get_settings
from app.qualification.service import QualificationService
from app.rag.embeddings import OpenAIEmbedder


async def main() -> None:
    settings = get_settings()
    print(f"base_url     : {settings.openai_base_url or 'OpenAI default'}")
    print(f"chat model   : {settings.openai_model}")
    print(f"embed model  : {settings.openai_embedding_model} (dim {settings.embedding_dim})\n")

    llm = OpenAIClient()

    generation = await llm.generate(
        system="You are Aria, a concise B2B SaaS sales assistant for FlowMetrics.",
        messages=[ChatMessage(role="user", content="In one sentence, what is FlowMetrics?")],
    )
    print(f"[generate] {generation.text.strip()}")
    print(f"           tokens={generation.usage.total_tokens}\n")

    service = QualificationService(llm, model=settings.openai_model_cheap)
    qualification, _usage = await service.qualify(
        [
            ChatMessage(
                role="user",
                content=(
                    "We have a $50k budget approved, I'm the VP of Product, "
                    "and we need this live next month."
                ),
            )
        ]
    )
    print(
        f"[parse/BANT] stage={qualification.stage} score={qualification.score} "
        f"budget={qualification.budget} authority={qualification.authority}\n"
    )

    vector = await OpenAIEmbedder().embed_one("hello world")
    print(f"[embed] dims={len(vector)} (expected {settings.embedding_dim})")


if __name__ == "__main__":
    asyncio.run(main())
