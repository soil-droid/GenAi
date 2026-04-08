"""REST CRUD endpoints for Notes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.engine import get_db_session
from app.schemas.notes import NoteCreate, NoteRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Notes"])


@router.post("/notes", response_model=NoteRead, status_code=201)
async def create_note(
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db_session),
) -> NoteRead:
    """Create a new note."""
    await crud.get_or_create_user(db, payload.user_id)
    note = await crud.create_note(
        db,
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
    )
    return NoteRead.model_validate(note)


@router.get("/notes", response_model=list[NoteRead])
async def list_notes(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[NoteRead]:
    """List notes for a user."""
    notes = await crud.get_notes(db, user_id=user_id)
    return [NoteRead.model_validate(n) for n in notes]
