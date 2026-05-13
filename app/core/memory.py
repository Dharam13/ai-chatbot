"""
Conversation Memory Manager
============================
In-memory, session-scoped conversation history.

Each session_id maps to an ordered list of (role, content) message pairs.
The full history is injected into every LLM request so the model maintains
conversational context across turns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from loguru import logger


@dataclass
class SessionHistory:
    """Chat history for a single session."""

    messages: List[BaseMessage] = field(default_factory=list)


class MemoryManager:
    """
    Thread-safe (GIL-protected) in-memory store for per-session chat history.

    Usage::

        memory = MemoryManager()
        memory.add_user_message("sess_1", "Hello!")
        memory.add_ai_message("sess_1", "Hi there!")
        history = memory.get_history("sess_1")
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionHistory] = {}

    # ── Private helpers ──────────────────────────────────────

    def _ensure_session(self, session_id: str) -> SessionHistory:
        """Get or create a session history entry."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionHistory()
            logger.debug(f"New session created: {session_id}")
        return self._sessions[session_id]

    # ── Public API ───────────────────────────────────────────

    def add_user_message(self, session_id: str, content: str) -> None:
        """
        Append a user (human) message to the session history.

        Args:
            session_id: Unique session identifier.
            content:    The user's message text.
        """
        session = self._ensure_session(session_id)
        session.messages.append(HumanMessage(content=content))

    def add_ai_message(self, session_id: str, content: str) -> None:
        """
        Append an AI (assistant) message to the session history.

        Args:
            session_id: Unique session identifier.
            content:    The assistant's response text.
        """
        session = self._ensure_session(session_id)
        session.messages.append(AIMessage(content=content))

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """
        Return the full ordered list of LangChain messages for a session.

        Args:
            session_id: Unique session identifier.

        Returns:
            List of BaseMessage objects (empty list if session doesn't exist).
        """
        session = self._sessions.get(session_id)
        return list(session.messages) if session else []

    def get_history(self, session_id: str) -> List[dict]:
        """
        Return the conversation history as plain dicts for API responses.

        Args:
            session_id: Unique session identifier.

        Returns:
            List of ``{"role": "user"|"assistant", "content": "..."}`` dicts.
        """
        messages = self.get_messages(session_id)
        history: List[dict] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history

    def clear_session(self, session_id: str) -> bool:
        """
        Delete all history for a given session.

        Args:
            session_id: Unique session identifier.

        Returns:
            True if the session existed and was deleted, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session cleared: {session_id}")
            return True
        return False

    @property
    def active_session_count(self) -> int:
        """Return the number of sessions currently stored in memory."""
        return len(self._sessions)


# ── Singleton instance ──────────────────────────────────────
memory_manager = MemoryManager()
