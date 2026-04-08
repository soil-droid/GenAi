"""Typed CRUD operations for all database models."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Note, Schedule, Task, User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def get_or_create_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Return existing user or create a placeholder."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(user_id=user_id, email=f"{user_id}@placeholder.local")
        db.add(user)
        await db.flush()
        logger.info("Created placeholder user %s", user_id)
    return user


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

async def create_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str | None = None,
    tags: list[str] | None = None,
) -> Note:
    """Create and return a new note."""
    note = Note(user_id=user_id, title=title, content=content, tags=tags)
    db.add(note)
    await db.flush()
    logger.info("Created note '%s' (id=%s)", title, note.note_id)
    return note


async def get_notes(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[Note]:
    """List notes for a user, newest first."""
    result = await db.execute(
        select(Note)
        .where(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_note_by_id(db: AsyncSession, note_id: uuid.UUID) -> Note | None:
    """Fetch a single note by ID."""
    result = await db.execute(select(Note).where(Note.note_id == note_id))
    return result.scalar_one_or_none()


async def search_notes(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    limit: int = 10,
) -> list[Note]:
    """Simple keyword search across note titles and content."""
    pattern = f"%{query}%"
    result = await db.execute(
        select(Note)
        .where(
            Note.user_id == user_id,
            (Note.title.ilike(pattern)) | (Note.content.ilike(pattern)),
        )
        .order_by(Note.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

async def create_task(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    description: str | None = None,
    due_date: datetime | None = None,
    linked_note_id: uuid.UUID | None = None,
) -> Task:
    """Create and return a new task."""
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        due_date=due_date,
        linked_note_id=linked_note_id,
    )
    db.add(task)
    await db.flush()
    logger.info("Created task '%s' (id=%s)", title, task.task_id)
    return task


async def get_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
) -> list[Task]:
    """List tasks for a user, with optional status filter."""
    stmt = select(Task).where(Task.user_id == user_id)
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.due_date.asc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task_status(
    db: AsyncSession,
    task_id: uuid.UUID,
    status: str,
) -> Task | None:
    """Update a task's status. Returns None if not found."""
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return None
    task.status = status
    await db.flush()
    logger.info("Updated task %s → status=%s", task_id, status)
    return task


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

async def create_schedule(
    db: AsyncSession,
    user_id: uuid.UUID,
    event_title: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str] | None = None,
) -> Schedule:
    """Create and return a new calendar event."""
    event = Schedule(
        user_id=user_id,
        event_title=event_title,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
    )
    db.add(event)
    await db.flush()
    logger.info("Created event '%s' (id=%s)", event_title, event.event_id)
    return event


async def get_schedules(
    db: AsyncSession,
    user_id: uuid.UUID,
    from_time: datetime | None = None,
    limit: int = 50,
) -> list[Schedule]:
    """List upcoming events for a user."""
    stmt = select(Schedule).where(Schedule.user_id == user_id)
    if from_time:
        stmt = stmt.where(Schedule.start_time >= from_time)
    stmt = stmt.order_by(Schedule.start_time.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def check_schedule_conflicts(
    db: AsyncSession,
    user_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
) -> list[Schedule]:
    """Return any events that overlap with the given time window."""
    result = await db.execute(
        select(Schedule).where(
            Schedule.user_id == user_id,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time,
        )
    )
    return list(result.scalars().all())
