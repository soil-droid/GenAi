"""MCP-style tool wrappers for Calendar / Schedule operations."""

import uuid
import logging
from datetime import datetime

from langchain_core.tools import tool

from app.db.crud import (
    create_schedule as _crud_create_schedule,
    get_schedules as _crud_get_schedules,
    check_schedule_conflicts as _crud_check_conflicts,
)
from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


@tool
async def create_calendar_event(
    user_id: str,
    event_title: str,
    start_time: str,
    end_time: str,
    attendees: str = "",
) -> str:
    """Create a new calendar event.

    Args:
        user_id: The user's UUID.
        event_title: Title of the event.
        start_time: ISO-8601 start time (e.g. "2026-04-14T10:00:00Z").
        end_time: ISO-8601 end time (e.g. "2026-04-14T11:00:00Z").
        attendees: Comma-separated list of attendee emails.

    Returns:
        Confirmation string with the event ID.
    """
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    attendee_list = (
        [a.strip() for a in attendees.split(",") if a.strip()]
        if attendees
        else None
    )

    async with async_session_factory() as db:
        event = await _crud_create_schedule(
            db,
            user_id=uuid.UUID(user_id),
            event_title=event_title,
            start_time=start,
            end_time=end,
            attendees=attendee_list,
        )
        await db.commit()
    return f"Calendar event created: '{event_title}' (id={event.event_id})"


@tool
async def read_calendar_availability(
    user_id: str,
    date: str,
    timezone: str = "UTC",
) -> str:
    """Check calendar availability for a given date.

    Args:
        user_id: The user's UUID.
        date: Date to check in ISO-8601 format (e.g. "2026-04-14").
        timezone: Timezone string (currently informational).

    Returns:
        List of existing events on that date, or 'No events' if free.
    """
    day_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
    day_end = datetime.fromisoformat(f"{date}T23:59:59+00:00")

    async with async_session_factory() as db:
        events = await _crud_get_schedules(
            db, user_id=uuid.UUID(user_id), from_time=day_start
        )
        # Filter to only that day
        events = [e for e in events if e.start_time < day_end]

    if not events:
        return f"No events on {date}. The entire day is free."

    lines = [
        f"- {e.event_title}: {e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}"
        for e in events
    ]
    return f"Events on {date}:\n" + "\n".join(lines)


@tool
async def check_conflicts(
    user_id: str,
    start_time: str,
    end_time: str,
) -> str:
    """Check if a proposed time slot has scheduling conflicts.

    Args:
        user_id: The user's UUID.
        start_time: ISO-8601 start time.
        end_time: ISO-8601 end time.

    Returns:
        List of conflicting events, or 'No conflicts'.
    """
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    async with async_session_factory() as db:
        conflicts = await _crud_check_conflicts(
            db, user_id=uuid.UUID(user_id), start_time=start, end_time=end
        )
    if not conflicts:
        return "No scheduling conflicts. The slot is available."

    lines = [
        f"- CONFLICT: {c.event_title} ({c.start_time} – {c.end_time})"
        for c in conflicts
    ]
    return f"Found {len(conflicts)} conflict(s):\n" + "\n".join(lines)
