"""CLI entry point: run the eval suites and emit a report.

Guardrail suites always run (deterministic). The qualification suite runs when an
OpenAI key is configured; the RAG suite additionally needs a seeded PostgreSQL
database. Run with: ``python -m evals.run``.
"""

import asyncio

from app.agent.openai_client import OpenAIClient
from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.rag.embeddings import OpenAIEmbedder
from app.rag.retriever import PgVectorRetriever
from evals.report import Results, format_report, write_report
from evals.suites import (
    run_injection_suite,
    run_pii_suite,
    run_qualification_suite,
    run_rag_suite,
)


async def run_all() -> Results:
    settings = get_settings()
    results: Results = {
        "guardrails_injection": run_injection_suite(),
        "guardrails_pii": run_pii_suite(),
    }

    if not settings.openai_api_key.get_secret_value():
        print("Skipping LLM-dependent suites (OPENAI_API_KEY not set).")
        return results

    llm = OpenAIClient()
    results["qualification"] = await run_qualification_suite(llm, model=settings.openai_model_cheap)

    if "postgresql" in settings.database_url:
        async with get_sessionmaker()() as session:
            retriever = PgVectorRetriever(session, OpenAIEmbedder())
            results["rag"] = await run_rag_suite(retriever)
    else:
        print("Skipping RAG suite (PostgreSQL DATABASE_URL not configured).")

    return results


async def main() -> None:
    results = await run_all()
    print(format_report(results))
    path = write_report(results)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    asyncio.run(main())
