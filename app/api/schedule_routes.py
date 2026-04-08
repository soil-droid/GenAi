"""REST CRUD endpoints for Schedules."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.engine import get_db_session
from app.schemas.schedules import ScheduleCreate, ScheduleRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Schedules"])


@router.post("/schedules", response_model=ScheduleRead, status_code=201)
async def create_schedule(
    payload: ScheduleCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    """Create a new calendar event."""
    await crud.get_or_create_user(db, payload.user_id)
    event = await crud.create_schedule(
        db,
        user_id=payload.user_id,
        event_title=payload.event_title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        attendees=payload.attendees,
    )
    return ScheduleRead.model_validate(event)


@router.get("/schedules", response_model=list[ScheduleRead])
async def list_schedules(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleRead]:
    """List upcoming events for a user."""
    events = await crud.get_schedules(db, user_id=user_id)
    return [ScheduleRead.model_validate(e) for e in events]
