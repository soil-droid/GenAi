"""Health-check endpoint for Cloud Run and load balancers."""

from fastapi import APIRouter

from app.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
    )
