"""Shared LangChain LLM client factory."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI

from src.config import get_settings


def get_llm(model: Optional[str] = None, temperature: float = 0.2) -> ChatOpenAI:
    """Return a configured ChatOpenAI instance.

    Args:
        model: Override the model name. Falls back to settings.llm_model.
        temperature: Sampling temperature (lower = more deterministic).

    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    settings = get_settings()
    settings.validate_openai_key()

    chosen_model = model or settings.llm_model
    return ChatOpenAI(
        model=chosen_model,
        temperature=temperature,
        api_key=settings.openai_api_key,
    )
