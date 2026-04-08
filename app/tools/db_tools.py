"""MCP-style tool for Knowledge / RAG queries.

In the MVP this performs simple keyword search across notes.
In production this would use pgvector embeddings.
"""

import uuid
import logging

from langchain_core.tools import tool

from app.db.crud import search_notes as _crud_search_notes
from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


@tool
async def query_knowledge_base(user_id: str, question: str) -> str:
    """Search the knowledge base (notes) to answer a question.

    This tool performs keyword search across the user's notes to find
    relevant historical information.

    Args:
        user_id: The user's UUID.
        question: The natural-language question to search for.

    Returns:
        Relevant note excerpts, or a 'no results' message.
    """
    # Extract key terms from the question for search
    # In production, this would use embeddings / vector similarity
    async with async_session_factory() as db:
        notes = await _crud_search_notes(
            db, user_id=uuid.UUID(user_id), query=question, limit=5
        )

    if not notes:
        return (
            f"No relevant information found in the knowledge base for: '{question}'. "
            "The user may not have any notes on this topic yet."
        )

    results: list[str] = []
    for note in notes:
        snippet = (note.content or "")[:300]
        tags_str = ", ".join(note.tags) if note.tags else "none"
        results.append(
            f"📄 **{note.title}** (tags: {tags_str})\n{snippet}"
        )

    return (
        f"Found {len(notes)} relevant knowledge entries:\n\n"
        + "\n---\n".join(results)
    )
