"""Schemas for Note CRUD endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Payload to create a new note."""

    user_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = None
    tags: list[str] | None = None


class NoteRead(BaseModel):
    """Note returned to the client."""

    note_id: UUID
    user_id: UUID
    title: str
    content: str | None = None
    tags: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
