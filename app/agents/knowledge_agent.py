"""Knowledge Agent (RAG) node.

Searches the user's historical data (notes, tasks) to answer
questions about past decisions, meetings, and context.
"""

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.tools.db_tools import query_knowledge_base

logger = logging.getLogger(__name__)

KNOWLEDGE_SYSTEM_PROMPT = """You are the Knowledge Agent in a multi-agent productivity assistant.

Your responsibilities:
- Search the user's knowledge base to find relevant historical information
- Answer questions about past meetings, decisions, and notes
- Synthesize information from multiple sources into coherent answers

You have access to this tool:
- query_knowledge_base: Search the user's notes and knowledge base

Always use the user_id from the conversation context.
If you cannot find relevant information, say so clearly rather than making up answers.
"""

KNOWLEDGE_TOOLS = [query_knowledge_base]


async def knowledge_agent_node(state: AgentState) -> dict:
    """Knowledge Agent — searches historical data."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(KNOWLEDGE_TOOLS)

    messages = [
        SystemMessage(content=KNOWLEDGE_SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = await llm_with_tools.ainvoke(messages)

    # Execute any tool calls
    tool_results: list[str] = []
    if response.tool_calls:
        tool_map = {t.name: t for t in KNOWLEDGE_TOOLS}
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state["user_id"]
            if tool_name in tool_map:
                result = await tool_map[tool_name].ainvoke(tool_args)
                tool_results.append(f"{tool_name}: {result}")
                logger.info("Knowledge Agent executed tool: %s", tool_name)

    action_summary = "; ".join(tool_results) if tool_results else response.content[:200]

    trace_entry = {
        "agent": "Knowledge Agent",
        "action": action_summary,
    }
    execution_trace = list(state.get("execution_trace", []))
    execution_trace.append(trace_entry)

    return {
        "messages": [AIMessage(content=f"[Knowledge Agent] {action_summary}")],
        "execution_trace": execution_trace,
        "next_agent": "supervisor",
    }
