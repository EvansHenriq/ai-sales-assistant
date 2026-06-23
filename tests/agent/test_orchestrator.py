from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import AgentOrchestrator
from app.agent.types import ChatMessage
from app.db.models import MessageRole
from app.db.repositories import ConversationRepository
from tests.fakes import FakeLLMClient


async def test_handle_turn_persists_user_and_assistant_messages(
    db_session: AsyncSession, fake_llm: FakeLLMClient
) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    fake_llm.reply = "FlowMetrics is a product-analytics platform."
    orchestrator = AgentOrchestrator(llm=fake_llm, repo=repo)

    result = await orchestrator.handle_turn(
        conversation_id=conversation.id, user_message="what is flowmetrics?"
    )

    assert result.reply == "FlowMetrics is a product-analytics platform."
    assert result.usage.total_tokens == 15

    messages = await repo.list_messages(conversation.id)
    assert [(m.role, m.content) for m in messages] == [
        (MessageRole.user, "what is flowmetrics?"),
        (MessageRole.assistant, "FlowMetrics is a product-analytics platform."),
    ]


async def test_handle_turn_passes_history_and_system_prompt(
    db_session: AsyncSession, fake_llm: FakeLLMClient
) -> None:
    repo = ConversationRepository(db_session)
    conversation = await repo.create()
    orchestrator = AgentOrchestrator(llm=fake_llm, repo=repo)

    await orchestrator.handle_turn(conversation_id=conversation.id, user_message="hi")

    call = fake_llm.calls[0]
    assert isinstance(call["system"], str) and call["system"]
    history = call["messages"]
    assert isinstance(history, list)
    assert history[-1] == ChatMessage(role="user", content="hi")
