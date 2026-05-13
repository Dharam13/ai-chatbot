"""
Conversational AI Chatbot — FastAPI Application
================================================
Production-grade chatbot with:
  • Automatic LLM fallback (Ollama -> Groq)
  • Session-based conversational memory
  • Tool-calling agent (datetime, weather, news, calculator, wikipedia)
  • In-memory rate limiting
  • LangSmith observability
  • Global exception handling with structured JSON errors

Run:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.exceptions import (
    ChatbotBaseError,
    LLMUnavailableError,
    RateLimitExceededError,
    ToolExecutionError,
)
from app.core.llm import check_providers_status
from app.core.memory import memory_manager
from app.routes.chat import router as chat_router


# ── Export LangSmith env vars for LangChain tracing ──────────
# LangChain reads these directly from os.environ, not from our
# pydantic settings, so we must export them explicitly.
if settings.langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


# ── Lifespan (startup / shutdown) ────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    Runs startup logic before yield and shutdown logic after.
    """
    # ── Startup ──
    logger.info("=" * 60)
    logger.info("🚀 Conversational AI Chatbot starting up...")
    logger.info(f"   Ollama URL    : {settings.ollama_base_url}")
    logger.info(f"   Ollama Model  : {settings.ollama_model}")
    logger.info(f"   Groq Model    : {settings.groq_model}")
    logger.info(f"   Rate Limit    : {settings.rate_limit_per_minute} req/min/session")
    logger.info(f"   LangSmith     : {'enabled' if settings.langchain_tracing_v2 else 'disabled'}")
    logger.info("=" * 60)

    providers = await check_providers_status()
    for name, available in providers.items():
        status = "✅ available" if available else "❌ unavailable"
        logger.info(f"   Provider {name}: {status}")

    yield

    # ── Shutdown ──
    logger.info("👋 Chatbot shutting down. Goodbye!")


# ── FastAPI App ──────────────────────────────────────────────

app = FastAPI(
    title="Conversational AI Chatbot",
    description=(
        "A production-grade conversational AI chatbot with automatic LLM fallback, "
        "session memory, and LangSmith observability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ──────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers ───────────────────────────────

@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    """Return 429 Too Many Requests for rate limit violations."""
    logger.warning(f"Rate limit exceeded: {exc.message}")
    return JSONResponse(
        status_code=429,
        content={"error": exc.message, "code": exc.code},
    )


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError) -> JSONResponse:
    """Return 503 Service Unavailable when no LLM is reachable."""
    logger.error(f"LLM unavailable: {exc.message}")
    return JSONResponse(
        status_code=503,
        content={"error": exc.message, "code": exc.code},
    )


@app.exception_handler(ToolExecutionError)
async def tool_failure_handler(request: Request, exc: ToolExecutionError) -> JSONResponse:
    """Return 500 for unexpected tool execution failures."""
    logger.error(f"Tool failure: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "code": exc.code},
    )


@app.exception_handler(ChatbotBaseError)
async def chatbot_error_handler(request: Request, exc: ChatbotBaseError) -> JSONResponse:
    """Catch-all for any custom chatbot errors not handled above."""
    logger.error(f"Chatbot error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler for completely unexpected exceptions.
    Logs the full traceback and returns a generic error to the client.
    """
    logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected internal error occurred. Please try again.",
            "code": "INTERNAL_ERROR",
        },
    )


# ── Register Routers ────────────────────────────────────────

app.include_router(chat_router)


# ── Health Check Endpoint ────────────────────────────────────

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Check the status of LLM providers and active session count.",
)
async def health_check() -> dict:
    """
    Returns the availability of each LLM provider and the number
    of active chat sessions.
    """
    providers = await check_providers_status()
    return {
        "status": "healthy",
        "providers": providers,
        "active_sessions": memory_manager.active_session_count,
    }
