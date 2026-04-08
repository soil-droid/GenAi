"""Task Agent node.

Handles task creation, milestone breakdown, status tracking,
and project management delegated by the Supervisor.
"""

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.tools.task_tools import create_task, list_tasks, update_task

logger = logging.getLogger(__name__)

TASK_SYSTEM_PROMPT = """You are the Task Agent in a multi-agent productivity assistant.

Your responsibilities:
- Break down goals into concrete, actionable tasks with clear titles
- Set appropriate due dates based on the user's request
- Track and update task statuses
- Link tasks to related notes when applicable

You have access to these tools:
- create_task: Create a new task with title, description, due date
- list_tasks: List tasks for a user, optionally filtered by status
- update_task: Update a task's status (pending / in_progress / completed)

Always use the user_id from the conversation context.
When creating multiple tasks, create them one at a time with descriptive titles.
"""

TASK_TOOLS = [create_task, list_tasks, update_task]


async def task_agent_node(state: AgentState) -> dict:
    """Task Agent — creates and manages tasks."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(TASK_TOOLS)

    messages = [
        SystemMessage(content=TASK_SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await llm_with_tools.ainvoke(messages)

    # Execute any tool calls
    tool_results: list[str] = []
    if response.tool_calls:
        tool_map = {t.name: t for t in TASK_TOOLS}
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state["user_id"]
            if tool_name in tool_map:
                result = await tool_map[tool_name].ainvoke(tool_args)
                tool_results.append(f"{tool_name}: {result}")
                logger.info("Task Agent executed tool: %s", tool_name)

    action_summary = "; ".join(tool_results) if tool_results else response.content[:200]

    trace_entry = {
        "agent": "Task Agent",
        "action": action_summary,
    }
    execution_trace = list(state.get("execution_trace", []))
    execution_trace.append(trace_entry)

    return {
        "messages": [AIMessage(content=f"[Task Agent] {action_summary}")],
        "execution_trace": execution_trace,
        "next_agent": "supervisor",
    }
