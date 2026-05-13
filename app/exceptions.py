"""
Custom Exceptions
=================
Application-specific exception classes for clean error propagation.
Each exception carries a human-readable message and a machine-readable error code.
"""

from __future__ import annotations


class ChatbotBaseError(Exception):
    """Base exception for all chatbot errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class LLMUnavailableError(ChatbotBaseError):
    """
    Raised when neither the primary (Ollama) nor fallback (Groq) LLM
    is reachable or returns a valid response.
    """

    def __init__(self, message: str = "All LLM providers are unavailable") -> None:
        super().__init__(message=message, code="LLM_UNAVAILABLE")


class RateLimitExceededError(ChatbotBaseError):
    """
    Raised when a session exceeds the configured request-per-minute limit.
    """

    def __init__(self, session_id: str, limit: int) -> None:
        message = (
            f"Rate limit exceeded for session '{session_id}'. "
            f"Maximum {limit} requests per minute allowed."
        )
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")


class ToolExecutionError(ChatbotBaseError):
    """
    Raised when a tool encounters an unrecoverable error during execution.
    Individual tools should catch their own exceptions and return friendly
    error strings; this exception is for truly unexpected failures.
    """

    def __init__(self, tool_name: str, detail: str) -> None:
        message = f"Tool '{tool_name}' failed: {detail}"
        super().__init__(message=message, code="TOOL_FAILURE")
