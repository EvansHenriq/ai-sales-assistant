"""Conversation endpoints: create and retrieve. Message posting (which triggers
the agent) is added in a later phase."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import DbSession, RequireApiKey
from app.api.schemas import ConversationCreate, ConversationRead
from app.core.rate_limit import limiter, rate_limit
from app.db.repositories import ConversationRepository

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(rate_limit)
async def create_conversation(
    request: Request,
    payload: ConversationCreate,
    session: DbSession,
    _: RequireApiKey,
) -> ConversationRead:
    repo = ConversationRepository(session)
    conversation = await repo.create(lead_id=payload.lead_id)
    # Build the response explicitly: a freshly created conversation has no
    # messages, and we avoid touching the (unloaded) relationship under async.
    return ConversationRead(
        id=conversation.id,
        status=conversation.status,
        lead_id=conversation.lead_id,
        created_at=conversation.created_at,
        messages=[],
    )


@router.get("/{conversation_id}", response_model=ConversationRead)
@limiter.limit(rate_limit)
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    session: DbSession,
    _: RequireApiKey,
) -> ConversationRead:
    repo = ConversationRepository(session)
    conversation = await repo.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationRead.model_validate(conversation)
