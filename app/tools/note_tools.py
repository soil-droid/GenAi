"""MCP-style tool wrappers for Note operations.

These functions are decorated with ``@tool`` so LangGraph agents can
invoke them during execution.  In the MVP they call the CRUD layer
directly; in production they would go through an MCP server.
"""

import uuid
import logging

from langchain_core.tools import tool

from app.db.crud import create_note as _crud_create_note
from app.db.crud import get_notes as _crud_get_notes
from app.db.crud import search_notes as _crud_search_notes
from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


@tool
async def save_note(
    user_id: str,
    title: str,
    content: str = "",
    tags: str = "",
) -> str:
    """Save a new note for the user.

    Args:
        user_id: The user's UUID.
        title: Title of the note.
        content: Body / content of the note.
        tags: Comma-separated tags (e.g. "project,acme,brief").

    Returns:
        Confirmation string with the note ID.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    async with async_session_factory() as db:
        note = await _crud_create_note(
            db,
            user_id=uuid.UUID(user_id),
            title=title,
            content=content or None,
            tags=tag_list,
        )
        await db.commit()
    return f"Note saved: '{title}' (id={note.note_id})"


@tool
async def list_notes(user_id: str, limit: int = 10) -> str:
    """List recent notes for the user.

    Args:
        user_id: The user's UUID.
        limit: Max number of notes to return.

    Returns:
        Formatted list of notes.
    """
    async with async_session_factory() as db:
        notes = await _crud_get_notes(db, user_id=uuid.UUID(user_id), limit=limit)
    if not notes:
        return "No notes found."
    lines = [f"- {n.title} (id={n.note_id})" for n in notes]
    return f"Found {len(notes)} notes:\n" + "\n".join(lines)


@tool
async def search_notes_tool(user_id: str, query: str) -> str:
    """Search notes by keyword.

    Args:
        user_id: The user's UUID.
        query: Search keyword.

    Returns:
        Matching notes or 'No results'.
    """
    async with async_session_factory() as db:
        notes = await _crud_search_notes(
            db, user_id=uuid.UUID(user_id), query=query
        )
    if not notes:
        return f"No notes matching '{query}'."
    lines = [f"- {n.title}: {(n.content or '')[:100]}" for n in notes]
    return f"Found {len(notes)} matching notes:\n" + "\n".join(lines)
