"""Schemas for Task CRUD endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Payload to create a new task."""

    user_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    linked_note_id: UUID | None = None


class TaskRead(BaseModel):
    """Task returned to the client."""

    task_id: UUID
    user_id: UUID
    title: str
    description: str | None = None
    status: str = "pending"
    due_date: datetime | None = None
    linked_note_id: UUID | None = None

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    """Payload to update a task's status."""

    status: str = Field(..., pattern="^(pending|in_progress|completed)$")
