"""Scheduling Agent node.

Handles calendar event creation, availability checking,
conflict resolution, and time management.
"""

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.tools.calendar_tools import (
    check_conflicts,
    create_calendar_event,
    read_calendar_availability,
)

logger = logging.getLogger(__name__)

SCHEDULING_SYSTEM_PROMPT = """You are the Scheduling Agent in a multi-agent productivity assistant.

Your responsibilities:
- Create calendar events with appropriate times and attendees
- Check calendar availability before scheduling
- Detect and resolve scheduling conflicts
- Handle timezone considerations

You have access to these tools:
- create_calendar_event: Create a new calendar event
- read_calendar_availability: Check what events exist on a given date
- check_conflicts: Check if a proposed time slot conflicts with existing events

Always use the user_id from the conversation context.
Before creating an event, check for conflicts first.
Use ISO-8601 format for all dates and times.
"""

SCHEDULING_TOOLS = [create_calendar_event, read_calendar_availability, check_conflicts]


async def scheduling_agent_node(state: AgentState) -> dict:
    """Scheduling Agent — manages calendar events."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(SCHEDULING_TOOLS)

    messages = [
        SystemMessage(content=SCHEDULING_SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await llm_with_tools.ainvoke(messages)

    # Execute any tool calls
    tool_results: list[str] = []
    if response.tool_calls:
        tool_map = {t.name: t for t in SCHEDULING_TOOLS}
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state["user_id"]
            if tool_name in tool_map:
                result = await tool_map[tool_name].ainvoke(tool_args)
                tool_results.append(f"{tool_name}: {result}")
                logger.info("Scheduling Agent executed tool: %s", tool_name)

    action_summary = "; ".join(tool_results) if tool_results else response.content[:200]

    trace_entry = {
        "agent": "Scheduling Agent",
        "action": action_summary,
    }
    execution_trace = list(state.get("execution_trace", []))
    execution_trace.append(trace_entry)

    return {
        "messages": [AIMessage(content=f"[Scheduling Agent] {action_summary}")],
        "execution_trace": execution_trace,
        "next_agent": "supervisor",
    }
