"""Schemas for the agent invocation endpoint."""

from uuid import UUID

from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    """Payload sent by the client to invoke the multi-agent system."""

    user_id: UUID
    session_id: str = Field(..., min_length=1, description="Client session identifier")
    prompt: str = Field(..., min_length=1, description="Natural-language instruction")


class ExecutionStep(BaseModel):
    """One step in the agent execution trace."""

    agent: str
    action: str
    resource_id: str | None = None


class AgentInvokeResponse(BaseModel):
    """Full response returned after agent execution."""

    status: str = "success"
    execution_trace: list[ExecutionStep] = Field(default_factory=list)
    final_reply: str = ""
