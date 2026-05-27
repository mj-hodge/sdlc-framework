"""
Auth helpers — extract user_id from MCP request context.

Uses module-level _last_user_id (NOT contextvars — they don't propagate
to MCP SDK tool handler tasks).

Called per-request in every tool handler:
    from src.auth.helpers import get_user_id_from_context
    user_id = get_user_id_from_context()
"""

from __future__ import annotations

_last_user_id: int | None = None


def set_current_user_id(user_id: int | None) -> None:
    """Called by ASGI identity middleware on each request."""
    global _last_user_id
    if user_id is not None:
        _last_user_id = user_id


def get_user_id_from_context() -> int:
    """Get the authenticated user_id. Raises RuntimeError if unauthenticated."""
    if _last_user_id is not None:
        return _last_user_id
    raise RuntimeError(
        "No authenticated user. Ensure the request includes a valid Bearer token."
    )
