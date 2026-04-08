"""Vertex AI Gemini LLM factory."""

import logging
from functools import lru_cache

from langchain_google_vertexai import ChatVertexAI

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> ChatVertexAI:
    """Return a cached ChatVertexAI instance.

    The LLM is initialised once and reused across all agent nodes
    to avoid re-authenticating on every request.
    """
    logger.info(
        "Initialising Vertex AI LLM (model=%s, project=%s)",
        settings.gemini_model,
        settings.gcp_project_id,
    )
    return ChatVertexAI(
        model_name=settings.gemini_model,
        project=settings.gcp_project_id,
        location=settings.gcp_region,
        temperature=0.2,
        max_output_tokens=4096,
        streaming=False,
    )
