"""Supervisor (Orchestrator) agent node.

The Supervisor is the brain of the multi-agent system. It:
1. Interprets the user's natural-language request.
2. Decomposes it into a plan of steps.
3. Routes execution to the correct sub-agent.
4. Decides when the overall goal is achieved and produces a final reply.
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

AGENT_NAMES = ["notes_agent", "task_agent", "scheduling_agent", "knowledge_agent"]
FINISH = "FINISH"

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor of a multi-agent productivity assistant.

Your job is to:
1. Understand the user's request.
2. Decompose it into discrete steps.
3. Decide which sub-agent should handle the NEXT step.

Available agents:
- notes_agent: Creates notes, project briefs, meeting summaries. Use for any content creation or note-taking.
- task_agent: Creates, lists, and updates tasks/milestones. Use for task management and project breakdown.
- scheduling_agent: Creates calendar events, checks availability, resolves conflicts. Use for anything time-related.
- knowledge_agent: Searches the user's existing notes and knowledge base. Use for answering questions about past data.

You MUST respond with valid JSON in this exact format:
{{
    "plan": ["step 1 description", "step 2 description", ...],
    "next_agent": "<agent_name or FINISH>",
    "reasoning": "Why this agent is needed next"
}}

Rules:
- If the plan is already set in the conversation and all steps are done, set next_agent to "FINISH".
- Only route to ONE agent at a time.
- After each agent completes, you will be called again to decide the next step.
- When next_agent is "FINISH", also include a "final_reply" field with a friendly summary for the user.
"""


async def supervisor_node(state: AgentState) -> dict:
    """Supervisor node — routes work to sub-agents or terminates."""
    llm = get_llm()

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        *state["messages"],
    ]

    # Add context about what has been done so far
    if state.get("execution_trace"):
        trace_summary = "\n".join(
            f"- {step['agent']}: {step['action']}"
            for step in state["execution_trace"]
        )
        messages.append(
            HumanMessage(
                content=(
                    f"EXECUTION PROGRESS SO FAR:\n{trace_summary}\n\n"
                    "Based on the original request and what has been completed, "
                    "decide what to do next. Respond with JSON."
                )
            )
        )

    response = await llm.ainvoke(messages)
    response_text = response.content

    # Parse the JSON response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        decision = json.loads(json_str.strip())
    except (json.JSONDecodeError, IndexError):
        logger.warning("Supervisor returned non-JSON: %s", response_text[:200])
        decision = {
            "plan": ["Handle the user's request"],
            "next_agent": "notes_agent",
            "reasoning": "Defaulting to notes agent due to parse error",
        }

    next_agent = decision.get("next_agent", FINISH)
    plan = decision.get("plan", state.get("plan", []))

    # Validate agent name
    if next_agent not in AGENT_NAMES and next_agent != FINISH:
        logger.warning("Invalid agent name '%s', defaulting to FINISH", next_agent)
        next_agent = FINISH

    result: dict = {
        "next_agent": next_agent,
        "plan": plan,
    }

    if next_agent == FINISH:
        final_reply = decision.get(
            "final_reply",
            "All tasks have been completed successfully!",
        )
        result["final_reply"] = final_reply

    logger.info(
        "Supervisor decision: next_agent=%s, plan_steps=%d",
        next_agent,
        len(plan),
    )
    return result
