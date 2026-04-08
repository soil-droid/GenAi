"""LangGraph shared state definition for the multi-agent system."""

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Shared state passed between all agent nodes in the graph.

    Attributes:
        messages: Chat history (auto-accumulated via ``add_messages`` reducer).
        plan: Steps the Supervisor has decided to execute.
        next_agent: The name of the next sub-agent to route to (or ``FINISH``).
        execution_trace: Audit log of agent actions taken so far.
        user_id: The requesting user's UUID (string form).
        final_reply: The natural-language reply returned to the user.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    plan: list[str]
    next_agent: str
    execution_trace: list[dict[str, str]]
    user_id: str
    final_reply: str
