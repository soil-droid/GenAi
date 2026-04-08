"""MCP-style tool wrappers for Task operations."""

import uuid
import logging
from datetime import datetime

from langchain_core.tools import tool

from app.db.crud import (
    create_task as _crud_create_task,
    get_tasks as _crud_get_tasks,
    update_task_status as _crud_update_task_status,
)
from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


@tool
async def create_task(
    user_id: str,
    title: str,
    description: str = "",
    due_date: str = "",
    linked_note_id: str = "",
) -> str:
    """Create a new task for the user.

    Args:
        user_id: The user's UUID.
        title: Title of the task.
        description: Detailed description.
        due_date: ISO-8601 due date (e.g. "2026-04-15T00:00:00Z"). Empty = no deadline.
        linked_note_id: Optional UUID of a related note.

    Returns:
        Confirmation string with the task ID.
    """
    parsed_due: datetime | None = None
    if due_date:
        parsed_due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

    note_id: uuid.UUID | None = None
    if linked_note_id:
        note_id = uuid.UUID(linked_note_id)

    async with async_session_factory() as db:
        task = await _crud_create_task(
            db,
            user_id=uuid.UUID(user_id),
            title=title,
            description=description or None,
            due_date=parsed_due,
            linked_note_id=note_id,
        )
        await db.commit()
    return f"Task created: '{title}' (id={task.task_id})"


@tool
async def list_tasks(user_id: str, status: str = "") -> str:
    """List tasks for the user, optionally filtered by status.

    Args:
        user_id: The user's UUID.
        status: Filter by status (pending / in_progress / completed). Empty = all.

    Returns:
        Formatted list of tasks.
    """
    async with async_session_factory() as db:
        tasks = await _crud_get_tasks(
            db,
            user_id=uuid.UUID(user_id),
            status=status or None,
        )
    if not tasks:
        return "No tasks found."
    lines = [
        f"- [{t.status}] {t.title} (due={t.due_date}, id={t.task_id})"
        for t in tasks
    ]
    return f"Found {len(tasks)} tasks:\n" + "\n".join(lines)


@tool
async def update_task(task_id: str, status: str) -> str:
    """Update a task's status.

    Args:
        task_id: The task's UUID.
        status: New status (pending / in_progress / completed).

    Returns:
        Confirmation or error message.
    """
    async with async_session_factory() as db:
        task = await _crud_update_task_status(
            db, task_id=uuid.UUID(task_id), status=status
        )
        await db.commit()
    if task is None:
        return f"Task {task_id} not found."
    return f"Task '{task.title}' updated to status='{status}'."
