"""Rate limiting via slowapi.

Requests are keyed by API key (falling back to client IP), so limits are
per-client rather than global. The limit value is read from settings at request
time through the ``rate_limit`` callable.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import get_settings


def _key_func(request: Request) -> str:
    return request.headers.get("X-API-Key") or get_remote_address(request) or "anonymous"


limiter = Limiter(key_func=_key_func)


def rate_limit() -> str:
    """Return the configured rate limit (slowapi syntax, e.g. '30/minute')."""
    return get_settings().rate_limit
