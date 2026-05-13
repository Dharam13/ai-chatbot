"""
LLM provider manager.

Ollama is the default provider. Groq is used as the cloud fallback when
Ollama is not available and ENABLE_GROQ_FALLBACK=true.
"""

from __future__ import annotations

from typing import Literal

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from loguru import logger

from app.config import settings
from app.exceptions import LLMUnavailableError


LLMProviderName = Literal["ollama", "groq"]


async def _is_ollama_available() -> bool:
    """Return True when the local Ollama server is reachable."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(settings.ollama_base_url)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
        logger.warning(f"Ollama health-check failed: {exc}")
        return False


def _build_ollama() -> ChatOllama:
    """Create the local Ollama chat model."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout,
    )


def _build_groq() -> ChatGroq:
    """Create the optional Groq fallback chat model."""
    if not settings.groq_api_key:
        raise LLMUnavailableError("Groq fallback is enabled, but GROQ_API_KEY is missing.")

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.7,
    )


async def get_llm_with_fallback() -> tuple[BaseChatModel, LLMProviderName]:
    """Return Ollama, or Groq when Ollama is unavailable."""
    if await _is_ollama_available():
        logger.info("LLM provider selected: Ollama ({model})", model=settings.ollama_model)
        return _build_ollama(), "ollama"

    if not settings.enable_groq_fallback:
        raise LLMUnavailableError(
            "Ollama is not available. Start Ollama and make sure "
            f"the model '{settings.ollama_model}' is installed."
        )

    logger.info("LLM provider selected: Groq ({model})", model=settings.groq_model)
    return _build_groq(), "groq"


async def check_providers_status() -> dict[str, bool]:
    """Return availability status for configured LLM providers."""
    return {
        "ollama": await _is_ollama_available(),
        "groq": settings.enable_groq_fallback and bool(settings.groq_api_key),
    }
