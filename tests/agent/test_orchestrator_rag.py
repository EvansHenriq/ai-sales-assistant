from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import AgentOrchestrator
from app.db.repositories import ConversationRepository
from app.rag.types import RetrievedChunk
from tests.fakes import FakeLLMClient, FakeRetriever


async def test_orchestrator_injects_retrieved_context(
    db_session: AsyncSession, fake_llm: FakeLLMClient
) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    retriever = FakeRetriever(
        [RetrievedChunk(content="Growth is $99/month.", source="Pricing", score=0.9)]
    )
    orchestrator = AgentOrchestrator(llm=fake_llm, repo=repo, retriever=retriever)

    await orchestrator.handle_turn(
        conversation_id=conversation.id, user_message="how much is growth?"
    )

    system_prompt = fake_llm.calls[0]["system"]
    assert isinstance(system_prompt, str)
    assert "Growth is $99/month." in system_prompt
    assert "Pricing" in system_prompt
    assert retriever.queries == ["how much is growth?"]


async def test_orchestrator_without_retriever_uses_base_prompt(
    db_session: AsyncSession, fake_llm: FakeLLMClient
) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    orchestrator = AgentOrchestrator(llm=fake_llm, repo=repo)

    await orchestrator.handle_turn(conversation_id=conversation.id, user_message="hi")

    system_prompt = fake_llm.calls[0]["system"]
    assert isinstance(system_prompt, str)
    assert "# Knowledge base" not in system_prompt
