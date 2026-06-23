"""Request/response schemas for the API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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
