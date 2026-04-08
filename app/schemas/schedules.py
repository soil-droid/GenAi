"""Schemas for Schedule CRUD endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """Payload to create a new calendar event."""

    user_id: UUID
    event_title: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    attendees: list[str] | None = None


class ScheduleRead(BaseModel):
    """Schedule returned to the client."""

    event_id: UUID
    user_id: UUID
    event_title: str
    start_time: datetime
    end_time: datetime
    attendees: list[str] | None = None

    model_config = {"from_attributes": True}
