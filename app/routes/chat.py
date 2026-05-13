"""
Chat API Routes
===============
Defines all chat-related endpoints:
  - POST   /chat                 — Send a message and get a response
  - DELETE  /chat/{session_id}   — Clear a session's history
  - GET     /chat/{session_id}/history — Retrieve full chat history
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter
from loguru import logger

from app.core.agent import run_chat
from app.core.memory import memory_manager
from app.core.rate_limiter import rate_limiter


# ── Router ───────────────────────────────────────────────────
router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Request / Response Schemas ───────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat message payload."""

    session_id: str = Field(
        ...,
        min_length=1,
        description="Unique session identifier for conversation tracking",
        examples=["user-abc-123"],
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message to the chatbot",
        examples=["What's the weather in London?"],
    )


class ChatResponse(BaseModel):
    """Outgoing chat response payload."""

    session_id: str
    reply: str
    llm_provider: str
    tools_used: list[str]


class HistoryResponse(BaseModel):
    """Full conversation history for a session."""

    session_id: str
    history: list[dict]
    message_count: int


class DeleteResponse(BaseModel):
    """Confirmation of session deletion."""

    session_id: str
    status: str


# ── Endpoints ────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message",
    description="Send a user message and receive an AI response with tool usage metadata.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user message through the chatbot.

    Steps:
      1. Enforce rate limit for the session.
      2. Generate a reply with the LLM and session memory.
      3. Return structured response with metadata.
    """
    logger.info(f"POST /chat | session={request.session_id}")

    # Rate-limit check (raises RateLimitExceededError if exceeded)
    rate_limiter.check(request.session_id)

    # Generate the reply
    result = await run_chat(
        session_id=request.session_id,
        user_message=request.message,
    )

    return ChatResponse(
        session_id=request.session_id,
        reply=result.reply,
        llm_provider=result.llm_provider,
        tools_used=result.tools_used,
    )


@router.delete(
    "/{session_id}",
    response_model=DeleteResponse,
    summary="Clear session history",
    description="Delete all conversation history for a specific session.",
)
async def clear_session(session_id: str) -> DeleteResponse:
    """Clear conversation memory for the given session."""
    logger.info(f"DELETE /chat/{session_id}")

    deleted = memory_manager.clear_session(session_id)
    status = "Session cleared successfully" if deleted else "Session not found"

    return DeleteResponse(session_id=session_id, status=status)


@router.get(
    "/{session_id}/history",
    response_model=HistoryResponse,
    summary="Get chat history",
    description="Retrieve the full conversation history for a session.",
)
async def get_history(session_id: str) -> HistoryResponse:
    """Return the full chat history for a session."""
    logger.info(f"GET /chat/{session_id}/history")

    history = memory_manager.get_history(session_id)

    return HistoryResponse(
        session_id=session_id,
        history=history,
        message_count=len(history),
    )
