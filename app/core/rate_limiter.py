"""
Rate Limiter
============
Simple sliding-window rate limiter backed by an in-memory dictionary.
Each session is tracked independently.

Algorithm:
  - Maintain a list of request timestamps per session.
  - On each request, prune timestamps older than 60 seconds.
  - If the remaining count ≥ configured limit → deny with 429.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List

from loguru import logger

from app.config import settings
from app.exceptions import RateLimitExceededError


class RateLimiter:
    """
    In-memory, per-session sliding-window rate limiter.

    Attributes:
        max_requests: Maximum allowed requests per session in the window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int = 60,
    ) -> None:
        self.max_requests = max_requests or settings.rate_limit_per_minute
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _prune(self, session_id: str) -> None:
        """Remove timestamps outside the current sliding window."""
        cutoff = time.time() - self.window_seconds
        self._requests[session_id] = [
            ts for ts in self._requests[session_id] if ts > cutoff
        ]

    def check(self, session_id: str) -> None:
        """
        Record a request and enforce the rate limit.

        Args:
            session_id: The session to track.

        Raises:
            RateLimitExceededError: If the session has exceeded its quota.
        """
        self._prune(session_id)

        if len(self._requests[session_id]) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for session {session_id} "
                f"({len(self._requests[session_id])}/{self.max_requests})"
            )
            raise RateLimitExceededError(session_id, self.max_requests)

        self._requests[session_id].append(time.time())

    def remaining(self, session_id: str) -> int:
        """Return how many requests the session has left in the current window."""
        self._prune(session_id)
        return max(0, self.max_requests - len(self._requests[session_id]))


# ── Singleton instance ──────────────────────────────────────
rate_limiter = RateLimiter()
