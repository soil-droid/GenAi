"""Shared response envelope and utility schemas."""

from pydantic import BaseModel


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str
    message: str = ""


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
