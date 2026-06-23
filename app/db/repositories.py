"""Data-access repositories. Repositories own queries; they flush but do not
commit (the session dependency controls the transaction boundary)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, Message, MessageRole


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, lead_id: UUID | None = None) -> Conversation:
        conversation = Conversation(lead_id=lead_id)
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get(self, conversation_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        *,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        redacted_content: str | None = None,
        tokens: int | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            redacted_content=redacted_content,
            tokens=tokens,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
