"""FastAPI application entry point.

This module creates the FastAPI app, configures middleware,
registers all routers, and sets up the application lifespan
(startup/shutdown hooks for the database connection pool).
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging

# Set up logging before anything else
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    # ── Startup ────────────────────────────────────────────────────────
    logger.info(
        "🚀 Starting Multi-Agent Productivity Assistant (env=%s)",
        settings.environment,
    )
    # Import engine here to avoid circular imports during testing
    from app.db.engine import engine  # noqa: F811
    from app.db.models import Base

    logger.info("Database engine created configured for immediate setup")

    # Automatically create tables for SQLite MVP
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Database schema initialized.")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("Shutting down — disposing database engine")
    await engine.dispose()
    logger.info("✅ Shutdown complete")


def create_app() -> FastAPI:
    """Application factory."""
    application = FastAPI(
        title="Multi-Agent Productivity Assistant",
        description=(
            "A GCP-native productivity assistant powered by LangGraph and "
            "Vertex AI Gemini. Uses a Supervisor-Worker multi-agent architecture "
            "to handle notes, tasks, scheduling, and knowledge queries."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────
    from app.api.health import router as health_router
    from app.api.agent_routes import router as agent_router
    from app.api.task_routes import router as task_router
    from app.api.note_routes import router as note_router
    from app.api.schedule_routes import router as schedule_router

    application.include_router(health_router)
    application.include_router(agent_router)
    application.include_router(task_router)
    application.include_router(note_router)
    application.include_router(schedule_router)

    from fastapi.responses import FileResponse
    import os

    @application.get("/", include_in_schema=False)
    async def serve_ui():
        ui_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
        return FileResponse(ui_path)

    return application


# The ASGI app — Uvicorn targets this via `app.main:app`
app = create_app()
