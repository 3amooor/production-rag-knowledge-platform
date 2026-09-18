"""Request and response contracts for conversations and grounded answers."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    title: str | None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=12_000)


class CitationResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    excerpt: str
    score: float


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    status: str
    citations: list[CitationResponse] = []
    created_at: datetime


class AnswerResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
