from __future__ import annotations

import secrets
import time
from threading import Lock
from typing import Annotated, Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings

# ── Session token store ───────────────────────────────────────────────────────
# In-memory dict: token -> expiry (unix timestamp).
# Tokens are short-lived (2 h) and issued only to authenticated server callers.

_SESSION_TTL = 7200  # 2 hours
_tokens: dict[str, float] = {}
_lock = Lock()


def create_session_token() -> tuple[str, int]:
    """Generate and store a new session token. Returns (token, expires_in_seconds)."""
    token = secrets.token_hex(32)
    expiry = time.time() + _SESSION_TTL
    with _lock:
        # Purge expired tokens to avoid unbounded growth
        now = time.time()
        expired = [k for k, v in _tokens.items() if v < now]
        for k in expired:
            del _tokens[k]
        _tokens[token] = expiry
    return token, _SESSION_TTL


def _is_valid_session_token(token: str) -> bool:
    with _lock:
        expiry = _tokens.get(token)
        return expiry is not None and time.time() < expiry


# ── Auth dependencies ─────────────────────────────────────────────────────────


def verify_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> None:
    """Accept only the master API key (server-to-server calls)."""
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def verify_token(
    x_api_key: Annotated[Optional[str], Header()] = None,
    x_session_token: Annotated[Optional[str], Header()] = None,
) -> None:
    """Accept master API key OR a valid session token (browser direct calls)."""
    if x_api_key and x_api_key == settings.API_KEY:
        return
    if x_session_token and _is_valid_session_token(x_session_token):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )
