"""Custom exceptions for Lumberjack."""

from __future__ import annotations

from typing import Any


class LumberjackError(Exception):
    """Base exception for all Lumberjack errors."""


class TreeherderAPIError(LumberjackError):
    """Error returned by the Treeherder API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class TreeherderNotFoundError(TreeherderAPIError):
    """Resource not found (404)."""


class TreeherderAuthError(TreeherderAPIError):
    """Authentication or authorization error (401/403)."""


class TreeherderRateLimitError(TreeherderAPIError):
    """Rate limit exceeded (429)."""
