from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.openai_client import get_llm_client
from app.db.repositories import ConversationRepository, QualificationRepository
from app.qualification.models import BANTLevel, LeadQualificationResult, LeadStage
from tests.fakes import FakeLLMClient

SeedApiKey = Callable[..., Awaitable[str]]


def _sample_result(score: int = 80, stage: LeadStage = LeadStage.hot) -> LeadQualificationResult:
    return LeadQualificationResult(
        budget=BANTLevel.high,
        authority=BANTLevel.high,
        need=BANTLevel.high,
        timeline=BANTLevel.medium,
        score=score,
        stage=stage,
        rationale="Strong fit.",
    )


async def test_repository_add_and_latest(db_session: AsyncSession) -> None:
    conversation = await ConversationRepository(db_session).create()
    repo = QualificationRepository(db_session)

    await repo.add(conversation_id=conversation.id, lead_id=None, result=_sample_result(60))
    await repo.add(conversation_id=conversation.id, lead_id=None, result=_sample_result(90))
    await db_session.commit()

    latest = await repo.latest_for_conversation(conversation.id)
    assert latest is not None
    assert latest.budget == "high"
    assert latest.stage == "hot"
    assert latest.score in {60, 90}


async def test_qualify_endpoint_then_get(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
) -> None:
    fake_llm.reply = "Thanks for the details!"
    fake_llm.parsed = _sample_result(score=75, stage=LeadStage.hot)
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}

    conversation_id = (
        await client_with_db.post("/v1/conversations", json={}, headers=headers)
    ).json()["id"]
    await client_with_db.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "We have budget and need this live in Q3."},
        headers=headers,
    )

    qualified = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/qualify", headers=headers
    )
    assert qualified.status_code == 200
    body = qualified.json()
    assert body["stage"] == "hot"
    assert body["score"] == 75
    assert body["budget"] == "high"

    fetched = await client_with_db.get(
        f"/v1/conversations/{conversation_id}/qualification", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


async def test_qualify_empty_conversation_returns_422(
    app: FastAPI,
    client_with_db: AsyncClient,
    seed_api_key: SeedApiKey,
    fake_llm: FakeLLMClient,
) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = (
        await client_with_db.post("/v1/conversations", json={}, headers=headers)
    ).json()["id"]

    response = await client_with_db.post(
        f"/v1/conversations/{conversation_id}/qualify", headers=headers
    )
    assert response.status_code == 422


async def test_get_qualification_returns_404_when_absent(
    client_with_db: AsyncClient, seed_api_key: SeedApiKey
) -> None:
    headers = {"X-API-Key": await seed_api_key()}
    conversation_id = (
        await client_with_db.post("/v1/conversations", json={}, headers=headers)
    ).json()["id"]

    response = await client_with_db.get(
        f"/v1/conversations/{conversation_id}/qualification", headers=headers
    )
    assert response.status_code == 404
