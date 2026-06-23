"""Data-access repositories. Repositories own queries; they flush but do not
commit (the session dependency controls the transaction boundary)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Conversation,
    DemoBooking,
    Lead,
    LeadQualification,
    Message,
    MessageRole,
)
from app.qualification.models import LeadQualificationResult


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


class QualificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        conversation_id: UUID,
        lead_id: UUID | None,
        result: LeadQualificationResult,
    ) -> LeadQualification:
        qualification = LeadQualification(
            conversation_id=conversation_id,
            lead_id=lead_id,
            budget=result.budget.value,
            authority=result.authority.value,
            need=result.need.value,
            timeline=result.timeline.value,
            score=result.score,
            stage=result.stage.value,
            rationale=result.rationale,
        )
        self._session.add(qualification)
        await self._session.flush()
        return qualification

    async def latest_for_conversation(self, conversation_id: UUID) -> LeadQualification | None:
        result = await self._session.execute(
            select(LeadQualification)
            .where(LeadQualification.conversation_id == conversation_id)
            .order_by(LeadQualification.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        company: str | None = None,
        phone: str | None = None,
    ) -> Lead:
        """Update an existing lead matched by email, or create a new one."""
        lead: Lead | None = None
        if email:
            result = await self._session.execute(select(Lead).where(Lead.email == email).limit(1))
            lead = result.scalar_one_or_none()

        if lead is None:
            lead = Lead(name=name, email=email, company=company, phone=phone)
            self._session.add(lead)
        else:
            if name is not None:
                lead.name = name
            if company is not None:
                lead.company = company
            if phone is not None:
                lead.phone = phone

        await self._session.flush()
        return lead


class DemoBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        conversation_id: UUID,
        lead_id: UUID | None,
        requested_time: str,
        notes: str | None = None,
    ) -> DemoBooking:
        booking = DemoBooking(
            conversation_id=conversation_id,
            lead_id=lead_id,
            requested_time=requested_time,
            notes=notes,
            status="requested",
        )
        self._session.add(booking)
        await self._session.flush()
        return booking
