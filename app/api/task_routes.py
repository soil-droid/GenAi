"""REST CRUD endpoints for Tasks."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.engine import get_db_session
from app.schemas.tasks import TaskCreate, TaskRead, TaskUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Tasks"])


@router.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
) -> TaskRead:
    """Create a new task."""
    await crud.get_or_create_user(db, payload.user_id)
    task = await crud.create_task(
        db,
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        linked_note_id=payload.linked_note_id,
    )
    return TaskRead.model_validate(task)


@router.get("/tasks", response_model=list[TaskRead])
async def list_tasks(
    user_id: UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> list[TaskRead]:
    """List tasks for a user, with optional status filter."""
    tasks = await crud.get_tasks(db, user_id=user_id, status=status)
    return [TaskRead.model_validate(t) for t in tasks]


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task_status(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> TaskRead:
    """Update a task's status."""
    task = await crud.update_task_status(db, task_id=task_id, status=payload.status)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(task)
