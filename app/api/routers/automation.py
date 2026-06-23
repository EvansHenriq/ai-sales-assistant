"""Service-automation endpoints: capture lead contact and schedule a demo.

These are deterministic actions the assistant orchestrates during a conversation.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import DbSession, RequireApiKey
from app.api.schemas import DemoBookingCreate, DemoBookingRead, LeadCapture, LeadRead
from app.core.rate_limit import limiter, rate_limit
from app.db.repositories import (
    ConversationRepository,
    DemoBookingRepository,
    LeadRepository,
)

router = APIRouter(prefix="/v1/conversations", tags=["automation"])


@router.post(
    "/{conversation_id}/lead", response_model=LeadRead, status_code=status.HTTP_201_CREATED
)
@limiter.limit(rate_limit)
async def capture_lead(
    request: Request,
    conversation_id: UUID,
    payload: LeadCapture,
    session: DbSession,
    _: RequireApiKey,
) -> LeadRead:
    conversation = await ConversationRepository(session).get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    lead = await LeadRepository(session).upsert(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        phone=payload.phone,
    )
    conversation.lead_id = lead.id
    await session.flush()
    return LeadRead.model_validate(lead)


@router.post(
    "/{conversation_id}/schedule-demo",
    response_model=DemoBookingRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(rate_limit)
async def schedule_demo(
    request: Request,
    conversation_id: UUID,
    payload: DemoBookingCreate,
    session: DbSession,
    _: RequireApiKey,
) -> DemoBookingRead:
    conversation = await ConversationRepository(session).get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.lead_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Capture lead contact before scheduling a demo",
        )

    booking = await DemoBookingRepository(session).create(
        conversation_id=conversation_id,
        lead_id=conversation.lead_id,
        requested_time=payload.requested_time,
        notes=payload.notes,
    )
    return DemoBookingRead.model_validate(booking)
