"""Notes Agent node.

Handles note creation, project briefs, meeting summaries,
and any content-synthesis tasks delegated by the Supervisor.
"""

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.tools.note_tools import list_notes, save_note, search_notes_tool

logger = logging.getLogger(__name__)

NOTES_SYSTEM_PROMPT = """You are the Notes Agent in a multi-agent productivity assistant.

Your responsibilities:
- Create structured notes, project briefs, meeting summaries
- Search existing notes for relevant information
- Organise content with appropriate titles and tags

You have access to these tools:
- save_note: Save a new note with title, content, and tags
- list_notes: List recent notes for a user
- search_notes_tool: Search notes by keyword

Always use the user_id from the conversation context.
Be thorough in your note content — include key details, action items, and relevant context.
"""

NOTES_TOOLS = [save_note, list_notes, search_notes_tool]


async def notes_agent_node(state: AgentState) -> dict:
    """Notes Agent — creates and manages notes."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(NOTES_TOOLS)

    messages = [
        SystemMessage(content=NOTES_SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await llm_with_tools.ainvoke(messages)

    # Execute any tool calls
    tool_results: list[str] = []
    if response.tool_calls:
        tool_map = {t.name: t for t in NOTES_TOOLS}
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            # Inject user_id if not provided
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state["user_id"]
            if tool_name in tool_map:
                result = await tool_map[tool_name].ainvoke(tool_args)
                tool_results.append(f"{tool_name}: {result}")
                logger.info("Notes Agent executed tool: %s", tool_name)

    action_summary = "; ".join(tool_results) if tool_results else response.content[:200]

    trace_entry = {
        "agent": "Notes Agent",
        "action": action_summary,
    }
    execution_trace = list(state.get("execution_trace", []))
    execution_trace.append(trace_entry)

    return {
        "messages": [AIMessage(content=f"[Notes Agent] {action_summary}")],
        "execution_trace": execution_trace,
        "next_agent": "supervisor",
    }
