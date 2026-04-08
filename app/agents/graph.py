"""LangGraph graph assembly and compilation.

This module wires together the Supervisor and all sub-agent nodes
into a single compiled ``StateGraph`` that can be invoked from the
FastAPI route.

Graph topology::

    START → supervisor → {notes_agent | task_agent | scheduling_agent | knowledge_agent} → supervisor → …→ END
"""

import logging

from langgraph.graph import END, START, StateGraph

from app.agents.knowledge_agent import knowledge_agent_node
from app.agents.notes_agent import notes_agent_node
from app.agents.scheduling_agent import scheduling_agent_node
from app.agents.state import AgentState
from app.agents.supervisor import FINISH, supervisor_node
from app.agents.task_agent import task_agent_node

logger = logging.getLogger(__name__)


def _route_from_supervisor(state: AgentState) -> str:
    """Conditional edge: inspect ``next_agent`` and route accordingly."""
    next_agent = state.get("next_agent", FINISH)
    if next_agent == FINISH:
        return END
    return next_agent


def build_graph() -> StateGraph:
    """Construct the multi-agent graph (uncompiled)."""
    graph = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────────────────────────────
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("notes_agent", notes_agent_node)
    graph.add_node("task_agent", task_agent_node)
    graph.add_node("scheduling_agent", scheduling_agent_node)
    graph.add_node("knowledge_agent", knowledge_agent_node)

    # ── Edges ──────────────────────────────────────────────────────────
    # Entry: always start with the Supervisor
    graph.add_edge(START, "supervisor")

    # Supervisor routes to a sub-agent or END
    graph.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "notes_agent": "notes_agent",
            "task_agent": "task_agent",
            "scheduling_agent": "scheduling_agent",
            "knowledge_agent": "knowledge_agent",
            END: END,
        },
    )

    # All sub-agents return to the Supervisor
    graph.add_edge("notes_agent", "supervisor")
    graph.add_edge("task_agent", "supervisor")
    graph.add_edge("scheduling_agent", "supervisor")
    graph.add_edge("knowledge_agent", "supervisor")

    return graph


def compile_graph():
    """Build and compile the graph, ready for invocation.

    Returns:
        A compiled LangGraph ``CompiledStateGraph``.
    """
    graph = build_graph()
    compiled = graph.compile()
    logger.info("Multi-agent graph compiled successfully")
    return compiled


# Pre-compiled singleton — import this in routes
agent_graph = compile_graph()
