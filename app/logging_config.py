"""Structured logging configuration for Cloud Run compatibility."""

import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configure root logger with structured output.

    Uses JSON-like format for production, human-readable for development.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.environment == "production":
        fmt = (
            '{"severity":"%(levelname)s","timestamp":"%(asctime)s",'
            '"module":"%(name)s","message":"%(message)s"}'
        )
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Quiet noisy libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
