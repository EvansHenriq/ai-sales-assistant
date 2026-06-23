from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MessageRole
from app.db.repositories import ConversationRepository


async def test_create_conversation_and_add_messages(db_session: AsyncSession) -> None:
    repo = ConversationRepository(db_session)

    conversation = await repo.create()
    assert conversation.id is not None

    await repo.add_message(conversation_id=conversation.id, role=MessageRole.user, content="hi")
    await repo.add_message(
        conversation_id=conversation.id, role=MessageRole.assistant, content="hello"
    )
    await db_session.commit()

    messages = await repo.list_messages(conversation.id)
    assert [m.content for m in messages] == ["hi", "hello"]

    fetched = await repo.get(conversation.id)
    assert fetched is not None
    assert len(fetched.messages) == 2


async def test_get_missing_conversation_returns_none(db_session: AsyncSession) -> None:
    import uuid

    repo = ConversationRepository(db_session)
    assert await repo.get(uuid.uuid4()) is None
