"""Request/response schemas for the API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ConversationStatus, MessageRole


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationCreate(BaseModel):
    lead_id: UUID | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ConversationStatus
    lead_id: UUID | None
    created_at: datetime
    messages: list[MessageRead] = []


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class UsageRead(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class MessageTurnResponse(BaseModel):
    conversation_id: UUID
    reply: str
    usage: UsageRead


class QualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    budget: str
    authority: str
    need: str
    timeline: str
    score: int
    stage: str
    rationale: str
    created_at: datetime
