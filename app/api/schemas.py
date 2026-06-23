"""Request/response schemas for the API."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class LeadCapture(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    company: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def _require_at_least_one(self) -> Self:
        if not any([self.name, self.email, self.company, self.phone]):
            raise ValueError("At least one lead field must be provided")
        return self


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None
    email: str | None
    company: str | None
    phone: str | None
    created_at: datetime


class DemoBookingCreate(BaseModel):
    requested_time: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class DemoBookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    lead_id: UUID | None
    requested_time: str
    notes: str | None
    status: str
    created_at: datetime
