"""Agent invocation endpoint — the primary API for the multi-agent system."""

import logging
import traceback

from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from app.agents.graph import agent_graph
from app.schemas.agent import AgentInvokeRequest, AgentInvokeResponse, ExecutionStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Agent"])


@router.post("/agent/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(request: AgentInvokeRequest) -> AgentInvokeResponse:
    """Invoke the multi-agent system with a natural-language prompt.

    The Supervisor decomposes the prompt into steps, routes to sub-agents,
    and returns a full execution trace plus a final reply.
    """
    logger.info(
        "Agent invocation: user=%s session=%s prompt='%s'",
        request.user_id,
        request.session_id,
        request.prompt[:100],
    )

    try:
        # Build initial state
        initial_state = {
            "messages": [HumanMessage(content=request.prompt)],
            "plan": [],
            "next_agent": "",
            "execution_trace": [],
            "user_id": str(request.user_id),
            "final_reply": "",
        }

        # Run the compiled graph
        result = await agent_graph.ainvoke(initial_state)

        # Build response
        execution_trace = [
            ExecutionStep(
                agent=step.get("agent", "Unknown"),
                action=step.get("action", ""),
                resource_id=step.get("resource_id"),
            )
            for step in result.get("execution_trace", [])
        ]

        return AgentInvokeResponse(
            status="success",
            execution_trace=execution_trace,
            final_reply=result.get("final_reply", "Done."),
        )

    except Exception as e:
        logger.error("Agent invocation failed: %s\n%s", e, traceback.format_exc())
        return AgentInvokeResponse(
            status="error",
            execution_trace=[],
            final_reply=f"An error occurred: {e!s}",
        )
